"""Reconstruction by elimination: material, layout and smooth-path constraints."""

import dataclasses

import numpy as np
import pytest

from ccdsr import constrained as c
from ccdsr import level1 as l1

DX = 20.0
LEVELS = (0.2, 1.0)


@pytest.fixture(scope="module")
def scene():
    surface, groups = l1.bar_groups([4000, 2000, 1200, 800, 480], DX)
    return surface, groups


def _frames(surface, seed=0, full_e=2500.0, **scan):
    return l1.simulate(surface, DX, l1.Optics1D(gap_nm=300),
                       l1.Scan1D(n_pixels=64, n_frames=160, shift_px=0.37, **scan),
                       l1.Noise1D(full_e=full_e), seed=seed)


def test_layout_lists_follow_the_width_rule():
    assert c.allowed_layouts(4, 1).shape == (16, 4)
    two = c.allowed_layouts(6, 2)
    as_text = {"".join(str(int(v)) for v in row) for row in two}
    assert "001100" in as_text and "110011" in as_text and "100111" in as_text
    assert "010011" not in as_text and "001011" not in as_text
    # brute force: no interior run shorter than 2
    for row in as_text:
        runs = [len(r) for r in row.replace("01", "0 1").replace("10", "1 0").split()]
        assert all(r >= 2 for r in runs[1:-1])
    assert len(c.allowed_layouts(12, 1)) == 4096 > len(c.allowed_layouts(12, 2)) > len(c.allowed_layouts(12, 3))


def _true_index(surface, groups, layouts):
    _, start, stop = groups[4]
    truth = np.where(surface[start:stop:12] > 0.6, 1.0, 0.0)
    return start, int(np.where((layouts == truth).all(axis=1))[0][0])


def _displacement(pattern, true_layout, shifts):
    """Grid steps by which a surviving pattern is the true layout displaced, or None if it is not."""
    low = min(shifts)
    for shift in shifts:
        row = np.zeros(pattern.size, dtype=np.int8)
        row[shift - low:shift - low + 144] = np.repeat(true_layout, 12).astype(np.int8)
        if (row == pattern).all():
            return shift
    return None


def test_the_same_surface_described_two_ways_counts_once():
    layouts = np.array([[0.0, 1.0, 0.0, 1.0], [1.0, 0.0, 1.0, 0.0], [1.0, 1.0, 0.0, 0.0]])
    survivors = np.zeros((2, 3), dtype=bool)
    survivors[0, 0] = survivors[1, 1] = True      # 0101 at shift 0 and 1010 at shift 3: the same bars
    result = c.Elimination(np.zeros((2, 3)), survivors, True, 1.0, 10, 20.0, (0, 3), (0, 0))
    assert len(result.surviving_patterns(layouts, 3)) == 1
    survivors[1, 0] = True                        # 0101 at shift 3: same bars, another place
    assert len(result.surviving_patterns(layouts, 3)) == 2
    assert len(result.surviving_shapes(layouts, 3)) == 1
    # the first raised cell: 0101 at shift 0 starts at step 3, at shift 3 at step 6
    assert result.surviving_edges_nm(layouts, 3, 20.0) == (60.0, 120.0)
    survivors[0, 2] = True
    assert len(result.surviving_shapes(layouts, 3)) == 2


def test_chi_squared_of_the_true_surface_is_about_the_number_of_readings(scene):
    surface, _ = scene
    values = [c.chi_squared(_frames(surface, seed), surface) for seed in range(6)]
    n = 64 * 160
    assert np.mean(values) == pytest.approx(n, rel=0.03)
    wrong = surface.copy()
    wrong[1000:1012] = 1.2 - wrong[1000:1012]
    frames = _frames(surface, 0)
    assert c.chi_squared(frames, wrong) > c.chi_squared(frames, surface) + 100
    assert c.misfit(frames, wrong) > c.misfit(frames, surface) + 100


def test_misfit_does_not_favour_brighter_candidates_in_poor_light(scene):
    """Without the log-variance term the best fit has, on average, a bright cell too many."""
    surface, groups = scene
    layouts = c.allowed_layouts(12, 1)
    start, true_index = _true_index(surface, groups, layouts)
    extra = []
    for seed in range(12):
        frames = _frames(surface, 100 + seed, full_e=10.0)
        result = c.eliminate_candidates(frames, surface, start, 12, layouts, LEVELS)
        extra.append(layouts[result.best[1]].sum() - layouts[true_index].sum())
        assert result.survivors[0, true_index]
    assert abs(np.mean(extra)) < 0.5


