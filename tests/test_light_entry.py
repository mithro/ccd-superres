import math

import numpy as np
import pytest

from ccdsr.light_entry import (ALUMINIUM, GLASS, SILICON, fresnel_reflectance,
                               light_under_sensor, ray_survival, slot_light)


def test_fresnel_known_values():
    # Straight on, R = |(n - 1) / (n + 1)|^2 for both polarisations.
    rs, rp = fresnel_reflectance(1.5, math.pi / 2)
    assert rs == pytest.approx(0.04) and rp == pytest.approx(0.04)
    # Brewster's angle for glass of index 1.5: no p reflection.
    brewster_from_normal = math.atan(1.5)
    _, rp = fresnel_reflectance(1.5, math.pi / 2 - brewster_from_normal)
    assert rp == pytest.approx(0.0, abs=1e-12)
    # Everything reflects completely at grazing incidence.
    for index in (SILICON, ALUMINIUM, GLASS):
        rs, rp = fresnel_reflectance(index, 1e-7)
        assert rs == pytest.approx(1.0, abs=1e-5) and rp == pytest.approx(1.0, abs=1e-5)


def test_no_distance_means_all_light_is_still_there():
    start = slot_light(0.0)
    assert start.surviving == pytest.approx(1.0, rel=1e-3)


def test_single_ray_matches_hand_count():
    # One ray at 45 degrees, 10 slot heights in: 5 hits on each surface.
    rs_c, rp_c = fresnel_reflectance(SILICON, math.pi / 4)
    rs_g, rp_g = fresnel_reflectance(GLASS, math.pi / 4)
    s, p = ray_survival(10, math.pi / 4, chip=SILICON, sensor=GLASS)
    assert s == pytest.approx((rs_c * rs_g) ** 5)
    assert p == pytest.approx((rp_c * rp_g) ** 5)


def test_light_falls_and_flattens_with_distance():
    readings = [slot_light(r).reading for r in (10, 100, 1000, 10000)]
    assert all(a > b for a, b in zip(readings, readings[1:]))
    # Far in, the reading falls as the power -3/2 of the distance.
    slope = math.log(readings[3] / readings[2]) / math.log(10)
    assert slope == pytest.approx(-1.5, abs=0.1)


def test_only_grazing_light_reaches_the_middle():
    mid = light_under_sensor(1000.0)
    assert mid.ratio == pytest.approx(1380)
    assert mid.grazing_deg < 2.0
    assert mid.arrival_deg > 88.0
    assert mid.reading == pytest.approx(2.6e-6, rel=0.05)
    # The light last touched the chip tens of micrometres away, not one gap away.
    assert 30 < mid.hop_in_gaps / 2 < 50


def test_hop_grows_as_square_root_of_distance_times_gap():
    a, b = light_under_sensor(300.0), light_under_sensor(3000.0)
    hop_a, hop_b = a.hop_in_gaps * 300.0, b.hop_in_gaps * 3000.0
    assert hop_b / hop_a == pytest.approx(math.sqrt(10), rel=0.05)


def test_conclusion_does_not_depend_on_the_material():
    for chip in (SILICON, ALUMINIUM, GLASS):
        mid = light_under_sensor(1000.0, chip=chip)
        assert 1e-6 < mid.reading < 1e-5
        assert mid.hop_in_gaps / 2 > 25
    # nor on the round values chosen for silicon
    for index in (3.9 + 0.02j, 4.3 + 0.07j):
        mid = light_under_sensor(1000.0, chip=index, sensor=index)
        assert mid.reading == pytest.approx(2.6e-6, rel=0.15)


def test_finite_everywhere():
    for ratio in (0.0, 1e-3, 1.0, 1e3, 1e6):
        got = slot_light(ratio)
        assert np.isfinite(got.surviving) and np.isfinite(got.reading)
