import math

import pytest

from ccdsr.resolution import explore, gap_transfer, recoverable_period
from ccdsr.sampling import Scan, Sensor


def test_gap_transfer_limits():
    assert gap_transfer(1e9, 100.0) == pytest.approx(1.0, abs=1e-6)
    # Falls roughly as exp(-2 pi gap / period)
    assert gap_transfer(100.0, 1000.0) < 1e-20


def test_more_samples_help_only_logarithmically():
    one_pass = recoverable_period(1.3e4, 3000.0)
    million_fold = recoverable_period(1.3e10, 3000.0)
    assert one_pass == pytest.approx(2013, rel=0.01)
    assert 1.5 < one_pass / million_fold < 2.0


def test_small_gap_gives_sub_pixel_resolution():
    assert recoverable_period(1.3e4, 300.0) < 0.5 * 1120


def test_explore_names_the_limit():
    s = Sensor()
    fast = explore(s, Scan(fps=10, fraction_per_s=0.2, tilt_tan=1 / 16), gap_nm=300)
    assert fast.limited_by == "motion blur"          # continuous exposure, 65.6 px smear
    frozen = explore(s, Scan(fps=10, fraction_per_s=0.2, tilt_tan=1 / 16,
                             exposure_s=0.0003), gap_nm=30000)
    assert frozen.limited_by == "gap"
    regular = explore(s, Scan(fps=10, fraction_per_s=0.2, exposure_s=0.0003), gap_nm=100)
    assert regular.limited_by == "sampling pattern"  # 5 positions on one line
    assert regular.recoverable_nm == pytest.approx(2 * math.sqrt(2) * 0.51 * 1120, rel=0.02)