def test_material_constraint_recovers_bars_at_equal_smoothing(scene):
    surface, groups = scene
    fine = groups[4]
    plain, bounded, fitted = [], [], []
    for seed in range(4):
        frames = _frames(surface, seed)
        plain.append(l1.bar_contrast(l1.least_squares(frames, smoothness=1e-3)[0], fine, DX))
        b, _ = c.material_reconstruction(frames, None, (0.0, 1.0))
        x, snapped = c.material_reconstruction(frames, LEVELS)
        bounded.append(l1.bar_contrast(b, fine, DX))
        fitted.append(l1.bar_contrast(x, fine, DX))
        assert set(np.unique(snapped)) <= set(LEVELS)
        assert b.min() > -0.05 and b.max() < 1.05
        for g in groups[:4]:
            assert l1.bar_contrast(x, g, DX) == pytest.approx(l1.bar_contrast(surface, g, DX), rel=0.05)
    assert np.mean(fitted) > np.mean(plain) + 0.15           # materials help
    assert abs(np.mean(bounded) - np.mean(plain)) < 0.1      # the 0 to 1 limits alone do not


def test_material_reconstruction_uses_the_positions_it_is_given(scene):
    surface, groups = scene
    frames = _frames(surface, 1, jitter_px=0.3)
    good, _ = c.material_reconstruction(frames, LEVELS)
    bad, _ = c.material_reconstruction(frames, LEVELS, positions_nm=l1.nominal_positions(frames))
    rms = lambda x: np.sqrt(np.mean((x - surface) ** 2))
    assert rms(bad) > 1.3 * rms(good)


def test_elimination_leaves_only_the_true_layout_in_good_light(scene):
    surface, groups = scene
    layouts = c.allowed_layouts(12, 1)
    start, true_index = _true_index(surface, groups, layouts)
    frames = _frames(surface, 2)
    _, base = c.material_reconstruction(frames, LEVELS)
    result = c.eliminate_candidates(frames, base, start, 12, layouts, LEVELS)
    assert result.fits and result.n_survivors == 1 and result.survivors[0, true_index]
    assert result.margin == pytest.approx(2 * np.log(4096 / 0.01))
    assert np.sort(result.misfits[0])[1] - result.misfits.min() > 500
    assert result.local_chi2_per_reading == pytest.approx(1.0, abs=0.25)


def test_elimination_is_honest_in_poor_light(scene):
    """With little light many candidates survive, and the true one is among them."""
    surface, groups = scene
    layouts = c.allowed_layouts(12, 1)
    start, true_index = _true_index(surface, groups, layouts)
    for seed in range(4):
        frames = _frames(surface, seed, full_e=25.0)
        result = c.eliminate_candidates(frames, surface, start, 12, layouts, LEVELS)
        assert result.fits and result.survivors[0, true_index]
        assert 10 < result.n_survivors < 1000


def test_elimination_says_so_when_nothing_fits(scene):
    """Wrong materials, or frames in the wrong place: no layout is returned, not a wrong one."""
    surface, groups = scene
    layouts = c.allowed_layouts(12, 1)
    start, _ = _true_index(surface, groups, layouts)
    frames = _frames(surface, 0)
    wrong_levels = (0.25, 0.95)
    _, base = c.material_reconstruction(frames, wrong_levels)
    result = c.eliminate_candidates(frames, base, start, 12, layouts, wrong_levels)
    assert not result.fits and result.n_survivors == 0
    assert result.local_chi2_per_reading > 3
    lost = l1.nominal_positions(frames) + 700.0 * np.sin(np.arange(160) / 9.0)[:, None]
    _, base = c.material_reconstruction(frames, LEVELS, positions_nm=lost)
    result = c.eliminate_candidates(frames, base, start, 12, layouts, LEVELS, positions_nm=lost)
    assert not result.fits and result.n_survivors == 0


