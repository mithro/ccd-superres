"""Estimates for the routes that keep ordinary light and still aim at 100 nm.

These are the small calculations behind ``docs/research/ordinary-light-routes.md``.
Every function is a first estimate from a simple model: nothing here has been
checked by a measurement, and only the slit over fine lines by a wave
calculation (``ccdsr/slit_waves.py``, which found the amount of light a slit
passes to be less simple than ``slit_light`` assumes). Lengths are in nanometres
unless a name says otherwise.

The page's central point is that detail finer than the wavelength exists only
within a short distance of the surface, so something sharp has to be brought
that close. The functions answer the questions that follow from it:

* how quickly the fine detail fades with distance (:func:`near_field_transfer`);
* what the pixel must be like once it is that close, and how much more readings
  then buy (:func:`finest_line`, :func:`oversampling_exponent`);
* whether a fine pattern survives inside the pixel's silicon
  (:func:`silicon_pattern_survival`);
* how much light small openings pass (:func:`hole_light`, :func:`slit_light`);
* how large an area can be held that close (:func:`contact_zone_sphere`,
  :func:`contact_band_wedge`);
* what a reading looks like when the light comes through the sensor itself
  (:func:`through_sensor_contrast`).
"""

from __future__ import annotations

import math

import numpy as np

from .backlight import absorption_per_um, silicon_nk
from .resolution import recoverable_period

FWHM_TO_SIGMA = 1 / (2 * math.sqrt(2 * math.log(2)))     # 1 / 2.355


def near_field_transfer(period_nm, distance_nm, wavelength_nm=450.0, index=1.0):
    """Share of a fine pattern's strength left after crossing ``distance_nm``.

    A pattern of period ``p`` lit by light of wavelength ``w`` in a medium of
    refractive index ``n`` travels freely when ``p > w / n``. A finer pattern
    exists only as a field that clings to the surface and fades as
    ``exp(-2 pi d sqrt(1 / p^2 - n^2 / w^2))`` with distance ``d``
    (Goodman, *Introduction to Fourier Optics*, the angular spectrum). This is
    for light arriving straight on; light arriving at a slant moves the
    threshold, not the form.
    """
    period = np.asarray(period_nm, dtype=float)
    k2 = 1 / period**2 - (index / float(wavelength_nm)) ** 2
    decay = np.exp(-2 * np.pi * np.asarray(distance_nm, dtype=float) * np.sqrt(np.maximum(k2, 0.0)))
    return np.where(k2 <= 0, 1.0, decay)


def fade_length_nm(period_nm, wavelength_nm=450.0, index=1.0):
    """Distance over which a fine pattern's strength falls by a factor e (2.72).

    Infinite for a pattern coarse enough to travel freely.
    """
    k2 = 1 / float(period_nm) ** 2 - (index / float(wavelength_nm)) ** 2
    return math.inf if k2 <= 0 else 1 / (2 * math.pi * math.sqrt(k2))


def finest_line(distance_nm, edge_fwhm_nm=0.0, readings=13_000.0, opening_nm=None,
                snr_single=50.0, pitch_nm=1120.0, light_share=None, margin=1.0,
                gap_model="diffuse", wavelength_nm=550.0):
    """Finest line width (half the finest period) the level 0 model gives.

    A thin wrapper around :func:`ccdsr.resolution.recoverable_period` with the
    "matt" blur, so its numbers match Table 4.11b of the design.

    ``edge_fwhm_nm`` is how soft the edge of the pixel's response is (full
    width at half height). ``opening_nm`` is the width of an opening in a mask
    on the pixel; the model takes the light as proportional to it, which suits
    a slit. ``light_share`` overrides that with the share of an open pixel's
    light that actually gets through (use it for a small round hole).

    ``margin`` is how many times stronger than the noise the pattern has to
    be. The default of 1 is the level 0 criterion, the point at which the
    pattern can just be told from noise; 5 is a rule of thumb for a picture
    that looks clean. ``gap_model="collimated"`` replaces the matt blur by
    the wave formula for light of ``wavelength_nm`` arriving straight on.
    """
    snr = snr_single / margin
    if light_share is not None:
        opening = pitch_nm if opening_nm is None else opening_nm
        # recoverable_period scales the signal-to-noise by opening / pitch; undo
        # that and apply the square root of the true share of the light instead.
        snr = snr_single / margin * math.sqrt(light_share) * pitch_nm / opening
    period = recoverable_period(readings, distance_nm, pitch_nm=pitch_nm, snr_single=snr,
                                edge_sigma_nm=edge_fwhm_nm * FWHM_TO_SIGMA,
                                aperture_nm=opening_nm, gap_model=gap_model,
                                wavelength_nm=wavelength_nm)
    return period / 2


