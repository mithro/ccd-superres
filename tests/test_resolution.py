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


def test_collimated_gap_model():
    # Periods above the wavelength cross the gap; finer ones decay exponentially.
    assert gap_transfer(600.0, 5000.0, "collimated", 405.0) == pytest.approx(1.0)
    kappa = 2 * math.pi * math.sqrt(1 / 200.0**2 - 1 / 405.0**2)
    assert gap_transfer(200.0, 100.0, "collimated", 405.0) == pytest.approx(math.exp(-kappa * 100))
    assert gap_transfer(200.0, 100.0, "collimated", 405.0) == pytest.approx(0.065, abs=0.003)


def test_mask_trades_light_for_resolution():
    bare = recoverable_period(1.3e4, 50.0, edge_sigma_nm=100.0)
    masked = recoverable_period(1.3e4, 50.0, edge_sigma_nm=0.0, aperture_nm=100.0)
    assert masked < bare


def test_coded_exposure_keeps_fine_detail():
    from ccdsr.resolution import motion_transfer

    blur = 73_500.0  # nm, continuous exposure at 20% per second and 10 frames per second
    plain = float(motion_transfer(200.0, blur))
    coded = float(motion_transfer(200.0, blur, code_chips=4096))
    assert plain == pytest.approx(200 / (math.pi * blur), rel=1e-6)
    assert coded == pytest.approx(math.sqrt(1 / 4096), rel=0.05)
    # No code: unchanged. Long periods: both pass everything.
    assert float(motion_transfer(200.0, blur, code_chips=0)) == plain
    assert float(motion_transfer(1e9, blur, code_chips=4096)) == pytest.approx(1.0, rel=1e-3)
