"""Rough estimate of how much ordinary light gets under the sensor.

The sensor covers the area it looks at, so ordinary light can only come in
from the side, through the slot between the chip and the sensor. This module
follows straight rays along that slot. A ray that makes a grazing angle
``phi`` with the two surfaces hits them alternately, ``tan(phi) / gap`` times
per unit length, and loses a share of its power at every hit. What the sensor
absorbs at its hits is the reading.

It is a ray model in two dimensions (the slot seen from the side), with flat
uniform surfaces and Fresnel reflection. A slot a few micrometres high or
less is too shallow for rays to be trusted, so the numbers are a first
indication of scale and nothing more: see ``docs/light-entry.md``.

Lengths only ever appear as the ratio of distance travelled to slot height,
so any unit may be used as long as both are the same.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

#: Refractive indices at a wavelength of 550 nm (green light), as ``n + ik``.
#: Round values from general knowledge, to be replaced by tabulated ones
#: under the data collection items of the plan. The results change little
#: with them (see ``tests/test_light_entry.py``).
SILICON = 4.08 + 0.03j
ALUMINIUM = 0.96 + 6.7j
GLASS = 1.46 + 0.0j


def fresnel_reflectance(index, grazing_angle):
    """Share of power reflected from a flat surface in air.

    ``index`` is the complex refractive index of the material and
    ``grazing_angle`` the angle between the ray and the surface, in radians.
    Returns ``(Rs, Rp)`` for the two polarisations: electric field parallel
    to the surface (s) and in the plane of the ray and the normal (p).
    """
    phi = np.asarray(grazing_angle, dtype=float)
    cos_i = np.sin(phi)                      # cosine of the angle from the normal
    sin_i = np.cos(phi)
    n = complex(index)
    cos_t = np.sqrt(1.0 - (sin_i / n) ** 2 + 0j)
    rs = (cos_i - n * cos_t) / (cos_i + n * cos_t)
    rp = (n * cos_i - cos_t) / (n * cos_i + cos_t)
    return np.abs(rs) ** 2, np.abs(rp) ** 2


@dataclass(frozen=True)
class SlotLight:
    """What the ray model gives at one distance into the slot."""

    ratio: float            #: distance travelled divided by slot height
    surviving: float        #: share of the light that entered and is still travelling
    reading: float          #: light a pixel absorbs, relative to an uncovered pixel in the same light
    grazing_deg: float      #: typical grazing angle of the light a pixel absorbs, degrees
    arrival_deg: float      #: the same measured from the pixel's normal, degrees
    hop_in_gaps: float      #: distance between two hits on the chip, in slot heights


def _angles(n=20001):
    # Dense near grazing incidence, where all the surviving light is.
    return np.logspace(-6, np.log10(np.pi / 2 - 1e-6), n)


def _integrate(y, x):
    return float(np.sum(0.5 * (y[1:] + y[:-1]) * np.diff(x)))


def ray_survival(ratio, grazing_angle, chip=SILICON, sensor=SILICON):
    """Share of one ray's power left after travelling ``ratio`` slot heights.

    Returns ``(s, p)`` for the two polarisations. The ray has hit each
    surface ``ratio * tan(grazing_angle) / 2`` times.
    """
    phi = np.asarray(grazing_angle, dtype=float)
    hits_each = ratio * np.tan(phi) / 2.0
    out = []
    for rc, rs in zip(fresnel_reflectance(chip, phi), fresnel_reflectance(sensor, phi)):
        # log form keeps tiny survivals from underflowing to nan
        with np.errstate(divide="ignore", invalid="ignore"):
            out.append(np.exp(np.where(hits_each > 0, hits_each * (np.log(rc) + np.log(rs)), 0.0)))
    return tuple(out)


def slot_light(ratio, chip=SILICON, sensor=SILICON):
    """Light reaching a point ``ratio`` slot heights in from the open edge.

    The edge is taken to be evenly lit from all directions (a matt source),
    which weights each grazing angle by its cosine. Both polarisations are
    followed separately and averaged.

    ``reading`` is the power a pixel there absorbs divided by what the same
    pixel would absorb lying uncovered under the same light, taking the
    uncovered pixel to absorb everything. With ``E`` the brightness falling
    on the slot's opening, the opening of height ``h`` admits ``E h`` per
    unit width; a ray at angle ``phi`` hits the sensor ``tan(phi) / (2 h)``
    times per unit length; so the height cancels and only ``ratio`` matters.
    """
    phi = _angles()
    weight = np.cos(phi)                     # integrates to 1 over 0..pi/2
    surviving = 0.0
    absorbed = np.zeros_like(phi)
    sensor_r = fresnel_reflectance(sensor, phi)
    for t, rs in zip(ray_survival(ratio, phi, chip, sensor), sensor_r):
        surviving += 0.5 * _integrate(weight * t, phi)
        absorbed += 0.5 * weight * t * np.tan(phi) / 2.0 * (1.0 - rs)
    reading = _integrate(absorbed, phi)
    # Typical angle: the one below which half the absorbed light arrives.
    cum = np.concatenate([[0.0], np.cumsum(0.5 * (absorbed[1:] + absorbed[:-1]) * np.diff(phi))])
    typical = float(np.interp(0.5 * cum[-1], cum, phi)) if cum[-1] > 0 else float("nan")
    return SlotLight(
        ratio=float(ratio),
        surviving=surviving,
        reading=reading,
        grazing_deg=float(np.degrees(typical)),
        arrival_deg=float(90.0 - np.degrees(typical)),
        hop_in_gaps=float(2.0 / np.tan(typical)),
    )


def flattest_wave_angle(gap_nm, wavelength_nm=550.0):
    """Smallest grazing angle a wave confined to the slot can have, radians.

    Light squeezed between two surfaces a distance ``gap`` apart cannot
    travel flatter than ``asin(wavelength / (2 gap))``: across the slot it
    must fit at least half a wave. Returns ``nan`` when the gap is under
    half a wavelength, where no travelling wave of this kind fits at all.
    This is the textbook result for two mirrors; real walls change the
    details and not the scale.
    """
    x = wavelength_nm / (2.0 * gap_nm)
    return float(np.arcsin(x)) if x <= 1.0 else float("nan")


def wave_limited_survival(gap_nm, distance_nm=1.38e6, wavelength_nm=550.0,
                          chip=SILICON, sensor=SILICON):
    """Share of the flattest allowed wave left after ``distance``.

    Applies the ray model's loss per touch to a ray at the flattest angle a
    wave can take (:func:`flattest_wave_angle`). Rays flatter than that,
    which carry nearly all the light in :func:`slot_light` when the gap is
    small, do not exist as waves, so this is the better guide to scale
    there. Returns ``(s, p)`` for the two polarisations, or ``(0.0, 0.0)``
    when the gap is under half a wavelength.
    """
    phi = flattest_wave_angle(gap_nm, wavelength_nm)
    if not np.isfinite(phi):
        return 0.0, 0.0
    s, p = ray_survival(distance_nm / gap_nm, phi, chip, sensor)
    return float(s), float(p)


def reach_of_flattest_wave(gap_nm, share=0.01, wavelength_nm=550.0,
                           chip=SILICON, sensor=SILICON):
    """Distance in at which the flattest allowed wave has fallen to ``share``.

    Returns ``(s, p)`` in nanometres for the two polarisations, or
    ``(0.0, 0.0)`` when the gap is under half a wavelength.
    """
    phi = flattest_wave_angle(gap_nm, wavelength_nm)
    if not np.isfinite(phi):
        return 0.0, 0.0
    out = []
    for rc, rs in zip(fresnel_reflectance(chip, phi), fresnel_reflectance(sensor, phi)):
        loss_per_nm = np.tan(phi) / (2.0 * gap_nm) * -(np.log(rc) + np.log(rs))
        out.append(float(-np.log(share) / loss_per_nm))
    return tuple(out)


def rays_are_self_consistent(gap_nm, distance_nm=1.38e6, wavelength_nm=550.0,
                             chip=SILICON, sensor=SILICON):
    """Whether the typical ray of :func:`slot_light` is one a wave could follow."""
    phi = flattest_wave_angle(gap_nm, wavelength_nm)
    typical = np.radians(slot_light(distance_nm / gap_nm, chip, sensor).grazing_deg)
    return bool(np.isfinite(phi) and typical >= phi)


def light_under_sensor(gap_nm, distance_nm=1.38e6, chip=SILICON, sensor=SILICON):
    """:func:`slot_light` for a gap and a distance in from the edge.

    The default distance is half the short side of the baseline sensor's
    light-sensitive area (2.76 mm), the furthest any pixel is from an edge.
    """
    return slot_light(distance_nm / gap_nm, chip=chip, sensor=sensor)
