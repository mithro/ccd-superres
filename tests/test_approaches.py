"""Approach files and the comparison runner."""

from pathlib import Path

import numpy as np
import pytest

from ccdsr import approaches as ap
from ccdsr import compare as cp
from ccdsr import level1 as l1

ROOT = Path(__file__).resolve().parent.parent

PLAIN = """
name = "plain"
description = "least squares"
positions = "known"
[reconstruction]
method = "least_squares"
"""


def test_every_committed_approach_file_loads_and_names_are_unique():
    files = sorted((ROOT / "approaches").glob("*.toml"))
    assert len(files) >= 10
    loaded = [ap.load_approach(f) for f in files]
    assert len({a.name for a in loaded}) == len(loaded)
    for approach, path in zip(loaded, files):
        assert approach.name == path.stem           # the file is named after the approach
        assert approach.description and approach.hardware


def test_the_committed_comparison_lists_every_approach_file():
    comparison = cp.load_comparison(ROOT / "comparisons" / "level1-first.toml")
    on_disk = {f.stem for f in (ROOT / "approaches").glob("*.toml")}
    assert {a.name for a in comparison.approaches} == on_disk


@pytest.mark.parametrize("text, reason", [
    (PLAIN.replace('"least_squares"', '"magic"'), "unknown reconstruction"),
    (PLAIN.replace('"known"', '"sometimes"'), "positions must be"),
    (PLAIN + "\n[optics]\ngap = 3\n", "unknown optics setting"),
    (PLAIN.replace("[reconstruction]", "colour = 1\n[reconstruction]"), "unknown entries"),
    (PLAIN.replace('"least_squares"', '"two_materials"'), "needs the materials"),
    (PLAIN.replace("[reconstruction]", 'level = "3"\n[reconstruction]'), "only level 1"),
    (PLAIN + "sharpness = 3\n", "has no option"),
])
def test_bad_approach_files_are_refused_with_the_reason(text, reason):
    with pytest.raises(ap.InvalidApproach, match=reason):
        ap.parse_approach(text)


def test_invalid_combinations_are_refused_and_recorded_not_run():
    materials = ap.parse_approach(PLAIN.replace('"least_squares"', '"two_materials"')
                                  + "\n[knowledge]\nmaterials = true\n")
    record = cp.run_one(materials, "soft_ramps", ap.Condition("ideal"), 0)
    assert "two materials" in record["refused"] and "rms_error" not in record
    # a condition may not silently override what the approach itself chose
    gap = ap.parse_approach(PLAIN + "\n[optics]\ngap_nm = 100.0\n")
    record = cp.run_one(gap, "bars", ap.Condition("wide", optics={"gap_nm": 1000.0}), 0)
    assert "both set optics" in record["refused"]


def test_settings_from_the_approach_and_the_condition_both_reach_the_simulation():
    approach = ap.parse_approach(PLAIN + "\n[optics]\naperture_nm = 280.0\n[scan]\nshift_px = 2.37\n")
    condition = ap.Condition("dim wide", optics={"gap_nm": 1000.0}, noise={"full_e": 100.0},
                             scan={"jitter_px": 0.3})
    frames = ap.simulate(approach, ap.get_scene("bars"), condition, 0)
    assert (frames.optics.aperture_nm, frames.optics.gap_nm) == (280.0, 1000.0)
    assert (frames.scan.shift_px, frames.scan.jitter_px, frames.noise.full_e) == (2.37, 0.3, 100.0)


def test_a_reconstruction_never_receives_the_truth():
    scene = ap.get_scene("bars")
    condition = ap.Condition("shaky", scan={"jitter_px": 0.3})
    seen = {}

    @ap.reconstruction("spy")
    def spy(frames, levels):
        seen["frames"], seen["levels"] = frames, levels
        return np.full(frames.n_grid, 0.5), None

    try:
        for positions in ("known", "unknown"):
            approach = ap.parse_approach(PLAIN.replace('"least_squares"', '"spy"').replace('"known"',
                                                                                         f'"{positions}"'))
            frames = ap.simulate(approach, scene, condition, 0)
            ap.reconstruct(approach, scene, frames)
            assert seen["frames"].truth == {} and frames.truth      # stripped from the copy only
            assert seen["levels"] is None                           # materials not asked for, not given
            same = np.allclose(seen["frames"].positions_nm, frames.positions_nm)
            assert same == (positions == "known")
            if positions == "unknown":
                assert np.allclose(seen["frames"].positions_nm, l1.nominal_positions(frames))
    finally:
        del ap.RECONSTRUCTIONS["spy"]


