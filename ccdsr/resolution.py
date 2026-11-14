"""Analytic resolution model.

Fast estimates of how strongly each stage attenuates fine detail and of the
smallest feature period that survives. No simulation is run, so these are
instant, and they are deliberately simple: a feature of period ``L`` counts as
recoverable when its signal, after attenuation by the gap, the pixel area and
motion blur, still exceeds the noise left after averaging the samples that
fall in a cell of ``(L / 2)`` squared.

Lengths are in nanometres unless a name says otherwise.

The trade-off explorer in ``explorer/model.js`` implements the same formulas
in JavaScript; ``tests/test_explorer_parity.py`` checks the two agree.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.special import k1

from .sampling import Budget, Scan, Sensor, scan_budget


def gap_transfer(period_nm, gap_nm, model="diffuse", wavelength_nm=550.0):
    """Contrast passed across the gap.

    ``model="diffuse"``: the surface scatters light in all directions with no
    fixed phase (a matt surface). The transfer is ``u K1(u)`` with
    ``u = 2 pi gap / period`` and does not depend on wavelength.

    ``model="collimated"``: a smooth, mirror-like surface under a collimated
    beam, such as a polished silicon chip. Detail with a period longer than
    the wavelength travels across the gap as ordinary diffracted beams and is
    not attenuated (recovering it then needs a wave reconstruction). Detail
    finer than the wavelength exists only as an evanescent wave that decays as
    ``exp(-2 pi gap sqrt(1/period^2 - 1/wavelength^2))``.
    """
    period = np.asarray(period_nm, dtype=float)
    gap = np.asarray(gap_nm, dtype=float)
    if model == "diffuse":
        u = 2 * np.pi * gap / period
        with np.errstate(invalid="ignore", over="ignore"):
            return np.where(u < 1e-8, 1.0, u * k1(np.maximum(u, 1e-300)))
    if model == "collimated":
        k2 = 1 / period**2 - 1 / float(wavelength_nm) ** 2
        return np.where(k2 <= 0, 1.0, np.exp(-2 * np.pi * gap * np.sqrt(np.maximum(k2, 0))))
    raise ValueError(f"unknown gap model {model!r}")


def box_envelope(period_nm, width_nm):
    """Upper envelope of ``|sinc(width / period)|`` for a box of the given width."""
    x = np.asarray(width_nm, dtype=float) / np.asarray(period_nm, dtype=float)
    return np.minimum(np.abs(np.sinc(np.minimum(x, 0.5))), 1 / (np.pi * np.maximum(x, 1e-9)))


def soft_edge(period_nm, sigma_nm):
    """Extra attenuation from pixel edges softened over ``sigma_nm``."""
    return np.exp(-2 * np.pi**2 * (np.asarray(sigma_nm, dtype=float) / period_nm) ** 2)


def combined_transfer(period_nm, gap_nm, pitch_nm, blur_px=0.0, edge_sigma_nm=0.0,
                      aperture_nm=None, gap_model="diffuse", wavelength_nm=550.0):
    """Product of gap, pixel and motion transfer along the scan direction.

    ``aperture_nm`` is the width of the light-sensitive opening of a pixel. It
    defaults to the pitch (a bare pixel); a mask makes it smaller.
    """
    return (
        gap_transfer(period_nm, gap_nm, gap_model, wavelength_nm)
        * box_envelope(period_nm, pitch_nm if aperture_nm is None else aperture_nm)
        * soft_edge(period_nm, edge_sigma_nm)
        * box_envelope(period_nm, blur_px * pitch_nm)
    )


def recoverable_period(
    n_per_pixel_area,
    gap_nm,
    pitch_nm=1120.0,
    snr_single=50.0,
    contrast=1.0,
    blur_px=0.0,
    edge_sigma_nm=0.0,
    aperture_nm=None,
    gap_model="diffuse",
    wavelength_nm=550.0,
):
    """Smallest period whose signal still exceeds the noise after averaging.

    ``n_per_pixel_area`` is the number of samples collected per pixel-sized
    area of surface. A feature of period ``L`` is judged over a cell of
    ``(L / 2)`` squared, which holds ``n * (L / 2p)`` squared samples.

    A masked pixel (``aperture_nm`` smaller than the pitch) collects less
    light. ``snr_single`` is the signal-to-noise of an unmasked pixel and is
    scaled by ``aperture / pitch``, as for photon-limited noise.
    """
    aperture = pitch_nm if aperture_nm is None else aperture_nm
    snr = snr_single * aperture / pitch_nm
    from scipy.optimize import brentq

    def margin(log_period):
        period = math.exp(log_period)
        n_cell = n_per_pixel_area * (period / (2 * pitch_nm)) ** 2
        signal = float(combined_transfer(period, gap_nm, pitch_nm, blur_px, edge_sigma_nm,
                                         aperture, gap_model, wavelength_nm))
        return math.log(signal * contrast * snr * math.sqrt(n_cell) + 1e-300)

    lo, hi = math.log(1e-2), math.log(1e12)
    if margin(hi) < 0:
        return math.inf
    return math.exp(brentq(margin, lo, hi))


@dataclass(frozen=True)
class Resolution:
    """Result of :func:`explore`."""

    budget: Budget
    samples_per_pixel_area: float
    noise_limited_nm: float     # limit from attenuation against noise
    sampling_limited_nm: float  # limit from how densely positions are covered
    recoverable_nm: float       # the larger of the two
    limited_by: str             # "gap", "pixel area", "motion blur" or "sampling pattern"
    transfer_gap: float         # transfers evaluated at the recoverable period
    transfer_pixel: float
    transfer_motion: float


def explore(
    sensor: Sensor,
    scan: Scan,
    gap_nm: float,
    snr_single: float = 50.0,
    contrast: float = 1.0,
    edge_sigma_nm: float = 0.0,
    passes: float = 1.0,
    seed: int | None = 0,
    aperture_nm: float | None = None,
    gap_model: str = "diffuse",
    wavelength_nm: float = 550.0,
) -> Resolution:
    """Sampling figures plus the analytic resolution estimate for one setting."""
    b = scan_budget(sensor, scan, seed)
    pitch_nm = sensor.pitch_um * 1e3
    n = b.samples_per_point * passes
    aperture = pitch_nm if aperture_nm is None else aperture_nm
    noise = recoverable_period(n, gap_nm, pitch_nm, snr_single, contrast, b.blur_px,
                               edge_sigma_nm, aperture, gap_model, wavelength_nm)
    # A square grid with spacing s has largest hole s / sqrt(2); Nyquist period is 2 s.
    sampling = 2 * math.sqrt(2) * b.coverage.largest_hole_px * pitch_nm
    period = max(noise, sampling)
    if math.isinf(period):
        t_gap = t_pix = t_mot = 0.0
    else:
        t_gap = float(gap_transfer(period, gap_nm, gap_model, wavelength_nm))
        t_pix = float(box_envelope(period, aperture) * soft_edge(period, edge_sigma_nm))
        t_mot = float(box_envelope(period, b.blur_px * pitch_nm))
    if sampling > noise:
        limited = "sampling pattern"
    else:
        limited = min(
            [("gap", t_gap), ("pixel area", t_pix), ("motion blur", t_mot)],
            key=lambda kv: kv[1],
        )[0]
    return Resolution(b, n, noise, sampling, period, limited, t_gap, t_pix, t_mot)
