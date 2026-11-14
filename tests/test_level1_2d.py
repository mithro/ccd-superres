"""Level 1 in two dimensions: agreement with one dimension, the formulas, and the effect of tilt."""

import numpy as np
import pytest

from ccdsr import level1 as l1
from ccdsr import level1_2d as l2

DX = 70.0
TILT = float(np.rad2deg(np.arcsin(1 / 16)))


def test_matches_one_dimension_for_a_scene_uniform_across_the_scan():
    line, _ = l1.bar_groups([2800, 1400], DX, cycles=3, margin_nm=2100)
    picture = np.tile(line, (32, 1))
    optics = l2.Optics(gap_nm=300)
    f2 = l2.simulate(picture, DX, optics, l2.Scan2D(n_rows=2, n_cols=8, n_frames=40),
                     l2.Noise(photon=False, read_e=0), seed=0)
    f1 = l1.simulate(line, DX, optics, l1.Scan1D(n_pixels=8, n_frames=40),
                     l1.Noise1D(photon=False, read_e=0), seed=0)
    for row in range(2):
        assert np.allclose(f2.readings[:, row, :], f1.readings, rtol=1e-9, atol=1e-6)


@pytest.mark.parametrize("angle", [0.0, 30.0, 90.0])
def test_blur_applies_the_transfer_in_every_direction(angle):
    """The Fourier machinery applies transfer2d correctly. The formula itself is checked below."""
    optics = l2.Optics(gap_nm=300)
    scan = l2.Scan2D(tilt_deg=TILT, exposure_fraction=0.5)
    picture, (fx, fy) = l2.sinusoid2d(2500.0, angle, DX, (240, 240))
    blurred = l2.blur(picture, DX, optics, scan)
    expected = abs(l2.transfer2d(np.array([fx]), np.array([fy]), optics, scan)[0])
    spectrum = np.abs(np.fft.fft2(blurred - blurred.mean())) / blurred.size
    assert 2 * spectrum.max() / blurred.mean() == pytest.approx(expected, rel=1e-6)


@pytest.mark.parametrize("tilt", [0.0, 20.0, -35.0])
def test_pixel_footprint_follows_the_tilted_pixel_grid(tilt):
    """The pixel blur equals a direct average over a square laid along the sensor's own rows.

    The square is built from the positions of neighbouring pixels given by
    sample_positions, so this ties the blur to the sampling geometry without
    using the transfer formula.
    """
    pitch = 1120.0
    optics = l2.Optics(gap_nm=1e-3, pitch_nm=pitch)
    scan = l2.Scan2D(n_rows=2, n_cols=2, n_frames=1, tilt_deg=tilt)
    corner = l2.sample_positions(scan, pitch)[0]
    along_row, along_col = corner[0, 1] - corner[0, 0], corner[1, 0] - corner[0, 0]
    assert np.hypot(*along_row) == pytest.approx(pitch)
    assert abs(np.dot(along_row, along_col)) < 1e-6
    u = (np.arange(200) + 0.5) / 200 - 0.5
    uu, vv = np.meshgrid(u, u)
    dx_ = uu[..., None] * along_row + vv[..., None] * along_col      # points of one pixel's area
    for wave_angle in (0.0, 50.0, 90.0):
        a = np.deg2rad(wave_angle)
        fx, fy = np.cos(a) / 1700.0, np.sin(a) / 1700.0
        direct = np.mean(np.cos(2 * np.pi * (fx * dx_[..., 0] + fy * dx_[..., 1])))
        formula = l2.transfer2d(np.array([fx]), np.array([fy]), optics, scan)[0].real
        assert formula == pytest.approx(direct, abs=2e-4)
    if tilt:
        a = np.deg2rad(50.0)
        fx, fy = np.cos(a) / 1700.0, np.sin(a) / 1700.0
        direct = np.mean(np.cos(2 * np.pi * (fx * dx_[..., 0] + fy * dx_[..., 1])))
        mirrored = l2.transfer2d(np.array([fx]), np.array([fy]), optics, l2.Scan2D(tilt_deg=-tilt))[0].real
        assert abs(mirrored - direct) > 0.004         # the opposite tilt would not pass


