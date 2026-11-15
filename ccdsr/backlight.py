"""Rough estimate for lighting the chip from behind with near-infrared light.

Silicon absorbs visible light within a few micrometres but lets light just
beyond red (near-infrared, around 1 micrometre) partly through. A plain
near-infrared lamp behind the chip therefore sends light up through the
chip's silicon, past its metal wiring, across the gap and into the sensor,
arriving straight on. The metal blocks it, so the sensor sees the shadow of
the wiring.

The catch is that the sensor is silicon too: light that silicon lets through
is light the sensor's thin light-sensitive layer mostly fails to catch. This
module multiplies the two effects to find how much light is detected at each
wavelength, and estimates how deep absorption in the pixel softens fine
detail.

Everything here is a straight-through, flat-layer estimate. It leaves out
absorption by free carriers in doped silicon, reflections back and forth
inside each layer, and the real layer stack of chip and sensor: see
``docs/backlight.md``.
"""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import numpy as np

from .resolution import box_envelope, combined_transfer

_DATA = Path(__file__).resolve().parent / "data" / "silicon_green2008.csv"

GLASS_INDEX = 1.45      #: silicon dioxide in the near-infrared, a round value


@lru_cache(maxsize=1)
def _table():
    rows = np.loadtxt(_DATA, delimiter=",", comments="#", skiprows=6)
    return rows[:, 0] * 1000.0, rows[:, 1], rows[:, 2]


def silicon_nk(wavelength_nm):
    """Refractive index ``n`` and extinction coefficient ``k`` of silicon.

    Interpolated from the table of Green (2008) in
    ``ccdsr/data/silicon_green2008.csv``, which covers 250 nm to 1450 nm.
    ``k`` is interpolated on a logarithmic scale because it falls by many
    powers of ten across the near-infrared.
    """
    w, n, k = _table()
    wavelength = np.asarray(wavelength_nm, dtype=float)
    if np.any(wavelength < w[0]) or np.any(wavelength > w[-1]):
        raise ValueError(f"wavelength outside the table ({w[0]:.0f} nm to {w[-1]:.0f} nm)")
    return np.interp(wavelength, w, n), np.exp(np.interp(wavelength, w, np.log(k)))


def absorption_per_um(wavelength_nm):
    """Share of light absorbed per micrometre of silicon, as a rate.

    Light falls as ``exp(-rate * depth)``; the rate is ``4 pi k / wavelength``.
    """
    _, k = silicon_nk(wavelength_nm)
    return 4 * np.pi * k / (np.asarray(wavelength_nm, dtype=float) / 1000.0)


def _reflect(n1, n2):
    """Share of light reflected going straight from index n1 to index n2."""
    return ((n1 - n2) / (n1 + n2)) ** 2


def chip_transmission(wavelength_nm, thickness_um):
    """Share of light that gets through the chip where no metal is in the way.

    Three losses: reflection where the light enters the bare back of the
    silicon, absorption on the way through ``thickness_um`` of silicon, and
    reflection where it leaves through the glass layers on the chip's face.
    """
    n, _ = silicon_nk(wavelength_nm)
    enter = 1 - _reflect(1.0, n)
    through = np.exp(-absorption_per_um(wavelength_nm) * thickness_um)
    leave = (1 - _reflect(n, GLASS_INDEX)) * (1 - _reflect(GLASS_INDEX, 1.0))
    return enter * through * leave


def pixel_absorption(wavelength_nm, depth_um=3.0):
    """Share of light falling on a bare pixel that its sensitive layer absorbs.

    ``depth_um`` is the thickness of the light-sensitive silicon. The default
    of 3 µm is an assumption for a small back-illuminated pixel.
    """
    n, _ = silicon_nk(wavelength_nm)
    return (1 - _reflect(1.0, n)) * (1 - np.exp(-absorption_per_um(wavelength_nm) * depth_um))


def backlight_reading(wavelength_nm, thickness_um, depth_um=3.0):
    """Light a pixel detects through an open part of the chip.

    Given as a share of what the pixel would detect if it absorbed all the
    lamp's light directly, the same yardstick as
    :func:`ccdsr.light_entry.slot_light`.
    """
    return chip_transmission(wavelength_nm, thickness_um) * pixel_absorption(wavelength_nm, depth_um)


def best_wavelength(thickness_um, depth_um=3.0):
    """Wavelength (nm) that gives the largest reading, and that reading."""
    grid = np.arange(700.0, 1200.5, 1.0)
    readings = backlight_reading(grid, thickness_um, depth_um)
    i = int(np.argmax(readings))
    return float(grid[i]), float(readings[i])


def depth_washout(period_nm, wavelength_nm, depth_um=3.0):
    """Contrast kept after the pattern travels through the pixel's depth.

    Near-infrared light is absorbed all the way down through the sensitive
    layer. A fine pattern of light changes as it travels down through the
    silicon (its bright lines drift and swap with its dark lines), so
    adding up the light absorbed at every depth smears it. For a pattern of
    period ``p`` the phase between the straight-on light and the light bent
    by the pattern grows with depth ``z`` as ``2 pi z (n / w - sqrt(n^2 /
    w^2 - 1 / p^2))`` for wavelength ``w`` and index ``n``. Averaging the
    cosine of that phase evenly over the depth gives a sinc; its upper
    envelope is returned, as for the other transfer factors.

    Returns 0 for patterns too fine to travel in silicon at all.
    """
    period = np.asarray(period_nm, dtype=float)
    n, _ = silicon_nk(wavelength_nm)
    straight = n / wavelength_nm
    inside = straight**2 - 1 / period**2
    bent = np.sqrt(np.maximum(inside, 0.0))
    cycles = (straight - bent) * depth_um * 1000.0       # phase over the depth, in turns
    return np.where(inside <= 0, 0.0, box_envelope(1.0, cycles))


def backlight_period(n_per_pixel_area, gap_nm, wavelength_nm=1050.0, depth_um=3.0,
                     pitch_nm=1120.0, snr_single=50.0, edge_sigma_nm=0.0):
    """Finest period recoverable with light from behind, in nanometres.

    The same test as :func:`ccdsr.resolution.recoverable_period`, with the
    gap treated as crossed by directed light (the "collimated" model: detail
    coarser than the wavelength crosses any gap, finer detail fades within a
    fraction of a wavelength) and with :func:`depth_washout` as one more
    factor.
    """
    from scipy.optimize import brentq

    def margin(log_period):
        period = math.exp(log_period)
        n_cell = n_per_pixel_area * (period / (2 * pitch_nm)) ** 2
        signal = float(combined_transfer(period, gap_nm, pitch_nm, 0.0, edge_sigma_nm,
                                         None, "collimated", wavelength_nm)
                       * depth_washout(period, wavelength_nm, depth_um))
        return math.log(signal * snr_single * math.sqrt(n_cell) + 1e-300)

    lo, hi = math.log(10.0), math.log(1e9)
    if margin(hi) < 0:
        return math.inf
    if margin(lo) > 0:
        return math.exp(lo)
    return math.exp(brentq(margin, lo, hi))