def test_an_unknown_overall_offset_is_found_by_searching_shifts(scene):
    surface, groups = scene
    layouts = c.allowed_layouts(12, 1)
    start, true_index = _true_index(surface, groups, layouts)
    frames = _frames(surface, 3)
    off = frames.positions_nm + 100.0            # the whole scan believed 100 nm from where it was
    _, base = c.material_reconstruction(frames, LEVELS, positions_nm=off)
    shifts = tuple(range(-6, 7))
    result = c.eliminate_candidates(frames, base, start, 12, layouts, LEVELS, positions_nm=off, shifts=shifts)
    assert result.fits
    assert len(result.surviving_shapes(layouts, 12)) == 1
    found = [_displacement(p, layouts[true_index], shifts) for p in result.surviving_patterns(layouts, 12)]
    assert None not in found
    assert all(abs(f * DX - 100.0) <= DX for f in found)
    # the positions argument matters: with the true positions the best shift is zero
    _, base0 = c.material_reconstruction(frames, LEVELS)
    again = c.eliminate_candidates(frames, base0, start, 12, layouts, LEVELS, shifts=shifts)
    assert shifts[again.best[0]] == 0
    # the position read out is a place on the surface, whichever label described it
    first_raised = int(np.nonzero(layouts[true_index])[0][0]) * 12 * DX
    low, high = result.surviving_edges_nm(layouts, 12, DX)
    assert abs(low - first_raised - 100.0) <= DX and abs(high - first_raised - 100.0) <= DX
    # the absolute test looks at the readings around the region where the best candidate puts it
    best = np.array(base, dtype=float)
    cover = np.arange(start + min(shifts), start + max(shifts) + 144)
    best[cover] = LEVELS[0]
    at = start + shifts[result.best[0]]
    best[at:at + 144] = np.where(np.repeat(layouts[result.best[1]], 12) > 0.5, LEVELS[1], LEVELS[0])
    predicted = c._predict(frames, best, off)
    length = surface.size * DX
    centre = (at + 72) * DX
    distance = np.abs((off.ravel() - centre + length / 2) % length - length / 2)
    near = distance <= 72 * DX + 1.5 * frames.optics.pitch_nm
    direct = np.sum((frames.readings.ravel()[near] - predicted[near]) ** 2 / c._variance(frames, predicted[near]))
    assert result.local_readings == near.sum()
    assert result.local_chi2_per_reading == pytest.approx(direct / near.sum(), rel=1e-9)
    assert shifts[result.best[0]] != 0


def test_the_fit_threshold_is_five_standard_deviations(scene):
    """A light level assumed 2 % too high is caught; 1 % is within the noise of the test."""
    surface, groups = scene
    layouts = c.allowed_layouts(12, 1)
    start, true_index = _true_index(surface, groups, layouts)
    frames = _frames(surface, 0)

    def assumed(scale):
        noise = dataclasses.replace(frames.noise, full_e=frames.noise.full_e * scale)
        return c.eliminate_candidates(dataclasses.replace(frames, noise=noise), surface, start, 12, layouts, LEVELS)

    slightly, more = assumed(1.01), assumed(1.02)
    limit = 1 + 5 * np.sqrt(2 / more.local_readings)
    assert slightly.fits and slightly.local_chi2_per_reading < limit
    assert not more.fits and limit < more.local_chi2_per_reading < 1.6
    assert more.n_survivors == 0


def test_noise_model_switch_is_used(scene):
    surface, _ = scene
    frames = _frames(surface, 0)
    no_photon = dataclasses.replace(frames, noise=dataclasses.replace(frames.noise, photon=False))
    predicted = np.array([100.0, 400.0])
    assert np.allclose(c._variance(frames, predicted), predicted + frames.noise.read_e ** 2)
    assert np.allclose(c._variance(no_photon, predicted), frames.noise.read_e ** 2)


def test_candidate_misfits_match_the_direct_calculation(scene):
    surface, groups = scene
    _, start, _ = groups[4]
    frames = _frames(surface, 3)
    layouts = c.allowed_layouts(12, 1)[[0, 77, 1500, 4095]]
    result = c.eliminate_candidates(frames, surface, start, 12, layouts, LEVELS, shifts=(0, 5))
    for j, shift in enumerate((0, 5)):
        for row, value in zip(layouts, result.misfits[j]):
            candidate = surface.copy()
            candidate[start:start + 149] = 0.2
            candidate[start + shift:start + shift + 144] = np.repeat(np.where(row > 0.5, 1.0, 0.2), 12)
            assert value == pytest.approx(c.misfit(frames, candidate), rel=1e-9)


