"""Level 1 (one dimension): forward model, reconstruction, and checks against level 0."""

import numpy as np
import pytest

from ccdsr import level1 as l1
from ccdsr.resolution import box_envelope, gap_transfer, motion_transfer

DX = 20.0


def test_blur_matches_analytic_transfer():
    """A blurred sinusoid keeps exactly the contrast the level 0 formulas predict."""
    optics = l1.Optics1D(gap_nm=300)
    scan = l1.Scan1D()
    n = 4000
    for period in (800.0, 1600.0, 4000.0, 16000.0):
        blurred = l1.blur(l1.sinusoid(period, DX, n), DX, optics, scan)
        measured = (blurred.max() - blurred.min()) / 2 / 0.5
        expected = float(gap_transfer(period, 300.0)) * abs(np.sinc(1120.0 / period))
        assert measured == pytest.approx(expected, rel=1e-6, abs=1e-9)


def test_level0_envelopes_bound_the_exact_transfer():
    """Level 0 uses upper envelopes of the box transfers; level 1 uses the exact ones."""
    optics = l1.Optics1D(gap_nm=100)
    periods = np.geomspace(150, 50000, 200)
    smear = 5000.0
    exact = np.abs(l1.transfer(1 / periods, optics, smear))
    envelope = (gap_transfer(periods, 100.0) * box_envelope(periods, 1120.0)
                * motion_transfer(periods, smear))
    assert np.all(exact <= envelope * (1 + 1e-9))


def test_coded_exposure_transfer_matches_expected_level():
    """A random on-off code passes about sqrt((1 - duty) / open slots), as level 0 assumes."""
    rng = np.random.default_rng(0)
    code = tuple(int(v) for v in rng.random(1024) < 0.5)
    smear = 73_500.0
    periods = np.geomspace(300, 3000, 400)
    t = np.abs(l1.motion_kernel_transfer(1 / periods, smear, code))
    rms = np.sqrt(np.mean(t**2))
    expected = float(np.sqrt(np.mean(motion_transfer(periods, smear, 1024) ** 2)))
    assert rms == pytest.approx(expected, rel=0.15)


def test_sampling_matrix_reads_a_ramp_exactly():
    pos = np.array([[10.0, 35.0, 1234.5]])
    s = l1.sampling_matrix(pos, 200, DX)
    ramp = np.arange(200) * DX
    assert np.allclose(s @ ramp, pos.ravel())


def test_noise_free_reconstruction_recovers_what_the_blur_passes():
    """Without noise, least squares restores bar contrast wherever the transfer is not tiny."""
    surface, groups = l1.bar_groups([4000, 2000, 800], DX)
    scan = l1.Scan1D(n_pixels=32, n_frames=160, shift_px=0.37)
    frames = l1.simulate(surface, DX, l1.Optics1D(gap_nm=150), scan,
                         l1.Noise1D(photon=False, read_e=0.0), seed=0)
    est, iterations = l1.least_squares(frames, smoothness=1e-9, iterations=500)
    assert iterations < 500
    for g in groups:
        assert l1.bar_contrast(est, g, DX) == pytest.approx(l1.bar_contrast(surface, g, DX), rel=0.03)


def test_methods_rank_as_expected_with_noise():
    """Deblurring beats plain averaging, and least squares is at least as good as Wiener."""
    surface, groups = l1.bar_groups([4000, 2000, 800], DX)
    scan = l1.Scan1D(n_pixels=64, n_frames=160, shift_px=0.37)
    frames = l1.simulate(surface, DX, l1.Optics1D(gap_nm=300), scan, l1.Noise1D(), seed=1)
    truth = [l1.bar_contrast(surface, g, DX) for g in groups]
    plain, _ = l1.shift_and_add(frames)
    wien = l1.wiener(frames)
    lsq, _ = l1.least_squares(frames)

    def err(est):
        return sum(abs(l1.bar_contrast(est, g, DX) - t) for g, t in zip(groups, truth))

    assert err(lsq) < err(plain)
    assert err(wien) < err(plain)
    assert err(lsq) <= err(wien) * 1.1


def test_measured_noise_matches_the_analytic_prediction():
    """The scatter of a fitted contrast over noise seeds equals sigma * sqrt(2 / M) / (T * mean).

    This is the one-dimensional form of the level 0 criterion: signal times
    transfer against noise averaged over the samples.
    """
    optics = l1.Optics1D(gap_nm=300)
    scan = l1.Scan1D(n_pixels=64, n_frames=100, shift_px=0.37)
    noise = l1.Noise1D()
    period, n = 1600.0, 4000
    surface = l1.sinusoid(period, DX, n, contrast=0.5)
    errors = [l1.sinusoid_amplitude(l1.simulate(surface, DX, optics, scan, noise, seed=s), period)[0] - 0.5
              for s in range(300)]
    predicted = l1.predicted_contrast_noise(period, optics, scan, noise, contrast=0.5)
    assert abs(np.mean(errors)) < 3 * predicted / np.sqrt(300) + 1e-4
    assert np.std(errors) == pytest.approx(predicted, rel=0.12)


