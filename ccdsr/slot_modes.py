"""Wave solution for light travelling along the slot between chip and sensor.

``ccdsr/light_entry.py`` follows straight rays along the slot, which stops
being valid when the slot is only a few wavelengths high. This module solves
the same problem with waves, exactly, for the same idealised geometry: a
layer of air between two flat, uniform materials.

In such a slot light can only travel in a set of fixed patterns across the
gap, called modes. Mode number ``m`` has ``m`` half-waves across the gap, so
it corresponds to a ray at the grazing angle whose sine is about
``m * wavelength / (2 * gap)``. Each mode loses power at its own steady rate
as it travels, because a little of it leaks into the two materials at every
point. The mode with the fewest half-waves is the flattest and lasts longest.

The modes are found from the standard condition for a layer between two
reflecting surfaces: a wave that crosses the gap, reflects, crosses back and
reflects again must return in step with itself,

    r_chip * r_sensor * exp(2i * kx * gap) = 1,

where ``kx`` is the (complex) wavenumber across the gap and ``r`` are the
Fresnel reflection coefficients of the two surfaces for that ``kx``.

Lengths are in nanometres.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .light_entry import SILICON


def _reflection(kx, k0, index, polarisation):
    """Field reflection coefficient of a surface, for a wave in air.

    ``kx`` is the wavenumber across the gap. The wave in the material is the
    one travelling away from the surface.
    """
    n2 = complex(index) ** 2
    kxm = np.sqrt((n2 - 1.0) * k0**2 + kx**2 + 0j)
    kxm = np.where(kxm.real < 0, -kxm, kxm)
    if polarisation == "s":
        return (kx - kxm) / (kx + kxm)
    if polarisation == "p":
        return (n2 * kx - kxm) / (n2 * kx + kxm)
    raise ValueError(f"unknown polarisation {polarisation!r}")


def _mismatch(kx, gap_nm, k0, chip, sensor, polarisation):
    return (_reflection(kx, k0, chip, polarisation) * _reflection(kx, k0, sensor, polarisation)
            * np.exp(2j * kx * gap_nm) - 1.0)


@dataclass(frozen=True)
class Mode:
    """One pattern in which light can travel along the slot."""

    polarisation: str       #: "s" (field along the surfaces) or "p" (field across them)
    kx: complex             #: wavenumber across the gap, per nanometre
    grazing_deg: float      #: grazing angle of the matching ray, degrees
    loss_per_nm: float      #: rate at which the mode's power falls with distance
    to_sensor: float        #: share of the lost power that goes into the sensor

    @property
    def reach_nm(self):
        """Distance over which the power falls to 1 %."""
        return float(np.log(100.0) / self.loss_per_nm)

    def left_after(self, distance_nm):
        """Share of the mode's power left after ``distance_nm``."""
        return float(np.exp(-self.loss_per_nm * distance_nm))


def slot_modes(gap_nm, wavelength_nm=550.0, chip=SILICON, sensor=SILICON,
               polarisation="s", tolerance=1e-10):
    """All travelling modes of the slot for one polarisation, flattest first.

    Roots of the round-trip condition are found by Newton's method from a
    fine set of starting points, then checked and de-duplicated. Only modes
    that travel (whose matching ray angle is below 90 degrees) are returned.
    """
    k0 = 2 * np.pi / wavelength_nm
    found = []
    most = int(np.ceil(2 * gap_nm / wavelength_nm)) + 1
    starts = [(m + d) * np.pi / gap_nm * (1 - tilt * 1j) for m in range(most + 1)
              for d in np.arange(0.0, 1.0, 0.125) for tilt in (0.0, 0.02, 0.1) if m + d > 0]
    for start in starts:
        kx = complex(start)
        with np.errstate(all="ignore"):
            for _ in range(60):
                f = _mismatch(kx, gap_nm, k0, chip, sensor, polarisation)
                step = 1e-7 * k0
                slope = (_mismatch(kx + step, gap_nm, k0, chip, sensor, polarisation) - f) / step
                if slope == 0 or not np.isfinite(slope) or not np.isfinite(f):
                    break
                change = f / slope
                kx = kx - change
                if abs(change) < tolerance * k0:
                    break
            miss = abs(_mismatch(kx, gap_nm, k0, chip, sensor, polarisation))
        if not np.isfinite(kx) or not np.isfinite(miss) or miss > 1e-6:
            continue
        if not (0 < kx.real < k0) or kx.real * gap_nm < 0.05:
            continue
        beta = np.sqrt(k0**2 - kx**2 + 0j)
        if beta.real <= 0 or beta.imag <= 0:
            continue
        if any(abs(kx - other) < 1e-6 * k0 for other in found):
            continue
        found.append(kx)
    modes = []
    for kx in sorted(found, key=lambda v: v.real):
        beta = np.sqrt(k0**2 - kx**2 + 0j)
        lost_chip = 1 - abs(_reflection(kx, k0, chip, polarisation)) ** 2
        lost_sensor = 1 - abs(_reflection(kx, k0, sensor, polarisation)) ** 2
        modes.append(Mode(
            polarisation=polarisation,
            kx=complex(kx),
            grazing_deg=float(np.degrees(np.arcsin(min(1.0, kx.real / k0)))),
            loss_per_nm=float(2 * beta.imag),
            to_sensor=float(lost_sensor / (lost_chip + lost_sensor)),
        ))
    return modes


@dataclass(frozen=True)
class SlotWaveLight:
    """What the wave solution gives at one distance into the slot."""

    reading: float          #: light a pixel absorbs, relative to an uncovered pixel in the same light
    grazing_deg: float      #: grazing angle of the mode that delivers most of it
    last_touch_nm: float    #: half a hop of the matching ray: gap / tan(grazing angle)
    modes: int              #: number of travelling modes, both polarisations
    best_reach_nm: float    #: distance over which the longest-lived mode falls to 1 %


def wave_light(gap_nm, distance_nm=1.38e6, wavelength_nm=550.0, chip=SILICON, sensor=SILICON):
    """Light reaching a pixel ``distance_nm`` in from the open edge, with waves.

    The open edge is taken to be evenly lit from all directions, as in
    :func:`ccdsr.light_entry.slot_light`. Such light puts the same power
    into every mode: a quarter of ``brightness * wavelength`` per mode and
    polarisation, the wave counterpart of the rays' cosine weighting (a
    slot of height ``h`` holds ``2 h / wavelength`` modes, which between
    them take in the ``brightness * h`` that falls on the opening). A
    pixel's reading is the power the modes lose into the sensor per unit
    length, relative to the brightness an uncovered pixel would see.
    """
    total = 0.0
    best = (0.0, float("nan"))
    count = 0
    reach = 0.0
    for polarisation in ("s", "p"):
        for mode in slot_modes(gap_nm, wavelength_nm, chip, sensor, polarisation):
            count += 1
            reach = max(reach, mode.reach_nm)
            part = (wavelength_nm / 4.0) * mode.loss_per_nm * mode.to_sensor \
                * mode.left_after(distance_nm)
            total += part
            if part > best[0]:
                best = (part, mode.grazing_deg)
    angle = best[1]
    touch = gap_nm / np.tan(np.radians(angle)) if np.isfinite(angle) and angle > 0 else float("nan")
    return SlotWaveLight(reading=float(total), grazing_deg=float(angle),
                         last_touch_nm=float(touch), modes=count, best_reach_nm=float(reach))
