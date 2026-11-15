import math

import numpy as np
import pytest

from ccdsr.backlight import (absorption_per_um, backlight_period, backlight_reading,
                             best_wavelength, chip_transmission, depth_washout,
                             pixel_absorption, silicon_nk)
from ccdsr.resolution import recoverable_period


def test_table_values_match_the_source():
    # Rows copied by hand from the Green (2008) table.
    n, k = silicon_nk(550.0)
    assert n == pytest.approx(4.077) and k == pytest.approx(2.7968e-2)
    n, k = silicon_nk(1000.0)
    assert n == pytest.approx(3.572) and k == pytest.approx(5.0930e-4)
    with pytest.raises(ValueError):
        silicon_nk(2000.0)


def test_absorption_rate_by_hand():
    # 4 pi k / wavelength at 1000 nm: 4 pi * 5.093e-4 / 1.0 um = 6.40e-3 per um
    assert absorption_per_um(1000.0) == pytest.approx(6.40e-3, rel=1e-3)
    # Green light is gone within a few micrometres; 1100 nm crosses a whole wafer.
    assert math.exp(-absorption_per_um(550.0) * 10) < 0.01
    assert math.exp(-absorption_per_um(1100.0) * 500) > 0.8


def test_chip_transmission_by_hand():
    # 1050 nm through 500 um: n = 3.556, rate 1.630e-3 per um.
    n = 3.556
    enter = 1 - ((1 - n) / (1 + n)) ** 2
    through = math.exp(-1.630e-3 * 500)
    leave = (1 - ((n - 1.45) / (n + 1.45)) ** 2) * (1 - ((1.45 - 1) / (1.45 + 1)) ** 2)
    assert chip_transmission(1050.0, 500.0) == pytest.approx(enter * through * leave, rel=1e-3)
    assert chip_transmission(1050.0, 500.0) == pytest.approx(0.241, abs=0.002)
    assert chip_transmission(550.0, 500.0) < 1e-100       # visible light does not get through


def test_pixel_absorption_by_hand():
    n = 3.556
    expected = (1 - ((1 - n) / (1 + n)) ** 2) * (1 - math.exp(-1.630e-3 * 3))
    assert pixel_absorption(1050.0) == pytest.approx(expected, rel=1e-3)
    assert pixel_absorption(550.0) > 0.5                   # a thin pixel catches green light
    assert pixel_absorption(1050.0) < 0.005                # and very little near-infrared


def test_reading_peaks_between_two_losses():
    # Short wavelengths die in the chip, long ones pass through the pixel.
    for thickness, low, high in ((100.0, 950, 1010), (500.0, 1020, 1070), (750.0, 1030, 1080)):
        wavelength, reading = best_wavelength(thickness)
        assert low < wavelength < high
        assert reading > backlight_reading(wavelength - 80, thickness)
        assert reading > backlight_reading(wavelength + 80, thickness)
    assert best_wavelength(500.0)[1] == pytest.approx(8.2e-4, rel=0.03)
    # a thinner chip always lets more through
    assert best_wavelength(100.0)[1] > best_wavelength(500.0)[1] > best_wavelength(750.0)[1]


def test_depth_washout_limits():
    assert depth_washout(1e6, 1050.0) == pytest.approx(1.0, abs=1e-6)    # coarse detail untouched
    assert depth_washout(1e4, 1050.0, depth_um=0.0) == pytest.approx(1.0)
    assert depth_washout(200.0, 1050.0) == 0.0             # finer than the wavelength in silicon
    # coarse-pattern limit: turns = wavelength * depth / (2 n period^2)
    period, depth, n = 2000.0, 3.0, silicon_nk(1050.0)[0]
    turns = 1050.0 * depth * 1000.0 / (2 * n * period**2)
    assert depth_washout(period, 1050.0, depth) == pytest.approx(np.sinc(turns), abs=2e-3)
    # deeper absorption smears more
    assert depth_washout(700.0, 1050.0, 4.0) < depth_washout(700.0, 1050.0, 2.0)


def test_finest_period_with_light_from_behind():
    close = backlight_period(1.3e4, 300.0, edge_sigma_nm=127.4)
    far = backlight_period(1.3e4, 10000.0, edge_sigma_nm=127.4)
    assert close == pytest.approx(561, rel=0.02)
    # Directed light keeps detail down to about the wavelength at any gap.
    assert far == pytest.approx(1050, rel=0.02)
    # At a large gap that is far better than the matt, visible-light best case.
    assert far < 0.25 * recoverable_period(1.3e4, 10000.0, edge_sigma_nm=127.4)
    # without the washout the result is finer, so the factor is doing something
    assert backlight_period(1.3e4, 300.0, depth_um=0.0, edge_sigma_nm=127.4) < close