def oversampling_exponent(distance_nm, edge_fwhm_nm=0.0, readings=13_000.0, factor=1000.0, **kw):
    """How the finest line shrinks as readings grow: the power ``a`` in
    ``line ~ readings ** -a``, measured between ``readings`` and
    ``factor * readings``.

    A sharp pixel touching the surface gives 0.25: the pixel's own response
    falls only in proportion to the period, and the noise falls as the square
    root of the readings in a cell whose area shrinks with the period squared.
    A blur that removes detail exponentially gives a much smaller number.
    """
    a = finest_line(distance_nm, edge_fwhm_nm, readings, **kw)
    b = finest_line(distance_nm, edge_fwhm_nm, readings * factor, **kw)
    return math.log(a / b) / math.log(factor)


def readings_needed(target_line_nm, distance_nm, edge_fwhm_nm=0.0, **kw):
    """Readings per pixel area at which the model first reaches ``target_line_nm``.

    Returns ``inf`` when more than 1e30 would be needed.
    """
    lo, hi = 1.0, 1e30
    if finest_line(distance_nm, edge_fwhm_nm, hi, **kw) > target_line_nm:
        return math.inf
    if finest_line(distance_nm, edge_fwhm_nm, lo, **kw) <= target_line_nm:
        return lo
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        if finest_line(distance_nm, edge_fwhm_nm, mid, **kw) > target_line_nm:
            lo = mid
        else:
            hi = mid
        if hi / lo < 1.01:
            break
    return hi


def silicon_pattern_survival(period_nm, wavelength_nm, both_sides=False):
    """Share of a fine light pattern's contrast that survives inside silicon, at best.

    A pattern of period ``p`` that has entered the pixel's silicon is the sum
    of light going straight down and light bent sideways. The two drift out of
    step with depth ``z`` at the rate ``2 pi (n / w - sqrt(n^2 / w^2 - 1 / p^2))``
    per nanometre, so the bright lines move across and swap with the dark ones
    as the light goes deeper. The pixel adds up what is absorbed at every
    depth. Light is absorbed as ``exp(-z / L)`` with the absorption depth
    ``L``, and the average of the drifting pattern with that weight is
    ``1 / sqrt(1 + (rate * L)^2)``. That is the case of light bent to one
    side only, where the pattern slides sideways as it goes down. Light
    arriving straight on is bent to both sides equally; the pattern then
    fades and reverses in place, and its average is the smaller
    ``1 / (1 + (rate * L)^2)``, returned with ``both_sides=True``. The first
    is therefore an upper bound.

    Returns 0 for patterns too fine to travel in silicon at all
    (``p < w / n``). Assumes a weak pattern on a bright background and a pixel
    deeper than the absorption depth.
    """
    period = np.asarray(period_nm, dtype=float)
    n, _ = silicon_nk(wavelength_nm)
    straight = n / wavelength_nm
    inside = straight**2 - 1 / period**2
    rate = 2 * np.pi * (straight - np.sqrt(np.maximum(inside, 0.0)))          # per nm
    depth = 1000.0 / absorption_per_um(wavelength_nm)                         # nm
    kept = 1 / (1 + (rate * depth) ** 2)
    return np.where(inside <= 0, 0.0, kept if both_sides else np.sqrt(kept))


def absorption_depth_nm(wavelength_nm):
    """Depth of silicon in which light falls by a factor e (2.72)."""
    return 1000.0 / float(absorption_per_um(wavelength_nm))


