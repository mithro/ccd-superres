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
    predicted = l1.predicted_contrast_noise(None, period, optics, scan, noise)
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
