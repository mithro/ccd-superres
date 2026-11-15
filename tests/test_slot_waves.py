import math

import numpy as np
import pytest
from scipy.special import hankel1

from ccdsr.edge_scatter import run
from ccdsr.fdfd import solve
from ccdsr.light_entry import (ALUMINIUM, SILICON, flattest_wave_angle, light_under_sensor,
                               reach_of_flattest_wave)
from ccdsr.slot_modes import slot_modes, wave_light


def test_perfect_mirrors_give_the_textbook_modes():
    # Between two near-perfect mirrors mode m has m half-waves across the gap
    # and loses almost nothing.
    mirror = 0.01 + 1000j
    modes = slot_modes(2000.0, chip=mirror, sensor=mirror, polarisation="s")
    assert len(modes) == 7                     # 2 * gap / wavelength = 7.3
    for m, mode in enumerate(modes, start=1):
        assert math.sin(math.radians(mode.grazing_deg)) == pytest.approx(m * 550.0 / 4000.0, rel=2e-3)
        assert mode.reach_nm > 1e7


def test_every_mode_satisfies_the_round_trip_condition():
    from ccdsr.slot_modes import _mismatch
    k0 = 2 * math.pi / 550.0
    for polarisation in ("s", "p"):
        modes = slot_modes(3000.0, polarisation=polarisation)
        assert len(modes) >= 9
        for mode in modes:
            assert abs(_mismatch(mode.kx, 3000.0, k0, SILICON, SILICON, polarisation)) < 1e-6
            assert mode.loss_per_nm > 0
            assert mode.to_sensor == pytest.approx(0.5)       # same material both sides


def test_flattest_mode_matches_the_simple_wave_limit():
    # The light entry page estimated this from a ray at the flattest angle.
    for gap in (1000.0, 3000.0, 10000.0):
        mode = slot_modes(gap, polarisation="s")[0]
        assert mode.grazing_deg == pytest.approx(math.degrees(flattest_wave_angle(gap)), rel=0.01)
        assert mode.reach_nm == pytest.approx(reach_of_flattest_wave(gap)[0], rel=0.02)


def test_waves_agree_with_rays_where_rays_are_valid():
    for gap in (10000.0, 30000.0):
        wave, ray = wave_light(gap), light_under_sensor(gap)
        assert wave.reading == pytest.approx(ray.reading, rel=0.15)
        assert wave.last_touch_nm == pytest.approx(ray.hop_in_gaps * gap / 2, rel=0.15)


def test_no_side_light_reaches_the_middle_under_two_micrometres():
    assert wave_light(300.0).reading < 1e-100
    assert wave_light(1000.0).reading < 1e-40
    assert wave_light(2000.0).reading < 1e-8
    assert wave_light(3000.0).reading == pytest.approx(3.9e-6, rel=0.1)
    assert wave_light(5000.0).reading == pytest.approx(2.4e-5, rel=0.1)
    # a more reflective chip helps only a little
    assert wave_light(1000.0, chip=ALUMINIUM).reading < 1e-20


def test_solver_reproduces_a_point_source_in_empty_space():
    n, spacing = 240, 25.0
    source = np.zeros((n, n), dtype=complex)
    source[n // 2, n // 2] = 1 / spacing**2
    field = solve(np.ones((n, n)), source, 550.0, spacing)
    r = np.arange(10, 60) * spacing
    exact = -0.25j * hankel1(0, 2 * math.pi / 550.0 * r)
    got = field.e[n // 2 + np.arange(10, 60), n // 2]
    assert np.abs(got) == pytest.approx(np.abs(exact), rel=0.02)
    assert np.max(np.abs(got - exact) / np.abs(exact)) < 0.1      # phase drifts slowly on a grid
    # nothing comes back from the absorbing edges: the power leaving through
    # a small square round the source equals that through a larger one
    def leaving(half):
        c, side = n // 2, slice(n // 2 - half, n // 2 + half + 1)
        return (np.sum(field.flow_x(c + half)[side]) - np.sum(field.flow_x(c - half)[side])
                + np.sum(field.flow_z(c + half)[side]) - np.sum(field.flow_z(c - half)[side]))

    assert leaving(30) > 0 and leaving(60) == pytest.approx(leaving(30), rel=0.03)


def test_solver_and_mode_theory_agree_on_how_fast_slot_light_dies():
    # Two independent methods: launch the first mode in a 1 um slot between
    # silicon walls and measure how fast its power falls.
    result = run(gap_nm=1000.0, height_nm=0.0, before_nm=3000.0, after_nm=15000.0, spacing_nm=20.0)
    x, light = result.x_nm, result.bare
    keep = (x > 0) & (x < 12000)
    measured = -np.polyfit(x[keep], np.log(light[keep]), 1)[0]
    expected = slot_modes(1000.0, polarisation="s")[0].loss_per_nm
    assert measured == pytest.approx(expected, rel=0.15)           # 10 % low at this grid spacing


def test_a_line_on_the_chip_changes_the_reading_far_from_itself():
    result = run(gap_nm=3000.0, height_nm=300.0, before_nm=8000.0, after_nm=12000.0)
    assert result.arriving > 0
    assert 0 < result.thrown_up() < 0.05          # only a small share goes up near the line
    first, last = result.extent_nm()
    assert last - first > 2 * result.gap_nm       # the mark is spread over more than two gaps
    assert result.peak_ratio() > 1.3
    # with no line the two runs are identical
    empty = run(gap_nm=3000.0, height_nm=0.0, before_nm=3000.0, after_nm=3000.0)
    assert np.allclose(empty.bare, empty.with_feature)