def hole_light(diameter_nm, wavelength_nm, film_nm=50.0, pitch_nm=1120.0):
    """Share of an open pixel's light passed by one round hole in a metal film.

    Three factors, each for an ideal metal (Estimate):

    * the hole's share of the pixel's area;
    * for a hole much smaller than the wavelength, Bethe's result that the
      light passed, per unit of hole area, is ``(64 / 27 pi^2) (2 pi r / w)^4``
      (H. A. Bethe, 1944), capped at 1;
    * a round tube narrower than ``w / 1.706`` cannot carry light as a wave,
      and the field fades along the film's thickness ``t`` as
      ``exp(-2 pi t sqrt(1 / (1.706 d)^2 - 1 / w^2))``; the light is the
      square of that.

    Real metals at visible wavelengths pass somewhat more than this, because
    the field reaches a little way into the metal.
    """
    d = float(diameter_nm)
    area = math.pi * (d / 2) ** 2 / pitch_nm**2
    bethe = min(1.0, 64 / (27 * math.pi**2) * (math.pi * d / wavelength_nm) ** 4)
    k2 = 1 / (1.706 * d) ** 2 - 1 / wavelength_nm**2
    tube = 1.0 if k2 <= 0 else math.exp(-4 * math.pi * film_nm * math.sqrt(k2))
    return area * bethe * tube


def slit_light(width_nm, pitch_nm=1120.0):
    """Share of an open pixel's light passed by a slit across the whole pixel.

    A narrow slit in metal, unlike a small hole, always carries the half of
    the light whose electric field points across the slit, however narrow it
    is (Takakura, 2001, gives the resonances; here the passage is simply taken
    as complete for that half and zero for the other half). Estimate.
    """
    return 0.5 * float(width_nm) / pitch_nm


def contact_zone_sphere(radius_of_curvature_m, max_gap_nm, pitch_nm=1120.0):
    """Zone within ``max_gap_nm`` of a flat chip under a gently domed sensor.

    A dome of radius ``R`` touching a flat at one point stands off by
    ``r^2 / (2 R)`` at a distance ``r`` from the touching point (the same
    geometry as Newton's rings). Returns the zone's diameter in micrometres
    and the number of pixels inside it.
    """
    r_nm = math.sqrt(2 * radius_of_curvature_m * 1e9 * max_gap_nm)
    return 2 * r_nm / 1000.0, math.pi * (r_nm / pitch_nm) ** 2


def contact_band_wedge(rise_nm, over_um, max_gap_nm, pitch_nm=1120.0, rows=2464):
    """Band within ``max_gap_nm`` of the chip under a sensor that touches along
    one line and rises by ``rise_nm`` over ``over_um``.

    Returns the band's width in micrometres and the number of pixels in it
    (``rows`` pixels along the touching line).
    """
    width_um = over_um * max_gap_nm / rise_nm
    return width_um, rows * width_um * 1000.0 / pitch_nm


def through_sensor_contrast(reflect_a, reflect_b, wavelength_nm=1050.0, face_pass=None):
    """Contrast between two chip materials when the lamp shines through the sensor.

    The lamp's light crosses the pixel once on its way to the chip. The
    sensor's own face reflects a share ``F`` of it straight back through the
    pixel, and the chip reflects a share ``R`` of what got out, of which a
    share gets back in. With so little absorbed on each crossing, a pixel's
    reading is proportional to ``1 + F + T R``, where ``T`` is the share that
    passes the face twice. For a bare silicon face ``F`` is the reflectance
    of silicon against air and ``T`` is ``(1 - F)^2``. The contrast returned
    is the difference of the two readings divided by their mean.

    This treats the face and the chip as separate mirrors. In near contact
    the gap is far thinner than the wavelength and the two reflect as one
    stack, so the true value depends strongly on the gap: take the result as
    good to a factor of two at best.

    ``face_pass`` sets ``T`` directly and takes the face as not reflecting.
    """
    if face_pass is None:
        n, _ = silicon_nk(wavelength_nm)
        face = ((n - 1) / (n + 1)) ** 2
        face_pass = (1 - face) ** 2
    else:
        face = 0.0
    a = 1 + face + face_pass * reflect_a
    b = 1 + face + face_pass * reflect_b
    return abs(a - b) / ((a + b) / 2)


def lamp_needed_mw_per_cm2(light_share, wavelength_nm, electrons=2500.0, frames_per_s=30.0,
                           pitch_nm=1120.0):
    """Lamp brightness at the chip needed to fill a reading, in mW per square cm.

    ``light_share`` is the share of the light falling on one pixel's area
    that ends up detected. A reading of ``electrons`` in each frame then
    needs ``electrons * frames_per_s / light_share`` photons a second on an
    area of one pixel, each carrying ``h c / wavelength`` of energy.
    """
    photon_j = 6.626e-34 * 2.998e8 / (wavelength_nm * 1e-9)
    area_cm2 = (pitch_nm * 1e-7) ** 2
    return electrons * frames_per_s / light_share * photon_j / area_cm2 * 1e3