def test_alignment_removes_a_shift_and_is_limited():
    scene = ap.get_scene("isolated_lines")
    n = scene.surface.size
    smooth = np.fft.ifft(np.fft.fft(scene.surface) * np.exp(-(np.fft.fftfreq(n) * 40) ** 2)).real

    def moved(cells):
        return np.fft.ifft(np.fft.fft(smooth) * np.exp(-2j * np.pi * np.fft.fftfreq(n) * cells)).real

    back, shift = cp.align_to_truth(moved(7.3), smooth, 168)
    assert shift == pytest.approx(-7.3, abs=0.05)
    assert np.sqrt(np.mean((back - smooth) ** 2)) < 2e-3
    # a displacement beyond the allowed range is not undone
    _, shift = cp.align_to_truth(moved(400.0), smooth, 168)
    assert abs(shift) <= 168.5


def test_scores_of_a_perfect_and_of_a_flat_reconstruction():
    scene = ap.get_scene("bars")
    approach = ap.parse_approach(PLAIN)
    frames = ap.simulate(approach, scene, ap.Condition("ideal"), 0)
    perfect = cp.score(scene, frames, scene.surface, None, frames.positions_nm)
    assert perfect["rms_error"] < 1e-9 and perfect["wrong_material_percent"] == 0
    assert perfect["finest_period_nm"] == 320.0 and perfect["position_error_nm"] == 0
    assert np.allclose(perfect["contrast_share"], 1.0)
    flat = cp.score(scene, frames, np.full(scene.surface.size, 0.6), None, frames.positions_nm)
    assert flat["finest_period_nm"] == 8000.0            # nothing resolved: twice the coarsest period
    assert flat["rms_error"] > 0.3
    # a blur that removes only the finer groups: the coarser ones still count
    n = scene.surface.size
    blurred = np.fft.ifft(np.fft.fft(scene.surface) * (np.abs(np.fft.fftfreq(n, scene.dx_nm)) < 1 / 700)).real
    assert cp.score(scene, frames, blurred, None, frames.positions_nm)["finest_period_nm"] == 800.0
    # position error is that of the positions the reconstruction used
    off = frames.positions_nm + np.linspace(-50, 50, frames.positions_nm.shape[0])[:, None]
    used = cp.score(scene, frames, scene.surface, off, frames.positions_nm)["position_error_nm"]
    assert used == pytest.approx(np.std(np.linspace(-50, 50, off.shape[0])))


def test_a_small_comparison_runs_ranks_as_expected_and_repeats(tmp_path):
    def approach(name, method, positions="known"):
        return ap.parse_approach(f'name = "{name}"\ndescription = "d"\npositions = "{positions}"\n'
                                 f'[reconstruction]\nmethod = "{method}"\n')

    comparison = cp.Comparison(
        "tiny", "test",
        (approach("add", "shift_and_add"), approach("fit", "least_squares"),
         approach("planned", "least_squares", "unknown")),
        ("bars",), (ap.Condition("ideal"), ap.Condition("shaky", scan={"jitter_px": 0.3})), (0, 1))
    records = cp.run(comparison)
    assert len(records) == 3 * 1 * 2 * 2
    error = cp.summarise(records, "rms_error")
    period = cp.summarise(records, "finest_period_nm")
    assert error[("bars", "fit", "ideal")] < error[("bars", "add", "ideal")]
    assert period[("bars", "fit", "ideal")] < period[("bars", "add", "ideal")]
    # trusting the plan is as good as knowing the positions when the motion is steady, and worse when it is not
    assert error[("bars", "planned", "ideal")] == pytest.approx(error[("bars", "fit", "ideal")], rel=1e-6)
    assert error[("bars", "planned", "shaky")] > 1.2 * error[("bars", "fit", "shaky")]
    again = cp.run(comparison)
    for a, b in zip(records, again):
        assert {k: v for k, v in a.items() if k != "seconds"} == {k: v for k, v in b.items() if k != "seconds"}
    cp.write_results(comparison, records, tmp_path)
    text = (tmp_path / "tables.md").read_text()
    assert "| `fit` |" in text and "Table R1." in text and "median of 2 seeds" in text
    for name in ("results.json", "error-grid.svg", "error-grid.png", "reconstructions.svg"):
        assert (tmp_path / name).stat().st_size > 0