def test_gain_variation_and_jitter_are_recorded_for_scoring_only():
    surface, _ = l1.bar_groups([2000], DX)
    scan = l1.Scan1D(n_pixels=16, n_frames=40, jitter_px=0.5)
    frames = l1.simulate(surface, DX, l1.Optics1D(), scan, l1.Noise1D(gain_sigma=0.02), seed=3)
    assert frames.readings.shape == (40, 16)
    assert frames.truth["gains"].std() > 0
    steps = np.diff(frames.positions_nm[:, 0])
    assert steps.std() > 0.3 * 1120


def _jittered(jitter, seed=0):
    surface, groups = l1.bar_groups([4000, 2000, 1200, 800, 500], DX)
    scan = l1.Scan1D(n_pixels=64, n_frames=160, shift_px=0.37, jitter_px=jitter)
    return groups, l1.simulate(surface, DX, l1.Optics1D(gap_nm=300), scan, l1.Noise1D(), seed=seed)


def test_position_errors_blur_the_picture_and_estimation_restores_it():
    groups, frames = _jittered(0.2)
    nominal = l1.nominal_positions(frames)
    estimated, history = l1.estimate_positions(frames, nominal)
    contrast = lambda pos: l1.bar_contrast(
        l1.least_squares(frames, positions_nm=l1.align_positions(frames, pos))[0], groups[3], DX)
    assert l1.position_error(frames, nominal) == pytest.approx(0.2 * 1120, rel=0.2)
    assert contrast(nominal) < 0.5 * contrast(frames.positions_nm)
    assert contrast(estimated) == pytest.approx(contrast(frames.positions_nm), rel=0.05)
    assert history.shape == (12, 160)


def test_estimated_positions_reach_the_theoretical_precision():
    _, frames = _jittered(0.2, seed=3)
    estimated, _ = l1.estimate_positions(frames)
    limit = l1.position_precision_limit(frames)
    assert 0.95 * limit < l1.position_error(frames, estimated) < 1.2 * limit


def test_a_wrong_speed_is_corrected():
    _, frames = _jittered(0.0)
    wrong = l1.nominal_positions(frames, shift_px=0.37 * 1.01)
    estimated, _ = l1.estimate_positions(frames, wrong)
    assert l1.position_error(frames, wrong) > 150
    assert l1.position_error(frames, estimated) < 10


def test_a_wrong_speed_leaves_the_picture_sharp_once_aligned():
    """A 5% speed error shifts the estimate bodily; aligned, the contrast is that of true positions."""
    groups, frames = _jittered(0.0)
    wrong = l1.nominal_positions(frames, shift_px=0.37 * 1.05)
    estimated, _ = l1.estimate_positions(frames, wrong)
    contrast = lambda pos: l1.bar_contrast(l1.least_squares(frames, positions_nm=pos)[0], groups[3], DX)
    aligned = l1.align_positions(frames, estimated)
    assert abs(np.mean((aligned - frames.positions_nm)[:, 0])) < 1e-6
    assert contrast(aligned) == pytest.approx(contrast(frames.positions_nm), rel=0.03)


@pytest.mark.parametrize("noise", [l1.Noise1D(), l1.Noise1D(photon=False, read_e=40.0)])
def test_noise_prediction_holds_for_a_strong_pattern(noise):
    """At high blurred contrast the error of the fitted mean matters, differently for each noise type."""
    optics = l1.Optics1D(gap_nm=300)
    scan = l1.Scan1D(n_pixels=64, n_frames=100, shift_px=0.37)
    period, n = 8000.0, 4000
    surface = l1.sinusoid(period, DX, n, contrast=1.0)
    errors = [l1.sinusoid_amplitude(l1.simulate(surface, DX, optics, scan, noise, seed=s), period)[0] - 1.0
              for s in range(400)]
    predicted = l1.predicted_contrast_noise(period, optics, scan, noise, contrast=1.0)
    simple = l1.predicted_contrast_noise(period, optics, scan, noise)
    assert abs(predicted / simple - 1) > 0.15
    assert np.std(errors) == pytest.approx(predicted, rel=0.1)


def test_noise_added_to_readings_has_the_stated_size():
    surface = np.full(2000, 0.5)
    scan = l1.Scan1D(n_pixels=64, n_frames=200)
    optics = l1.Optics1D()
    read = l1.simulate(surface, DX, optics, scan, l1.Noise1D(photon=False, read_e=7.0), seed=0)
    assert np.std(read.readings - read.truth["clean"]) == pytest.approx(7.0, rel=0.03)
    both = l1.simulate(surface, DX, optics, scan, l1.Noise1D(full_e=2500, read_e=7.0), seed=0)
    assert np.var(both.readings - both.truth["clean"]) == pytest.approx(1250 + 49, rel=0.05)
    gains = l1.simulate(surface, DX, optics, l1.Scan1D(n_pixels=4000, n_frames=2),
                        l1.Noise1D(gain_sigma=0.03), seed=0).truth["gains"]
    assert np.std(gains) == pytest.approx(0.03, rel=0.05)


