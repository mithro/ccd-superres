"""Approach files and the comparison runner."""

import json
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
    flat = cp.score(scene, frames, np.full(scene.surface.size, 0.5), None, frames.positions_nm)
    assert flat["finest_period_nm"] is None              # not even the coarsest group
    assert flat["wrong_material_percent"] == pytest.approx(50.0)   # all one material: half marks, not 100 - share
    assert flat["rms_error"] > 0.3
    # a blur that removes only the finer groups: the coarser ones still count
    n = scene.surface.size
    blurred = np.fft.ifft(np.fft.fft(scene.surface) * (np.abs(np.fft.fftfreq(n, scene.dx_nm)) < 1 / 700)).real
    assert cp.score(scene, frames, blurred, None, frames.positions_nm)["finest_period_nm"] == 800.0
    # bars drawn half a period out of place are not counted, however strong
    period, start, stop = scene.groups[0]
    inverted = scene.surface.copy()
    inverted[start:stop] = 1.2 - inverted[start:stop]
    assert cp._contrast_share(inverted, scene.surface, scene.groups[0], scene.dx_nm) == pytest.approx(-1.0, abs=0.01)
    # twice the true swing is over the ceiling
    # a coarse group that fails hides the finer ones behind it
    doubled = scene.surface.copy()
    doubled[start:stop] = 0.6 + 2 * (doubled[start:stop] - 0.6)
    assert cp._contrast_share(doubled, scene.surface, scene.groups[0], scene.dx_nm) == pytest.approx(2.0, abs=0.01)
    assert cp.score(scene, frames, doubled, None, frames.positions_nm)["finest_period_nm"] is None
    # the score is taken after sliding the picture into place, by at most three pixels
    slid = np.roll(scene.surface, 37)
    assert cp.score(scene, frames, slid, None, frames.positions_nm)["rms_error"] < 1e-6
    far = np.roll(ap.get_scene("isolated_lines").surface, 400)
    lines = ap.get_scene("isolated_lines")
    assert cp.score(lines, frames, far, None, frames.positions_nm)["rms_error"] > 0.1
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
    worst = cp.summarise(records, "rms_error", "worst")
    assert all(worst[k] >= error[k] for k in error) and any(worst[k] > error[k] for k in error)
    lost = cp.summarise(records, "position_error_nm", "lost")
    assert lost[("bars", "planned", "shaky")] == 2 and lost[("bars", "planned", "ideal")] == 0
    assert error[("bars", "fit", "ideal")] < error[("bars", "add", "ideal")]
    assert period[("bars", "fit", "ideal")] < period[("bars", "add", "ideal")]
    # trusting the plan is as good as knowing the positions when the motion is steady, and worse when it is not
    assert error[("bars", "planned", "ideal")] == pytest.approx(error[("bars", "fit", "ideal")], rel=1e-6)
    assert error[("bars", "planned", "shaky")] > 1.2 * error[("bars", "fit", "shaky")]
    again = cp.run(comparison)
    for a, b in zip(records, again):
        assert {k: v for k, v in a.items() if k != "seconds"} == {k: v for k, v in b.items() if k != "seconds"}
    # spread over processes: the same records in the same order
    pooled = cp.run(comparison, workers=2)
    for a, b in zip(records, pooled):
        assert (a["approach"], a["condition"], a["seed"]) == (b["approach"], b["condition"], b["seed"])
        assert a["rms_error"] == pytest.approx(b["rms_error"], rel=1e-9)
    cp.write_results(comparison, records, tmp_path)
    text = (tmp_path / "tables.md").read_text()
    assert "| `fit` |" in text and "Table R1." in text and "2 runs per cell" in text
    assert text == cp.tables_markdown(comparison, again)          # no timings in it
    for name in ("results.json", "timings.md", "error-grid.svg", "error-grid.png", "reconstructions.svg"):
        assert (tmp_path / name).stat().st_size > 0
    saved = json.loads((tmp_path / "results.json").read_text())
    assert len(saved["records"]) == 12 and set(saved["approach_files"]) == {"add", "fit", "planned"}
    assert saved["records"][0]["rms_error"] == float(f"{records[0]['rms_error']:.6g}")
    assert "seconds" not in saved["records"][0]


