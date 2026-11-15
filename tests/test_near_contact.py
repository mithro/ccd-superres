import math

import pytest

from ccdsr.near_contact import (absorption_depth_nm, contact_band_wedge, contact_zone_sphere,
                                fade_length_nm, finest_line, hole_light, near_field_transfer,
                                oversampling_exponent, readings_needed, silicon_pattern_survival,
                                slit_light, through_sensor_contrast)
from ccdsr.resolution import recoverable_period


def test_fade_length_by_hand():
    # 200 nm repeat, 450 nm light: sqrt(1/200^2 - 1/450^2) = 4.479e-3 per nm,
    # so the fade length is 1 / (2 pi * 4.479e-3) = 35.5 nm.
    assert fade_length_nm(200, 450) == pytest.approx(35.5, abs=0.1)
    # A repeat longer than the wavelength in the medium travels freely.
    assert math.isinf(fade_length_nm(500, 450))
    assert math.isinf(fade_length_nm(310, 450, index=1.5))
    assert fade_length_nm(200, 450, index=1.5) > fade_length_nm(200, 450)


def test_near_field_transfer_matches_fade_length():
    length = fade_length_nm(200, 450)
    assert float(near_field_transfer(200, length, 450)) == pytest.approx(math.exp(-1))
    assert float(near_field_transfer(200, 0, 450)) == 1.0
    assert float(near_field_transfer(600, 1e6, 450)) == 1.0


def test_finest_line_matches_design_table():
    # Rows of Table 4.11b of the design: half the recoverable period.
    assert finest_line(140) == pytest.approx(100, abs=1)
    assert finest_line(300, 300) == pytest.approx(219, abs=1)
    assert finest_line(1000, 300) == pytest.approx(439, abs=1)
    assert finest_line(300) == pytest.approx(recoverable_period(13_000, 300) / 2)


def test_light_share_replaces_the_opening_scaling():
    # A share equal to (opening / pitch)^2 is what the model assumes by default.
    a = finest_line(50, 30, opening_nm=200)
    b = finest_line(50, 30, opening_nm=200, light_share=(200 / 1120) ** 2)
    assert a == pytest.approx(b, rel=1e-6)
    # More light through the same opening gives a finer line.
    assert finest_line(50, 30, opening_nm=200, light_share=0.09) < a


def test_oversampling_exponent_regimes():
    # A sharp pixel touching the surface follows a power law of one quarter.
    assert oversampling_exponent(0, 0) == pytest.approx(0.25, abs=0.005)
    # Any distance or softness makes it much smaller, and more of either smaller still.
    assert oversampling_exponent(50, 30) < 0.1
    assert oversampling_exponent(1000, 300) < oversampling_exponent(50, 30)


def test_readings_needed_is_consistent():
    n = readings_needed(100, 200, 0)
    assert finest_line(200, 0, n) <= 100 < finest_line(200, 0, n / 1.05)
    assert readings_needed(100, 140, 0) == pytest.approx(13_000, rel=0.1)
    assert readings_needed(100, 300, 0) > 1000 * readings_needed(100, 140, 0)
    assert math.isinf(readings_needed(100, 3000, 300))


def test_silicon_pattern_survival():
    # Violet light is absorbed near the surface and keeps the pattern; red loses it.
    assert float(silicon_pattern_survival(200, 405)) > 0.7
    assert float(silicon_pattern_survival(200, 630)) < 0.05
    # A pattern too fine to travel in silicon gives nothing: 630 nm / 3.88 = 162 nm.
    assert float(silicon_pattern_survival(150, 630)) == 0.0
    # By hand at 450 nm, 200 nm repeat: n = 4.67, depth 415 nm.
    n_over_w = 4.67 / 450
    rate = 2 * math.pi * (n_over_w - math.sqrt(n_over_w**2 - 1 / 200**2))
    expected = 1 / math.sqrt(1 + (rate * absorption_depth_nm(450)) ** 2)
    assert float(silicon_pattern_survival(200, 450)) == pytest.approx(expected, rel=0.03)


def test_holes_and_slits():
    # Bethe: halving a small hole costs 2^4 from the law and 2^2 from the area, and more from the tube.
    assert hole_light(100, 450) / hole_light(50, 450) > 64
    # A slit always passes half the light that falls on it.
    assert slit_light(100) == pytest.approx(0.5 * 100 / 1120)
    assert slit_light(100) > 1000 * hole_light(100, 450)
    # A hole wider than the cut-off is not choked: 600 nm > 450 / 1.706.
    area = math.pi * 300**2 / 1120**2
    assert hole_light(600, 450) == pytest.approx(area)


def test_contact_geometry():
    # r^2 / 2R = 100 nm at R = 1 m gives r = 447 um.
    diameter, pixels = contact_zone_sphere(1.0, 100)
    assert diameter == pytest.approx(894.4, abs=0.1)
    assert pixels == pytest.approx(math.pi * (447.2e3 / 1120) ** 2, rel=1e-3)
    width, pixels = contact_band_wedge(1000, 3680, 100)
    assert width == pytest.approx(368.0)
    assert pixels == pytest.approx(2464 * 368e3 / 1120)


def test_through_sensor_contrast():
    # With every bit of light passing the face: readings 1.95 and 1.31.
    assert through_sensor_contrast(0.95, 0.31, face_pass=1.0) == pytest.approx(0.64 / 1.63, rel=1e-6)
    assert through_sensor_contrast(0.5, 0.5) == 0.0
    assert 0.15 < through_sensor_contrast(0.95, 0.31) < 0.3