def test_smooth_wander_is_smooth_and_of_the_stated_size():
    path = l1.smooth_wander(4000, 20.0, np.random.default_rng(0))
    assert np.sqrt(np.mean(path**2)) == pytest.approx(1.0)
    assert np.std(np.diff(path)) < 0.1
    quick = l1.smooth_wander(4000, 3.0, np.random.default_rng(0))
    assert np.std(np.diff(quick)) > 3 * np.std(np.diff(path))
    frames = _frames(np.full(2000, 0.5), wander_px=1.0, wander_frames=20.0)
    error = (frames.positions_nm - l1.nominal_positions(frames))[:, 0]
    assert np.std(error) == pytest.approx(1120.0, rel=0.01)


def test_smooth_path_trusts_frames_by_their_weight():
    values = np.zeros(40)
    values[20] = 10.0                               # one frame disagrees with a flat path
    trusted = np.ones(40)
    doubted = np.ones(40)
    doubted[20] = 1e-3
    assert l1._smooth_path(values, doubted, 10.0)[20] < 0.1 * l1._smooth_path(values, trusted, 10.0)[20]
    line = np.arange(40.0)
    assert np.allclose(l1._smooth_path(line, trusted, 10.0), line)


def test_smooth_path_constraint_improves_accuracy(scene):
    """Over a set of scans the smooth-path rule solves at least as many and places frames better."""
    surface, _ = scene
    coarse = dict(smoothness=(1000.0, 1e-2), rounds=40, max_step_px=3.0)
    free, tied, limits = [], [], []
    for seed in range(6):
        frames = _frames(surface, seed, wander_px=1.0, wander_frames=20.0)
        free.append(l1.position_error(frames, l1.estimate_positions(frames, **coarse)[0]))
        tied.append(l1.position_error(frames, l1.estimate_positions(frames, path_stiffness=10.0, **coarse)[0]))
        limits.append(l1.position_precision_limit(frames))
    free, tied = np.array(free), np.array(tied)
    assert (tied < 20).sum() >= (free < 20).sum()
    assert np.median(tied[tied < 20]) < 0.7 * np.median(free[free < 20])
    assert np.median(tied[tied < 20]) < np.mean(limits)


def test_smooth_path_is_the_wrong_rule_for_frame_to_frame_jitter(scene):
    """Stated limit: independent errors on each frame are smoothed away wrongly."""
    surface, _ = scene
    frames = _frames(surface, 3, jitter_px=0.2)
    free, _ = l1.estimate_positions(frames)
    tied, _ = l1.estimate_positions(frames, path_stiffness=10.0)
    assert l1.position_error(frames, free) < 10
    assert l1.position_error(frames, tied) > 100


def test_everything_together_without_knowing_positions(scene):
    surface, groups = scene
    layouts = c.allowed_layouts(12, 1)
    start, true_index = _true_index(surface, groups, layouts)
    frames = _frames(surface, 1, wander_px=1.0, wander_frames=20.0)
    believed = l1.nominal_positions(frames) + 80.0           # overall position not known either
    fitted, snapped, positions = c.solve_surface_and_positions(frames, LEVELS, start_positions_nm=believed)
    assert l1.position_error(frames, positions) < 6
    assert np.mean((positions - frames.positions_nm)[:, 0]) == pytest.approx(80.0, abs=1.0)
    # the returned surface belongs to the estimated positions, displaced by the same 80 nm
    shifted = np.roll(surface, 4)
    assert np.mean(snapped != shifted) < 0.08
    assert np.mean(snapped != shifted) < 0.5 * np.mean(snapped != np.roll(surface, -8))
    shifts = tuple(range(-6, 7))
    result = c.eliminate_candidates(frames, snapped, start, 12, layouts, LEVELS, positions_nm=positions,
                                    shifts=shifts)
    assert result.fits and len(result.surviving_shapes(layouts, 12)) == 1
    found = [_displacement(p, layouts[true_index], shifts) for p in result.surviving_patterns(layouts, 12)]
    assert None not in found
    assert all(abs(f * DX - 80.0) <= DX for f in found)
