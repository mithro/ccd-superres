import math

import numpy as np
import pytest

from ccdsr.sampling import Scan, Sensor, phase_coverage, scan_budget


def test_twenty_percent_per_second_at_ten_fps():
    b = scan_budget(Sensor(), Scan(fps=10, fraction_per_s=0.2))
    assert b.samples_per_point == pytest.approx(50)
    assert b.shift_px == pytest.approx(65.6)
    assert b.time_under_sensor_s == pytest.approx(5)
    assert b.blur_px == pytest.approx(65.6)          # continuous exposure
    assert b.coverage.distinct_phases == 5           # 0.6 px remainder repeats every 5
    assert b.coverage.largest_gap_along_px == pytest.approx(0.2)
    assert b.coverage.largest_gap_across_px == pytest.approx(1.0)


def test_samples_per_point_is_fps_over_fraction():
    for fps, frac in [(30, 0.1), (5, 0.5), (100, 0.01)]:
        b = scan_budget(Sensor(), Scan(fps=fps, fraction_per_s=frac))
        assert b.samples_per_point == pytest.approx(fps / frac)


def test_speed_can_be_given_either_way():
    s = Sensor()
    a = scan_budget(s, Scan(fps=10, fraction_per_s=0.2))
    b = scan_budget(s, Scan(fps=10, speed_um_per_s=0.2 * s.length_um))
    assert a.shift_px == pytest.approx(b.shift_px)
    with pytest.raises(ValueError):
        scan_budget(s, Scan(fps=10))


def test_short_exposure_reduces_blur():
    b_exp = 0.0003
    b = scan_budget(Sensor(), Scan(fps=10, fraction_per_s=0.2, exposure_s=b_exp))
    assert b.blur_px == pytest.approx(65.6 * b_exp * 10)
    assert b.exposure_for_quarter_px_s == pytest.approx(0.25 / 65.6 / 10)


def test_tilt_and_jitter_both_fill_the_pixel():
    s = Sensor()
    plain = scan_budget(s, Scan(fps=10, fraction_per_s=0.2)).coverage
    tilted = scan_budget(s, Scan(fps=10, fraction_per_s=0.2, tilt_tan=1 / 16)).coverage
    jittered = scan_budget(s, Scan(fps=10, fraction_per_s=0.2, jitter_px=0.5)).coverage
    assert tilted.largest_hole_px < 0.5 * plain.largest_hole_px
    assert jittered.largest_hole_px < 0.5 * plain.largest_hole_px
    assert jittered.distinct_phases == jittered.n_samples


def test_perfect_grid_has_efficiency_one():
    n = 8
    g = (np.arange(n) + 0.5) / n
    pts = np.stack(np.meshgrid(g, g), axis=-1).reshape(-1, 2)
    c = phase_coverage(pts)
    assert c.largest_hole_px == pytest.approx(math.sqrt(0.5) / n, rel=1e-6)
    assert c.efficiency == pytest.approx(1.0, rel=1e-6)
