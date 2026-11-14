"""Level 1 of the simulation chain, in one dimension.

The surface is a line of reflectance values on a fine grid. It is blurred once
by the combined kernel (gap, pixel, motion), then read off at every position a
moving pixel sampled it, with pixel gains and noise. The reconstruction turns
those readings back into an estimate of the surface.

Everything here is along the scan direction only. The two-dimensional version
adds the direction across the scan and the tilt; the structure is the same.

Lengths are in nanometres. The fine grid is periodic, so a scene should be
padded if its ends matter.

The reconstruction functions are given only what an instrument would have:
the readings, sample positions (the true ones unless others are passed in;
:func:`estimate_positions` works them out from the readings), and the model
of the blur. They never see the surface.

Conventions. A frame taken later sits at a larger position. The motion smear
is centred on the frame's position, and slot ``k`` of an exposure code lies
at ``(k + 0.5) / n - 0.5`` of the smear length from that centre, so earlier
slots are at smaller positions. Shortening or coding the exposure does not
reduce the light here: ``full_e`` is the signal actually collected, and the
cost in light has to be put in by the caller.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import warnings

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import LinearOperator, cg

from .resolution import gap_transfer


# ----------------------------------------------------------------- settings

@dataclass(frozen=True)
class Optics1D:
    """What blurs the surface before it is sampled."""

    gap_nm: float = 300.0
    pitch_nm: float = 1120.0
    aperture_nm: float | None = None       # light-sensitive width; None = the pitch
    edge_sigma_nm: float = 0.0             # softness of the pixel edges (Gaussian sigma)
    gap_model: str = "diffuse"
    wavelength_nm: float = 550.0


@dataclass(frozen=True)
class Scan1D:
    """How the sensor moves and exposes."""

    n_pixels: int = 64                     # pixels along the scan
    n_frames: int = 200
    shift_px: float = 0.37                 # movement between frames, in pixels
    exposure_fraction: float = 0.0         # share of a frame the light is on (0 = frozen)
    code: tuple[int, ...] | None = None    # on-off pattern within the exposure, or None
    jitter_px: float = 0.0                 # random position error per frame (rms)
    start_nm: float = 0.0


@dataclass(frozen=True)
class Noise1D:
    """Pixel noise. Signal is in electrons: a reflectance of 1 gives ``full_e``."""

    full_e: float = 2500.0                 # electrons at reflectance 1 (snr 50 when photon limited)
    read_e: float = 2.0                    # read noise, electrons rms
    gain_sigma: float = 0.0                # spread of pixel gains (fraction)
    photon: bool = True


@dataclass
class Frames1D:
    """Raw readings plus what a real instrument would also know."""

    readings: np.ndarray                   # (n_frames, n_pixels), electrons
    positions_nm: np.ndarray               # (n_frames, n_pixels), pixel centres on the surface
    dx_nm: float
    n_grid: int
    optics: Optics1D
    scan: Scan1D
    noise: Noise1D
    truth: dict = field(default_factory=dict, repr=False)   # for scoring only


# ------------------------------------------------------------------ scenes

def bar_groups(periods_nm, dx_nm, cycles=6, margin_nm=3000.0, low=0.2, high=1.0):
    """Groups of bars of the given periods, separated by flat margins.

    Returns the reflectance line and, for each group, ``(period, start, stop)``
    in grid indices.
    """
    m = int(round(margin_nm / dx_nm))
    parts, groups, at = [np.full(m, low)], [], m
    for period in periods_nm:
        n = int(round(cycles * period / dx_nm))
        x = (np.arange(n) + 0.5) * dx_nm
        bars = np.where((x % period) < period / 2, high, low)
        parts += [bars, np.full(m, low)]
        groups.append((float(period), at, at + n))
        at += n + m
    return np.concatenate(parts), groups


def sinusoid(period_nm, dx_nm, n_grid, contrast=1.0, mean=0.5, phase=0.0):
    """A sinusoidal reflectance with a whole number of periods on the grid."""
    x = np.arange(n_grid) * dx_nm
    return mean * (1 + contrast * np.cos(2 * np.pi * x / period_nm + phase))


# ------------------------------------------------------------------- blur

def motion_kernel_transfer(freq, smear_nm, code=None):
    """Exact transfer of the motion smear at spatial frequencies ``freq`` (1/nm).

    A plain exposure is a box of length ``smear_nm``. A coded exposure is that
    box cut into ``len(code)`` slots with the light on where the code is 1.
    The smear is centred, so a plain box has a real transfer.
    """
    if smear_nm <= 0:
        return np.ones_like(freq, dtype=complex)
    if code is None:
        return np.sinc(freq * smear_nm).astype(complex)
    code = np.asarray(code, dtype=float)
    n = code.size
    slot = smear_nm / n
    centres = (np.arange(n) + 0.5) * slot - smear_nm / 2
    phases = np.exp(-2j * np.pi * np.outer(freq, centres))
    return np.sinc(freq * slot) * (phases @ code) / code.sum()


def transfer(freq, optics: Optics1D, smear_nm=0.0, code=None):
    """Combined transfer of gap, pixel and motion at frequencies ``freq`` (1/nm)."""
    f = np.abs(np.asarray(freq, dtype=float))
    aperture = optics.pitch_nm if optics.aperture_nm is None else optics.aperture_nm
    with np.errstate(divide="ignore"):
        period = np.where(f > 0, 1 / np.maximum(f, 1e-300), np.inf)
    h_gap = np.where(f > 0, gap_transfer(np.where(f > 0, period, 1.0), optics.gap_nm,
                                         optics.gap_model, optics.wavelength_nm), 1.0)
    h_pix = np.sinc(f * aperture) * np.exp(-2 * np.pi**2 * (optics.edge_sigma_nm * f) ** 2)
    return h_gap * h_pix * motion_kernel_transfer(np.asarray(freq, dtype=float), smear_nm, code)


def _grid_transfer(n_grid, dx_nm, optics, scan):
    freq = np.fft.fftfreq(n_grid, d=dx_nm)
    smear = scan.shift_px * optics.pitch_nm * scan.exposure_fraction
    return transfer(freq, optics, smear, scan.code)


def blur(surface, dx_nm, optics: Optics1D, scan: Scan1D):
    """The surface as the pixels see it, before sampling."""
    h = _grid_transfer(surface.size, dx_nm, optics, scan)
    return np.fft.ifft(np.fft.fft(surface) * h).real


# ---------------------------------------------------------------- sampling

def sample_positions(scan: Scan1D, pitch_nm, rng=None):
    """Centre of every pixel in every frame, on the surface."""
    frame = scan.start_nm + np.arange(scan.n_frames) * scan.shift_px * pitch_nm
    if scan.jitter_px > 0:
        rng = np.random.default_rng() if rng is None else rng
        frame = frame + rng.normal(0, scan.jitter_px * pitch_nm, scan.n_frames)
    return frame[:, None] + np.arange(scan.n_pixels)[None, :] * pitch_nm


def sampling_matrix(positions_nm, n_grid, dx_nm):
    """Sparse matrix that reads a periodic fine grid at the given positions.

    Linear interpolation: each row has two entries.
    """
    x = np.asarray(positions_nm, dtype=float).ravel() / dx_nm
    i0 = np.floor(x).astype(np.int64)
    w1 = x - i0
    rows = np.repeat(np.arange(x.size), 2)
    cols = np.stack([i0 % n_grid, (i0 + 1) % n_grid], axis=1).ravel()
    vals = np.stack([1 - w1, w1], axis=1).ravel()
    return csr_matrix((vals, (rows, cols)), shape=(x.size, n_grid))


# ----------------------------------------------------------------- forward

def simulate(surface, dx_nm, optics: Optics1D, scan: Scan1D, noise: Noise1D | None = None, seed=0):
    """Raw frames for a surface: blur, sample at the moving pixels, add noise."""
    noise = Noise1D() if noise is None else noise
    rng = np.random.default_rng(seed)
    surface = np.asarray(surface, dtype=float)
    positions = sample_positions(scan, optics.pitch_nm, rng)
    s = sampling_matrix(positions, surface.size, dx_nm)
    aperture = optics.pitch_nm if optics.aperture_nm is None else optics.aperture_nm
    light = noise.full_e * aperture / optics.pitch_nm
    clean = light * (s @ blur(surface, dx_nm, optics, scan))
    gains = 1 + noise.gain_sigma * rng.standard_normal(scan.n_pixels)
    clean = clean.reshape(scan.n_frames, scan.n_pixels) * gains[None, :]
    noisy = rng.poisson(np.maximum(clean, 0)).astype(float) if noise.photon else clean.copy()
    if noise.read_e > 0:
        noisy += rng.normal(0, noise.read_e, noisy.shape)
    return Frames1D(noisy, positions, dx_nm, surface.size, optics, scan, noise,
                    truth={"surface": surface, "gains": gains, "clean": clean, "light": light})


# ---------------------------------------------------------- reconstruction

def _scale(frames: Frames1D):
    aperture = (frames.optics.pitch_nm if frames.optics.aperture_nm is None
                else frames.optics.aperture_nm)
    return frames.noise.full_e * aperture / frames.optics.pitch_nm


def shift_and_add(frames: Frames1D):
    """Put every reading on the fine grid at its position and average.

    Returns the estimate and the coverage (weight of readings per grid cell).
    No deblurring: this shows what dense sampling alone achieves.
    """
    s = sampling_matrix(frames.positions_nm, frames.n_grid, frames.dx_nm)
    m = frames.readings.ravel() / _scale(frames)
    weight = np.asarray(s.T @ np.ones(m.size)).ravel()
    total = np.asarray(s.T @ m).ravel()
    est = np.where(weight > 0, total / np.maximum(weight, 1e-12), np.nan)
    if np.isnan(est).any():                       # fill unsampled cells from neighbours
        idx = np.arange(est.size)
        good = ~np.isnan(est)
        est = np.interp(idx, idx[good], est[good], period=est.size)
    return est, weight


def wiener(frames: Frames1D, noise_to_signal=1e-3):
    """Shift and add, then undo the blur where the signal is above the noise."""
    est, _ = shift_and_add(frames)
    h = _grid_transfer(frames.n_grid, frames.dx_nm, frames.optics, frames.scan)
    filt = np.conj(h) / (np.abs(h) ** 2 + noise_to_signal)
    return np.fft.ifft(np.fft.fft(est) * filt).real


def least_squares(frames: Frames1D, smoothness=1e-2, iterations=200, tol=1e-8, weights=None,
                  positions_nm=None):
    """Regularised least squares, solved by conjugate gradients.

    Finds the surface whose predicted readings best match the recorded ones,
    with a mild preference for smoothness. No matrix is formed for the blur:
    it is applied by Fourier transform, and sampling is a sparse matrix.

    ``smoothness`` is relative to the mean sampling weight over the whole grid
    (readings per grid cell), so it keeps its meaning when the number of
    frames changes. Adding unsampled margin to a scene lowers that mean and
    with it the effective smoothing; raise ``smoothness`` in proportion to
    compare like with like. A warning is raised if the solver
    stops before reaching ``tol``.

    ``positions_nm`` replaces the recorded positions. The recorded ones are the
    true positions; pass the nominal or estimated ones to see the effect of
    position errors.
    """
    n = frames.n_grid
    pos = frames.positions_nm if positions_nm is None else positions_nm
    s = sampling_matrix(pos, n, frames.dx_nm)
    h = _grid_transfer(n, frames.dx_nm, frames.optics, frames.scan)
    m = frames.readings.ravel() / _scale(frames)
    w = np.ones(m.size) if weights is None else np.asarray(weights, dtype=float).ravel()
    sws = (s.T @ s.multiply(w[:, None])).tocsr()
    diag = sws.diagonal()
    mean_w = diag.mean()
    lam = smoothness * mean_w
    freq = np.fft.fftfreq(n)
    lap = (2 * np.sin(np.pi * freq)) ** 2

    def k(v):
        return np.fft.ifft(np.fft.fft(v) * h).real

    def kt(v):
        return np.fft.ifft(np.fft.fft(v) * np.conj(h)).real

    def normal(v):
        return kt(sws @ k(v)) + lam * np.fft.ifft(np.fft.fft(v) * lap).real

    rhs = kt(np.asarray(s.T @ (w * m)).ravel())
    precond_diag = mean_w * np.abs(h) ** 2 + lam * lap + 1e-12 * mean_w

    def precond(v):
        return np.fft.ifft(np.fft.fft(v) / precond_diag).real

    op = LinearOperator((n, n), matvec=normal, dtype=float)
    pre = LinearOperator((n, n), matvec=precond, dtype=float)
    count = [0]
    x, info = cg(op, rhs, rtol=tol, maxiter=iterations, M=pre,
                 callback=lambda _: count.__setitem__(0, count[0] + 1))
    if info != 0:
        warnings.warn(f"least_squares stopped after {count[0]} iterations without reaching tol={tol}",
                      RuntimeWarning, stacklevel=2)
    return x, count[0]


# --------------------------------------------------------- motion estimation

def nominal_positions(frames: Frames1D, shift_px=None):
    """Positions the instrument would assume: constant speed, no jitter.

    ``shift_px`` is the believed movement per frame, if it differs from the
    true one.
    """
    scan = frames.scan
    shift = scan.shift_px if shift_px is None else shift_px
    frame = scan.start_nm + np.arange(scan.n_frames) * shift * frames.optics.pitch_nm
    return frame[:, None] + np.arange(scan.n_pixels)[None, :] * frames.optics.pitch_nm


def estimate_positions(frames: Frames1D, start_positions_nm=None, rounds=12, smoothness=(1.0, 1e-2),
                       max_step_px=0.5):
    """Estimate where each frame really was, from the readings alone.

    Alternates two steps. First, reconstruct the surface with the current
    positions. Second, slide each frame along that reconstruction to where its
    readings fit best (one Gauss-Newton step per frame, using the slope of the
    predicted readings). The reconstruction starts smooth and sharpens from
    round to round, so that large errors are caught on coarse detail before
    fine detail is trusted.

    The spacing of the pixels within a frame is known, so only one offset per
    frame is solved. A shift of all frames together cannot be seen in the data
    and is left as it started.

    Returns ``(positions, offsets_history)`` where the history has one row of
    per-frame offsets (nanometres, relative to the start) per round.
    """
    n, dx = frames.n_grid, frames.dx_nm
    start = nominal_positions(frames) if start_positions_nm is None else np.asarray(start_positions_nm)
    offsets = np.zeros(frames.scan.n_frames)
    h = _grid_transfer(n, dx, frames.optics, frames.scan)
    slope_filter = 2j * np.pi * np.fft.fftfreq(n, d=dx)
    m = frames.readings / _scale(frames)
    levels = np.geomspace(smoothness[0], smoothness[1], rounds)
    history = []
    for level in levels:
        pos = start + offsets[:, None]
        est, _ = least_squares(frames, smoothness=level, positions_nm=pos)
        spectrum = np.fft.fft(est) * h
        s = sampling_matrix(pos, n, dx)
        predicted = (s @ np.fft.ifft(spectrum).real).reshape(m.shape)
        slope = (s @ np.fft.ifft(spectrum * slope_filter).real).reshape(m.shape)
        step = np.sum(slope * (m - predicted), axis=1) / np.maximum(np.sum(slope**2, axis=1), 1e-30)
        limit = max_step_px * frames.optics.pitch_nm
        offsets = offsets + np.clip(step, -limit, limit)
        offsets -= offsets.mean()
        history.append(offsets.copy())
    return start + offsets[:, None], np.array(history)


def position_precision_limit(frames: Frames1D):
    """Reference limit for the rms error of a frame's position, in nanometres.

    The Cramér-Rao bound for sliding one frame along a surface that is known
    exactly: the noise of the readings divided by the summed slope of the
    blurred surface under the frame. An estimator that also has to work out
    the surface, as :func:`estimate_positions` does, is not bound by it in a
    strict sense, so treat it as a yardstick. Uses the true surface, so it is
    for scoring only. Returns the rms over frames.
    """
    n, dx = frames.n_grid, frames.dx_nm
    spectrum = np.fft.fft(frames.truth["surface"]) * _grid_transfer(n, dx, frames.optics, frames.scan)
    s = sampling_matrix(frames.positions_nm, n, dx)
    shape = frames.readings.shape
    level = (s @ np.fft.ifft(spectrum).real).reshape(shape)
    slope = (s @ np.fft.ifft(spectrum * 2j * np.pi * np.fft.fftfreq(n, d=dx)).real).reshape(shape)
    light = _scale(frames)
    variance = ((light * level if frames.noise.photon else 0.0) + frames.noise.read_e**2) / light**2
    return float(np.sqrt(np.mean(1 / np.sum(slope**2 / variance, axis=1))))


def align_positions(frames: Frames1D, positions_nm):
    """Positions shifted as a whole so that their mean error is zero. For scoring only.

    The data cannot tell a shift of every frame together from a shift of the
    surface, so an estimate is free to carry one. Removing it before
    reconstructing puts the picture where the true surface is, so that it can
    be scored against the truth in fixed windows.
    """
    positions = np.asarray(positions_nm, dtype=float)
    return positions - np.mean((positions - frames.positions_nm)[:, 0])


def position_error(frames: Frames1D, positions_nm):
    """Rms error of per-frame positions against the truth, in nanometres.

    The mean error is removed first: a shift of every frame together moves the
    whole picture and does not blur it.
    """
    err = (np.asarray(positions_nm) - frames.positions_nm)[:, 0]
    return float(np.std(err))


# ------------------------------------------------------------------ metrics

def bar_contrast(estimate, group, dx_nm):
    """Contrast of the fundamental of one bar group in an estimate.

    Returns the amplitude at the group's period divided by the mean, measured
    over a whole number of periods in the middle of the group.
    """
    period, start, stop = group
    per = period / dx_nm
    cycles = int((stop - start) / per) - 2
    if cycles < 1:
        raise ValueError("group too short to measure")
    a = start + int(round(per))
    seg = estimate[a:a + int(round(cycles * per))]
    x = np.arange(seg.size)
    amp = 2 * np.abs(np.mean(seg * np.exp(-2j * np.pi * x / per)))
    return float(amp / np.mean(seg))


def sinusoid_amplitude(frames: Frames1D, period_nm):
    """Best estimate of the contrast of a sinusoid of known period from raw readings.

    Fits mean, cosine and sine to the readings directly (no reconstruction),
    then divides out the model transfer. Used to check the noise prediction.
    Returns ``(contrast, phase)``.
    """
    x = frames.positions_nm.ravel()
    m = frames.readings.ravel() / _scale(frames)
    basis = np.stack([np.ones_like(x), np.cos(2 * np.pi * x / period_nm),
                      np.sin(2 * np.pi * x / period_nm)], axis=1)
    coef, *_ = np.linalg.lstsq(basis, m, rcond=None)
    smear = frames.scan.shift_px * frames.optics.pitch_nm * frames.scan.exposure_fraction
    t = np.abs(transfer(np.array([1 / period_nm]), frames.optics, smear, frames.scan.code))[0]
    amp = np.hypot(coef[1], coef[2]) / t
    return float(amp / coef[0]), float(np.arctan2(-coef[2], coef[1]))


def predicted_contrast_noise(period_nm, optics: Optics1D, scan: Scan1D, noise: Noise1D, mean=0.5,
                             contrast=0.0):
    """Analytic rms error of the contrast estimated by :func:`sinusoid_amplitude`.

    For ``M`` readings with noise ``sigma`` each (relative to full signal),
    fitting a sinusoid gives each of its two components an error of
    ``sigma * sqrt(2 / M)``. Dividing by the transfer ``T`` and the mean gives
    the error in contrast. This is the one-dimensional counterpart of the
    level 0 criterion ``T * contrast * snr * sqrt(samples) >= 1``.

    ``contrast`` is the true contrast of the pattern. Contrast is the fitted
    amplitude divided by the fitted mean, and the error of the mean matters
    once the blurred contrast ``b = T * contrast`` is not small: the variance
    is multiplied by ``1 + b**2 / 2 - b**2 * p``, where ``p`` is the share of
    the noise variance that comes from the light itself (photon noise makes
    the two errors move together). With the default of 0 the factor is 1.
    """
    aperture = optics.pitch_nm if optics.aperture_nm is None else optics.aperture_nm
    light = noise.full_e * aperture / optics.pitch_nm
    electrons = light * mean
    photon_var = electrons if noise.photon else 0.0
    sigma_e = np.sqrt(photon_var + noise.read_e**2)
    sigma = sigma_e / light
    m = scan.n_frames * scan.n_pixels
    smear = scan.shift_px * optics.pitch_nm * scan.exposure_fraction
    t = np.abs(transfer(np.array([1 / period_nm]), optics, smear, scan.code))[0]
    b = t * contrast
    factor = 1 + b**2 / 2 - b**2 * photon_var / sigma_e**2
    return float(sigma * np.sqrt(2 / m) / (t * mean) * np.sqrt(factor))