def test_aperture_sets_the_light_and_the_blind_spot():
    surface = np.full(2000, 0.5)
    scan = l1.Scan1D(n_pixels=8, n_frames=4)
    quiet = l1.Noise1D(photon=False, read_e=0)
    full = l1.simulate(surface, DX, l1.Optics1D(), scan, quiet)
    half = l1.simulate(surface, DX, l1.Optics1D(aperture_nm=560.0), scan, quiet)
    assert half.readings.mean() == pytest.approx(full.readings.mean() / 2)
    optics = l1.Optics1D(gap_nm=1e-3, aperture_nm=560.0)
    assert abs(l1.transfer(np.array([1 / 560.0]), optics)[0]) < 1e-12
    assert abs(l1.transfer(np.array([1 / 1120.0]), optics)[0]) == pytest.approx(2 / np.pi, rel=1e-6)


def _direct_blur(surface, kernel_offsets_cells, weights):
    """Blur by adding shifted copies: an independent route that uses no transfer function."""
    out = np.zeros_like(surface)
    for k, w in zip(kernel_offsets_cells, weights):
        out += w * np.roll(surface, k)
    return out / np.sum(weights)


def test_pixel_and_motion_blur_match_direct_averaging_in_space():
    """Box pixel and box smear, checked by averaging shifted copies of the surface."""
    surface, _ = l1.bar_groups([4000, 2000], DX)
    optics = l1.Optics1D(gap_nm=1e-3, pitch_nm=1120.0)          # no gap blur
    cells = int(1120 / DX)                                       # 56 grid cells per pixel
    offsets = np.arange(-cells // 2, cells // 2 + 1)
    trapezoid = np.ones(offsets.size)
    trapezoid[[0, -1]] = 0.5
    pixel_only = l1.blur(surface, DX, optics, l1.Scan1D())
    assert np.allclose(pixel_only, _direct_blur(surface, offsets, trapezoid), atol=2e-3)
    # smear of exactly one pixel (shift 2 pixels, light on half the time), after the pixel blur
    smeared = l1.blur(surface, DX, optics, l1.Scan1D(shift_px=2.0, exposure_fraction=0.5))
    assert np.allclose(smeared, _direct_blur(pixel_only, offsets, trapezoid), atol=2e-3)
    assert np.abs(smeared - pixel_only).max() > 0.05


def test_edge_softness_and_mirror_like_gap_follow_their_formulas():
    f = np.array([1 / 900.0, 1 / 400.0, 1 / 250.0])
    sharp = l1.transfer(f, l1.Optics1D(gap_nm=1e-3))
    soft = l1.transfer(f, l1.Optics1D(gap_nm=1e-3, edge_sigma_nm=60.0))
    assert np.allclose(soft / sharp, np.exp(-2 * np.pi**2 * (60.0 * f) ** 2))
    pixel = l1.transfer(f, l1.Optics1D(gap_nm=1e-3))
    mirror = l1.transfer(f, l1.Optics1D(gap_nm=200.0, gap_model="collimated", wavelength_nm=405.0))
    decay = np.exp(-2 * np.pi * 200.0 * np.sqrt(np.maximum(f**2 - 1 / 405.0**2, 0)))
    assert np.allclose(mirror / pixel, decay)
    assert decay[0] == 1.0 and decay[2] < 0.05


def test_exposure_code_puts_early_slots_behind_the_frame_position():
    """Convention: slot k of n sits at (k + 0.5) / n - 0.5 of the smear from the centre."""
    n = 2000
    spike = np.zeros(n)
    spike[1000] = 1.0
    optics = l1.Optics1D(gap_nm=1e-3, pitch_nm=DX)               # pixel of one cell: nearly no blur
    scan = l1.Scan1D(shift_px=80.0, exposure_fraction=1.0, code=(1, 0, 0, 0))   # smear 1600 nm
    out = l1.blur(spike, DX, optics, scan)
    centroid = np.sum(np.arange(n) * out) / np.sum(out) - 1000
    assert centroid * DX == pytest.approx(-0.375 * 1600.0, abs=DX)


def test_wiener_undoes_a_coded_smear():
    """With an uneven code the transfer is complex; the filter must use its conjugate."""
    surface, groups = l1.bar_groups([4000, 2000], DX)
    scan = l1.Scan1D(n_pixels=64, n_frames=160, shift_px=0.37, exposure_fraction=1.0, code=(1, 1, 0, 1, 0, 0, 0))
    frames = l1.simulate(surface, DX, l1.Optics1D(gap_nm=300), scan, l1.Noise1D(photon=False, read_e=0))
    est = l1.wiener(frames, noise_to_signal=1e-4)
    reference = l1.wiener(l1.simulate(surface, DX, l1.Optics1D(gap_nm=300),
                                      l1.Scan1D(n_pixels=64, n_frames=160, shift_px=0.37),
                                      l1.Noise1D(photon=False, read_e=0)), noise_to_signal=1e-4)
    assert np.sqrt(np.mean((est - reference) ** 2)) < 0.02


def test_solver_warns_when_it_does_not_converge():
    _, frames = _jittered(0.0)
    with pytest.warns(RuntimeWarning):
        l1.least_squares(frames, smoothness=1e-9, iterations=1)