def test_light_scales_with_pixel_area_and_jitter_moves_frames_both_ways():
    picture = np.full((64, 64), 0.5)
    quiet = l2.Noise(photon=False, read_e=0)
    scan = l2.Scan2D(n_rows=4, n_cols=4, n_frames=3)
    full = l2.simulate(picture, DX, l2.Optics(), scan, quiet)
    half = l2.simulate(picture, DX, l2.Optics(aperture_nm=560.0), scan, quiet)
    assert half.readings.mean() == pytest.approx(full.readings.mean() / 4)
    still = l2.sample_positions(l2.Scan2D(n_frames=400), 1120.0)
    shaken = l2.sample_positions(l2.Scan2D(n_frames=400, jitter_px=0.1), 1120.0, np.random.default_rng(0))
    move = (shaken - still)[:, 0, 0, :]
    assert np.std(move[:, 0]) == pytest.approx(112.0, rel=0.15)
    assert np.std(move[:, 1]) == pytest.approx(112.0, rel=0.15)
    assert np.allclose(shaken - still, (shaken - still)[:, :1, :1, :])


def test_sampling_matrix_reads_a_plane_exactly():
    ny, nx = 40, 50
    y, x = np.meshgrid(np.arange(ny), np.arange(nx), indexing="ij")
    plane = 0.3 * x + 0.7 * y
    pos = np.array([[10.25, 5.5], [20.75, 30.1], [3.0, 7.0]]) * DX
    got = l2.sampling_matrix(pos, (ny, nx), DX) @ plane.ravel()
    assert np.allclose(got, 0.3 * pos[:, 0] / DX + 0.7 * pos[:, 1] / DX)


def test_tilt_spreads_the_pixels_across_the_scan():
    assert l2.cross_scan_offsets(l2.Scan2D(tilt_deg=0.0), 1120.0).size == 1
    offsets = l2.cross_scan_offsets(l2.Scan2D(tilt_deg=TILT), 1120.0)
    assert offsets.size >= 16
    assert np.diff(offsets).max() < 1 / 15


def test_rolling_readout_delays_each_row():
    still = l2.sample_positions(l2.Scan2D(n_frames=1), 1120.0)
    rolling = l2.sample_positions(l2.Scan2D(n_frames=1, row_delay_px=0.01), 1120.0)
    shift = rolling[0, :, 0, 0] - still[0, :, 0, 0]
    assert np.allclose(shift, np.arange(16) * 0.01 * 1120.0)
    assert np.allclose(rolling[..., 1], still[..., 1])


def _contrasts(tilt, noise=None, seed=1, **solver):
    shape = (256, 512)
    picture, groups = l2.line_groups([1960, 1400, 980, 700], DX, shape)
    frames = l2.simulate(picture, DX, l2.Optics(gap_nm=300),
                         l2.Scan2D(n_frames=300, tilt_deg=tilt), noise, seed=seed)
    est, _ = l2.least_squares(frames, **solver)
    return picture, groups, est


def test_tilt_recovers_detail_across_the_scan_that_no_tilt_loses():
    picture, groups, flat = _contrasts(0.0)
    _, _, tilted = _contrasts(TILT)
    along = [g for g in groups if g[1] == "along" and g[0] == 1400.0][0]
    across = [g for g in groups if g[1] == "across" and g[0] == 1400.0][0]
    true = l2.group_contrast(picture, across, DX)
    assert l2.group_contrast(flat, along, DX) > 0.8 * true
    assert l2.group_contrast(flat, across, DX) < 0.2 * true
    assert l2.group_contrast(tilted, across, DX) > 0.8 * true
    assert l2.group_contrast(tilted, across, DX) == pytest.approx(
        l2.group_contrast(tilted, along, DX), rel=0.1)


def test_noise_free_reconstruction_recovers_the_picture_with_tilt():
    picture, groups, est = _contrasts(TILT, l2.Noise(photon=False, read_e=0), smoothness=1e-5,
                                     tol=1e-9, iterations=500)
    for g in groups:
        assert l2.group_contrast(est, g, DX) == pytest.approx(l2.group_contrast(picture, g, DX), rel=0.05)


def test_wrong_positions_degrade_the_two_dimensional_fit():
    picture, groups = l2.line_groups([1960, 1400, 980, 700], DX, (256, 512))
    frames = l2.simulate(picture, DX, l2.Optics(gap_nm=300),
                         l2.Scan2D(n_frames=300, tilt_deg=TILT, jitter_px=0.3), seed=2)
    good, _ = l2.least_squares(frames)
    same, _ = l2.least_squares(frames, positions_nm=frames.positions_nm)
    assumed = l2.sample_positions(l2.Scan2D(n_frames=300, tilt_deg=TILT), 1120.0)
    bad, _ = l2.least_squares(frames, positions_nm=assumed)
    assert np.allclose(good, same)
    g = groups[1]
    assert l2.group_contrast(bad, g, DX) < 0.6 * l2.group_contrast(good, g, DX)