def test_summaries_and_table_text_on_made_up_records():
    def record(seed, **values):
        return {"approach": "a", "scene": "bars", "condition": "c", "seed": seed, "has_bars": True, **values}

    records = [record(0, rms_error=0.1, finest_period_nm=800.0, position_error_nm=5.0),
               record(1, rms_error=0.5, finest_period_nm=None, position_error_nm=500.0),
               record(2, rms_error=0.2, finest_period_nm=None, position_error_nm=7.0)]
    key = ("bars", "a", "c")
    assert cp.summarise(records, "rms_error")[key] == 0.2
    assert cp.summarise(records, "rms_error", "worst")[key] == 0.5
    assert cp.summarise(records, "position_error_nm", "lost")[key] == 1
    assert np.isinf(cp.summarise(records, "finest_period_nm")[key])        # most runs showed no bars
    refused = [{"approach": "b", "scene": "bars", "condition": "c", "seed": 0, "refused": "b: no good"}]
    assert cp.summarise(refused, "rms_error")[("bars", "b", "c")] == "refused"
    a = ap.parse_approach(PLAIN.replace('"plain"', '"a"').replace('"known"', '"unknown"'))
    b = ap.parse_approach(PLAIN.replace('"plain"', '"b"'))
    for r in records:
        r.update(readings=10, warnings=[], wrong_material_percent=1.0)
    text = cp.tables_markdown(cp.Comparison("m", "", (a, b), ("bars",), (ap.Condition("c"),), (0, 1, 2)),
                              records + refused)
    assert "| `a` | none |" in text and "| `b` | not run |" in text and "| `b` | `bars` | no good |" in text


def test_options_and_seed_reach_the_run():
    scene = ap.get_scene("bars")
    usual = ap.parse_approach(PLAIN)
    light = ap.parse_approach(PLAIN + "smoothness = 1e-4\n")
    ideal = ap.Condition("ideal")
    first = cp.run_one(usual, "bars", ideal, 0)
    assert cp.run_one(light, "bars", ideal, 0)["rms_error"] != pytest.approx(first["rms_error"], rel=1e-3)
    assert cp.run_one(usual, "bars", ideal, 1)["rms_error"] != pytest.approx(first["rms_error"], rel=1e-6)
    assert not np.allclose(ap.simulate(usual, scene, ideal, 0).readings, ap.simulate(usual, scene, ideal, 1).readings)


def test_one_command_run_with_changed_settings(tmp_path, capsys):
    from ccdsr import run

    path = ROOT / "approaches" / "least-squares.toml"
    usual = ap.load_approach(path)
    changed = ap.load_approach(path, ["optics.gap_nm=1000", "noise.full_e=100", "positions=unknown",
                                      "reconstruction.smoothness=1e-3", "scan.code=[1, 0, 1]"])
    assert (changed.optics, changed.noise, changed.positions) == ({"gap_nm": 1000}, {"full_e": 100}, "unknown")
    assert changed.options == {"smoothness": 1e-3} and changed.scan["code"] == (1, 0, 1)
    assert usual.optics == {} and usual.positions == "known"
    with pytest.raises(ap.InvalidApproach, match="unknown optics setting"):
        ap.load_approach(path, ["optics.gap=3"])
    with pytest.raises(ap.InvalidApproach, match="section.setting=value"):
        ap.load_approach(path, ["optics.gap_nm"])
    scene, frames, estimate, scores = run.run(usual)
    wide = run.run(ap.load_approach(path, ["optics.gap_nm=1000"]))[3]
    assert frames.optics.gap_nm == 300 and wide["rms_error"] > scores["rms_error"] + 0.03
    same = cp.run_one(usual, "bars", ap.Condition("as set"), 0)                 # same as the runner
    assert all(same[k] == v for k, v in scores.items())
    out = tmp_path / "try.png"
    run.main([str(path), "--set", "optics.gap_nm=1000", "--out", str(out)])
    text = capsys.readouterr().out
    assert "gap 1000 nm" in text and f"{wide['rms_error']:.3f}" in text and out.stat().st_size > 10000
    run.main(["--list"])
    listed = capsys.readouterr().out
    assert "optics.gap_nm=300.0" in listed and "reconstruction.method=two_materials (needs: materials)" in listed
    with pytest.raises(SystemExit, match="cannot run"):
        run.main([str(path), "--scene", "nowhere"])
