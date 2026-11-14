"""Reconstruction by elimination: material, layout and smooth-path constraints."""

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


def test_misfit_of_the_true_surface_is_about_the_number_of_readings(scene):
    surface, _ = scene
    values = [c.misfit(_frames(surface, seed), surface) for seed in range(6)]
    n = 64 * 160
    assert np.mean(values) == pytest.approx(n, rel=0.03)
    wrong = surface.copy()
    wrong[1000:1012] = 1.2 - wrong[1000:1012]
    frames = _frames(surface, 0)
    assert c.misfit(frames, wrong) > c.misfit(frames, surface) + 100


def test_material_constraint_recovers_bars_the_plain_fit_loses(scene):
    surface, groups = scene
    frames = _frames(surface, 1)
    plain, _ = l1.least_squares(frames)
    bounded, _ = c.material_reconstruction(frames, None, (0.0, 1.0))
    fitted, snapped = c.material_reconstruction(frames, LEVELS)
    fine = groups[4]
    assert l1.bar_contrast(plain, fine, DX) < 0.15
    assert l1.bar_contrast(bounded, fine, DX) > 0.3
    assert l1.bar_contrast(fitted, fine, DX) > 0.6
    assert set(np.unique(snapped)) <= set(LEVELS)
    assert bounded.min() > -0.05 and bounded.max() < 1.05
    for g in groups[:4]:
        assert l1.bar_contrast(fitted, g, DX) == pytest.approx(l1.bar_contrast(surface, g, DX), rel=0.05)


def test_elimination_leaves_only_the_true_layout_in_good_light(scene):
    surface, groups = scene
    _, start, stop = groups[4]
    layouts = c.allowed_layouts(12, 1)
    truth = np.where(surface[start:stop:12] > 0.6, 1.0, 0.0)
    true_index = int(np.where((layouts == truth).all(axis=1))[0][0])
    frames = _frames(surface, 2)
    _, base = c.material_reconstruction(frames, LEVELS)
    misfits, survivors = c.eliminate_candidates(frames, base, start, 12, layouts, LEVELS)
    assert survivors.sum() == 1 and survivors[true_index]
    assert np.sort(misfits)[1] - misfits.min() > 500


def test_elimination_is_honest_in_poor_light(scene):
    """With little light many candidates survive, and the true one is among them."""
    surface, groups = scene
    _, start, stop = groups[4]
    layouts = c.allowed_layouts(12, 1)
    truth = np.where(surface[start:stop:12] > 0.6, 1.0, 0.0)
    true_index = int(np.where((layouts == truth).all(axis=1))[0][0])
    for seed in range(4):
        frames = _frames(surface, seed, full_e=25.0)
        _, survivors = c.eliminate_candidates(frames, surface, start, 12, layouts, LEVELS)
        assert survivors[true_index]
        assert 20 < survivors.sum() < 1000


def test_candidate_misfits_match_the_direct_calculation(scene):
    surface, groups = scene
    _, start, _ = groups[4]
    frames = _frames(surface, 3)
    layouts = c.allowed_layouts(12, 1)[[0, 77, 1500, 4095]]
    misfits, _ = c.eliminate_candidates(frames, surface, start, 12, layouts, LEVELS)
    for row, value in zip(layouts, misfits):
        candidate = surface.copy()
        candidate[start:start + 144] = np.repeat(np.where(row > 0.5, 1.0, 0.2), 12)
        assert value == pytest.approx(c.misfit(frames, candidate), rel=1e-9)


def test_smooth_wander_is_smooth_and_of_the_stated_size():
    path = l1.smooth_wander(4000, 20.0, np.random.default_rng(0))
    assert np.sqrt(np.mean(path**2)) == pytest.approx(1.0)
    assert np.std(np.diff(path)) < 0.1
    frames = _frames(np.full(2000, 0.5), wander_px=1.0, wander_frames=20.0)
    error = (frames.positions_nm - l1.nominal_positions(frames))[:, 0]
    assert np.std(error) == pytest.approx(1120.0, rel=0.01)


def test_smooth_path_constraint_finds_large_wandering_errors(scene):
    """Seeds on which the unconstrained estimate fails are solved, to below the per-frame limit."""
    surface, _ = scene
    coarse = dict(smoothness=(1000.0, 1e-2), rounds=40, max_step_px=3.0)
    for seed in (0, 2):
        frames = _frames(surface, seed, wander_px=1.0, wander_frames=20.0)
        free, _ = l1.estimate_positions(frames, **coarse)
        tied, _ = l1.estimate_positions(frames, path_stiffness=10.0, **coarse)
        assert l1.position_error(frames, free) > 300
        assert l1.position_error(frames, tied) < l1.position_precision_limit(frames)


def test_everything_together_without_knowing_positions(scene):
    surface, groups = scene
    _, start, stop = groups[4]
    frames = _frames(surface, 1, wander_px=1.0, wander_frames=20.0)
    _, _, positions = c.solve_surface_and_positions(frames, LEVELS)
    assert l1.position_error(frames, positions) < 6
    aligned = l1.align_positions(frames, positions)
    fitted, snapped = c.material_reconstruction(frames, LEVELS, positions_nm=aligned)
    for g in groups[:4]:
        assert l1.bar_contrast(fitted, g, DX) == pytest.approx(l1.bar_contrast(surface, g, DX), rel=0.05)
    layouts = c.allowed_layouts(12, 1)
    truth = np.where(surface[start:stop:12] > 0.6, 1.0, 0.0)
    _, survivors = c.eliminate_candidates(frames, snapped, start, 12, layouts, LEVELS, positions_nm=aligned)
    assert survivors.sum() == 1
    assert (layouts[survivors][0] == truth).all()
