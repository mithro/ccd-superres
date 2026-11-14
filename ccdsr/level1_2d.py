"""Level 1 of the simulation chain, in two dimensions.

The surface is a picture of reflectance on a fine grid whose x axis is the
scan direction and whose y axis runs across it. The sensor is a small array
of pixels, turned by a tilt angle about the line of sight, that moves along x
between frames. The structure is the same as the one-dimensional version in
:mod:`ccdsr.level1`: blur once, read off at every pixel position, add noise,
reconstruct.

Lengths are in nanometres. The grid is periodic in both directions.

The reconstruction functions are given the readings, the sample positions and
the blur model. They never see the surface.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import LinearOperator, cg

from .level1 import Noise1D as Noise
from .level1 import Optics1D as Optics
from .level1 import motion_kernel_transfer
from .resolution import gap_transfer

__all__ = ["Optics", "Noise", "Scan2D", "Frames2D", "line_groups", "sinusoid2d", "transfer2d",
           "blur", "sample_positions", "sampling_matrix", "simulate", "shift_and_add",
           "least_squares", "group_contrast", "cross_scan_offsets"]


@dataclass(frozen=True)
class Scan2D:
    """How the sensor array is placed, moves and exposes."""

    n_rows: int = 16                       # pixels across the scan (before tilting)
    n_cols: int = 16                       # pixels along the scan (before tilting)
    n_frames: int = 200
    shift_px: float = 0.37                 # movement along x between frames, in pixels
    tilt_deg: float = 0.0                  # sensor rows turned from the scan direction
    exposure_fraction: float = 0.0         # share of a frame the light is on (0 = frozen)
    code: tuple[int, ...] | None = None
    row_delay_px: float = 0.0              # extra movement per sensor row (rolling readout)
    jitter_px: float = 0.0                 # random position error per frame, each axis (rms)
    start_nm: tuple[float, float] = (0.0, 0.0)


@dataclass
class Frames2D:
    """Raw readings plus what a real instrument would also know."""

    readings: np.ndarray                   # (n_frames, n_rows, n_cols), electrons
    positions_nm: np.ndarray               # (n_frames, n_rows, n_cols, 2): x, y of pixel centres
    dx_nm: float
    shape: tuple[int, int]                 # grid (ny, nx)
    optics: Optics
    scan: Scan2D
    noise: Noise
    truth: dict = field(default_factory=dict, repr=False)   # for scoring only


# ------------------------------------------------------------------ scenes

def line_groups(periods_nm, dx_nm, shape, cycles=4, low=0.2, high=1.0):
    """A test picture with groups of lines running both ways.

    The top half holds groups of lines that vary along x (the scan direction),
    the bottom half the same groups varying along y (across the scan). Returns
    the picture and, for each group, ``(period, direction, y0, y1, x0, x1)``
    in grid indices, where ``direction`` is ``"along"`` or ``"across"``.
    """
    ny, nx = shape
    picture = np.full(shape, low)
    groups = []
    slot = nx // len(periods_nm)
    for half, direction in enumerate(("along", "across")):
        yc = ny // 4 + half * ny // 2
        for k, period in enumerate(periods_nm):
            size = int(round(cycles * period / dx_nm))
            xc = k * slot + slot // 2
            y0, x0 = yc - size // 2, xc - size // 2
            y1, x1 = y0 + size, x0 + size
            if x0 < k * slot or x1 > (k + 1) * slot or size > ny // 2:
                raise ValueError(f"group of period {period} nm does not fit")
            t = (np.arange(size) + 0.5) * dx_nm
            bars = np.where((t % period) < period / 2, high, low)
            picture[y0:y1, x0:x1] = bars[None, :] if direction == "along" else bars[:, None]
            groups.append((float(period), direction, y0, y1, x0, x1))
    return picture, groups


def sinusoid2d(period_nm, angle_deg, dx_nm, shape, contrast=1.0, mean=0.5):
    """A sinusoid whose wave direction is ``angle_deg`` from the x axis.

    The period is nudged so that a whole number of waves fits the grid each
    way. Returns the picture and the frequency actually used, ``(fx, fy)`` in
    cycles per nanometre.
    """
    ny, nx = shape
    a = np.deg2rad(angle_deg)
    fx = round(np.cos(a) / period_nm * nx * dx_nm) / (nx * dx_nm)
    fy = round(np.sin(a) / period_nm * ny * dx_nm) / (ny * dx_nm)
    y, x = np.meshgrid(np.arange(ny) * dx_nm, np.arange(nx) * dx_nm, indexing="ij")
    return mean * (1 + contrast * np.cos(2 * np.pi * (fx * x + fy * y))), (fx, fy)


# -------------------------------------------------------------------- blur

def transfer2d(fx, fy, optics: Optics, scan: Scan2D):
    """Combined transfer of gap, pixel and motion at frequencies ``(fx, fy)`` (1/nm).

    The gap acts the same in every direction. The pixel is a square whose
    sides follow the tilted sensor. The motion smear lies along x.
    """
    fx = np.asarray(fx, dtype=float)
    fy = np.asarray(fy, dtype=float)
    f = np.hypot(fx, fy)
    aperture = optics.pitch_nm if optics.aperture_nm is None else optics.aperture_nm
    period = np.where(f > 0, 1 / np.maximum(f, 1e-300), 1.0)
    h_gap = np.where(f > 0, gap_transfer(period, optics.gap_nm, optics.gap_model,
                                         optics.wavelength_nm), 1.0)
    t = np.deg2rad(scan.tilt_deg)
    fu = fx * np.cos(t) + fy * np.sin(t)
    fv = -fx * np.sin(t) + fy * np.cos(t)
    h_pix = (np.sinc(fu * aperture) * np.sinc(fv * aperture)
             * np.exp(-2 * np.pi**2 * (optics.edge_sigma_nm * f) ** 2))
    smear = scan.shift_px * optics.pitch_nm * scan.exposure_fraction
    return h_gap * h_pix * motion_kernel_transfer(fx, smear, scan.code)


def _grid_transfer(shape, dx_nm, optics, scan):
    ny, nx = shape
    fy, fx = np.meshgrid(np.fft.fftfreq(ny, d=dx_nm), np.fft.fftfreq(nx, d=dx_nm), indexing="ij")
    return transfer2d(fx.ravel(), fy.ravel(), optics, scan).reshape(shape)


def blur(surface, dx_nm, optics: Optics, scan: Scan2D):
    """The surface as the pixels see it, before sampling."""
    h = _grid_transfer(surface.shape, dx_nm, optics, scan)
    return np.fft.ifft2(np.fft.fft2(surface) * h).real


# ---------------------------------------------------------------- sampling

def sample_positions(scan: Scan2D, pitch_nm, rng=None):
    """Centre of every pixel in every frame: array ``(frames, rows, cols, 2)`` of x, y."""
    t = np.deg2rad(scan.tilt_deg)
    row, col = np.meshgrid(np.arange(scan.n_rows), np.arange(scan.n_cols), indexing="ij")
    x = (col * np.cos(t) - row * np.sin(t)) * pitch_nm + row * scan.row_delay_px * pitch_nm
    y = (col * np.sin(t) + row * np.cos(t)) * pitch_nm
    step = np.arange(scan.n_frames) * scan.shift_px * pitch_nm
    fx = scan.start_nm[0] + step
    fy = np.full(scan.n_frames, scan.start_nm[1])
    if scan.jitter_px > 0:
        rng = np.random.default_rng() if rng is None else rng
        fx = fx + rng.normal(0, scan.jitter_px * pitch_nm, scan.n_frames)
        fy = fy + rng.normal(0, scan.jitter_px * pitch_nm, scan.n_frames)
    return np.stack([fx[:, None, None] + x[None], fy[:, None, None] + y[None]], axis=-1)


def sampling_matrix(positions_nm, shape, dx_nm):
    """Sparse matrix that reads a periodic grid at the given x, y positions.

    Bilinear interpolation: each row has four entries. The picture is
    flattened row by row (y first).
    """
    ny, nx = shape
    p = np.asarray(positions_nm, dtype=float).reshape(-1, 2) / dx_nm
    ix, iy = np.floor(p[:, 0]).astype(np.int64), np.floor(p[:, 1]).astype(np.int64)
    wx, wy = p[:, 0] - ix, p[:, 1] - iy
    rows = np.repeat(np.arange(p.shape[0]), 4)
    cols = np.stack([(iy % ny) * nx + ix % nx, (iy % ny) * nx + (ix + 1) % nx,
                     ((iy + 1) % ny) * nx + ix % nx, ((iy + 1) % ny) * nx + (ix + 1) % nx],
                    axis=1).ravel()
    vals = np.stack([(1 - wx) * (1 - wy), wx * (1 - wy), (1 - wx) * wy, wx * wy], axis=1).ravel()
    return csr_matrix((vals, (rows, cols)), shape=(p.shape[0], ny * nx))


def cross_scan_offsets(scan: Scan2D, pitch_nm):
    """Where the pixels sit across the scan, as fractions of a pixel pitch.

    Sorted distinct values of ``y / pitch`` modulo 1. With no tilt there is a
    single value: every pixel samples the same lines across the scan. Tilt
    spreads them out.
    """
    y = sample_positions(Scan2D(scan.n_rows, scan.n_cols, 1, tilt_deg=scan.tilt_deg), pitch_nm)[0, ..., 1]
    frac = np.round((y / pitch_nm) % 1.0, 6) % 1.0
    return np.unique(frac)


# ----------------------------------------------------------------- forward

def _scale(optics: Optics, noise: Noise):
    aperture = optics.pitch_nm if optics.aperture_nm is None else optics.aperture_nm
    return noise.full_e * (aperture / optics.pitch_nm) ** 2


def simulate(surface, dx_nm, optics: Optics, scan: Scan2D, noise: Noise | None = None, seed=0):
    """Raw frames for a surface: blur, sample at the moving pixels, add noise."""
    noise = Noise() if noise is None else noise
    rng = np.random.default_rng(seed)
    surface = np.asarray(surface, dtype=float)
    positions = sample_positions(scan, optics.pitch_nm, rng)
    s = sampling_matrix(positions, surface.shape, dx_nm)
    light = _scale(optics, noise)
    clean = light * (s @ blur(surface, dx_nm, optics, scan).ravel())
    gains = 1 + noise.gain_sigma * rng.standard_normal((scan.n_rows, scan.n_cols))
    clean = clean.reshape(scan.n_frames, scan.n_rows, scan.n_cols) * gains[None]
    noisy = rng.poisson(np.maximum(clean, 0)).astype(float) if noise.photon else clean.copy()
    if noise.read_e > 0:
        noisy += rng.normal(0, noise.read_e, noisy.shape)
    return Frames2D(noisy, positions, dx_nm, surface.shape, optics, scan, noise,
                    truth={"surface": surface, "gains": gains, "clean": clean, "light": light})


# ---------------------------------------------------------- reconstruction

def shift_and_add(frames: Frames2D):
    """Put every reading on the grid at its position and average.

    Returns the estimate and the coverage (weight of readings per grid cell).
    Cells that no reading reached are set to the mean of the others.
    """
    s = sampling_matrix(frames.positions_nm, frames.shape, frames.dx_nm)
    m = frames.readings.ravel() / _scale(frames.optics, frames.noise)
    weight = np.asarray(s.T @ np.ones(m.size)).ravel()
    total = np.asarray(s.T @ m).ravel()
    seen = weight > 1e-9
    est = np.full(weight.size, total[seen].sum() / weight[seen].sum())
    est[seen] = total[seen] / weight[seen]
    return est.reshape(frames.shape), weight.reshape(frames.shape)


def least_squares(frames: Frames2D, smoothness=1e-2, iterations=300, tol=1e-6, positions_nm=None):
    """Regularised least squares, solved by conjugate gradients.

    Finds the picture whose predicted readings best match the recorded ones,
    with a mild preference for smoothness. ``positions_nm`` replaces the
    recorded positions, for testing the effect of position errors. Returns the
    estimate and the number of iterations used.
    """
    ny, nx = frames.shape
    n = ny * nx
    pos = frames.positions_nm if positions_nm is None else positions_nm
    s = sampling_matrix(pos, frames.shape, frames.dx_nm)
    h = _grid_transfer(frames.shape, frames.dx_nm, frames.optics, frames.scan)
    m = frames.readings.ravel() / _scale(frames.optics, frames.noise)
    sts = (s.T @ s).tocsr()
    mean_w = sts.diagonal().mean()
    lam = smoothness * mean_w
    ly, lx = np.meshgrid(np.fft.fftfreq(ny), np.fft.fftfreq(nx), indexing="ij")
    lap = (2 * np.sin(np.pi * ly)) ** 2 + (2 * np.sin(np.pi * lx)) ** 2

    def filt(v, g):
        return np.fft.ifft2(np.fft.fft2(v.reshape(ny, nx)) * g).real.ravel()

    def normal(v):
        return filt(sts @ filt(v, h), np.conj(h)) + lam * filt(v, lap)

    rhs = filt(np.asarray(s.T @ m).ravel(), np.conj(h))
    precond_diag = mean_w * np.abs(h) ** 2 + lam * lap + 1e-9 * mean_w
    op = LinearOperator((n, n), matvec=normal, dtype=float)
    pre = LinearOperator((n, n), matvec=lambda v: filt(v, 1 / precond_diag), dtype=float)
    count = [0]
    x, _ = cg(op, rhs, rtol=tol, maxiter=iterations, M=pre,
              callback=lambda _: count.__setitem__(0, count[0] + 1))
    return x.reshape(ny, nx), count[0]


# ------------------------------------------------------------------ metrics

def group_contrast(estimate, group, dx_nm):
    """Contrast of the basic repeat of one line group in an estimate.

    Averages the group along its lines, then returns the amplitude at the
    group's period divided by the mean.
    """
    period, direction, y0, y1, x0, x1 = group
    patch = np.asarray(estimate)[y0:y1, x0:x1]
    profile = patch.mean(axis=0 if direction == "along" else 1)
    t = (np.arange(profile.size) + 0.5) * dx_nm
    wave = np.exp(-2j * np.pi * t / period)
    return float(2 * np.abs(np.mean(profile * wave)) / np.mean(profile))
