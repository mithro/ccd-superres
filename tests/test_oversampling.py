"""Oversampling: the result against the number of readings of each point."""

import dataclasses
import math

import numpy as np
import pytest

from ccdsr import approaches as ap
from ccdsr import gui
from ccdsr import level1 as l1
from ccdsr import oversampling as ov


def _approach(method="least_squares", **options):
    return ap.Approach(name=method, description="", hardware=(), positions="known", method=method,
                       options=options, knows_materials="materials" in ap.RECONSTRUCTIONS[method].needs)


def test_readings_per_point_counts_pixel_widths_of_surface():
    scene = ap.get_scene("random_layout")
    frames = l1.simulate(scene.surface, scene.dx_nm, l1.Optics1D(), l1.Scan1D(n_pixels=64, n_frames=10))
    expected = 640 * 1120.0 / (scene.surface.size * scene.dx_nm)
    assert ov.readings_per_point(frames) == pytest.approx(expected)
    narrow = l1.simulate(scene.surface, scene.dx_nm, l1.Optics1D(aperture_nm=300.0), l1.Scan1D(n_pixels=64, n_frames=10))
    assert ov.readings_per_point(narrow) == pytest.approx(expected)       # the opening does not change the count


def test_a_sensor_held_still_adds_no_new_positions():
    scene = ap.get_scene("random_layout")
    base, noise = l1.Scan1D(), l1.Noise1D()
    few, _ = ov.scan_for("repeat", 4, base, noise)
    many, _ = ov.scan_for("repeat", 64, base, noise)
    spread, _ = ov.scan_for("more-time", 64, base, noise)
    count = lambda scan: ov.distinct_positions_per_pixel(l1.simulate(scene.surface, scene.dx_nm, l1.Optics1D(), scan))
    assert count(few) == count(many)
    assert count(spread) > 10 * count(many)


def test_same_time_keeps_the_total_light():
    base, noise = l1.Scan1D(), l1.Noise1D(full_e=2500.0)
    for n in (1, 16, 512):
        scan, changed = ov.scan_for("same-time", n, base, noise)
        assert scan.n_frames == n
        assert changed.full_e * n == pytest.approx(2500.0 * ov.REFERENCE_FRAMES)
    scan, changed = ov.scan_for("more-time", 512, base, noise)
    assert changed.full_e == 2500.0 and scan.shift_px == base.shift_px
    with pytest.raises(ValueError):
        ov.scan_for("sideways", 4, base, noise)


def test_recovered_period_of_a_copy_a_blurred_copy_and_noise():
    scene = ap.get_scene("fine_layout")
    truth = scene.surface
    assert ov.recovered_period([truth], truth, scene.dx_nm) < 100.0
    # a copy with everything finer than a 1 µm period removed is recovered down to about 1 µm
    spectrum = np.fft.rfft(truth)
    spectrum[np.fft.rfftfreq(truth.size, scene.dx_nm) > 1 / 1000.0] = 0
    blurred = np.fft.irfft(spectrum, truth.size)
    assert 850.0 < ov.recovered_period([blurred], truth, scene.dx_nm) < 1200.0
    rng = np.random.default_rng(0)
    noise = [rng.standard_normal(truth.size) for _ in range(5)]
    assert math.isinf(ov.recovered_period(noise, truth, scene.dx_nm))
    # a copy with bright and dark swapped does not count
    assert math.isinf(ov.recovered_period([1.2 - truth], truth, scene.dx_nm))


def test_level0_estimate_gets_finer_with_readings_and_coarser_with_gap():
    scan, noise = l1.Scan1D(), l1.Noise1D()
    near = l1.Optics1D(gap_nm=300.0, edge_sigma_nm=127.4)
    far = dataclasses.replace(near, gap_nm=3000.0)
    a, b = (ov.noise_limit_period(near, scan, noise, n) for n in (10, 10000))
    assert b < a
    assert ov.noise_limit_period(far, scan, noise, 100) > 3 * ov.noise_limit_period(near, scan, noise, 100)
    dim = dataclasses.replace(noise, full_e=25.0)
    assert ov.noise_limit_period(near, scan, dim, 100) > ov.noise_limit_period(near, scan, noise, 100)


def test_more_readings_at_new_places_beat_the_same_places_again():
    records = ov.sweep(_approach(), "random_layout", ("more-time", "repeat"), (1, 64), seeds=(0, 1, 2),
                       tuning_seeds=(1000,))
    by = {(r["way"], r["frames"]): r for r in records}
    assert by[("more-time", 1)]["rms_error"] == pytest.approx(by[("repeat", 1)]["rms_error"])
    assert by[("more-time", 64)]["readings_per_point"] == pytest.approx(by[("repeat", 64)]["readings_per_point"])
    assert by[("more-time", 64)]["rms_error"] < 0.9 * by[("repeat", 64)]["rms_error"]
    assert by[("more-time", 64)]["recovered_period_nm"] < by[("repeat", 64)]["recovered_period_nm"]
    assert by[("more-time", 64)]["rms_error"] < by[("more-time", 1)]["rms_error"]
    assert by[("more-time", 64)]["scan_time"] == 1.0 and by[("more-time", 1)]["scan_time"] == pytest.approx(1 / 64)


def test_tuning_lowers_the_smoothing_as_readings_rise_and_never_does_worse():
    scene = ap.get_scene("random_layout")
    optics, noise = l1.Optics1D(), l1.Noise1D()
    chosen = [ov.tuned(_approach(), scene, optics, l1.Scan1D(n_frames=n), noise, seeds=(1000,))[1] for n in (1, 512)]
    assert chosen[1] < chosen[0]
    fixed = ov.sweep(_approach(smoothness=1e-2), "random_layout", ("more-time",), (512,), seeds=(0, 1, 2), tune=False)
    best = ov.sweep(_approach(smoothness=1e-2), "random_layout", ("more-time",), (512,), seeds=(0, 1, 2))
    assert fixed[0]["smoothness"] is None
    assert best[0]["rms_error"] <= fixed[0]["rms_error"] + 1e-9
    untouched, strength = ov.tuned(_approach("shift_and_add"), scene, optics, l1.Scan1D(), noise)
    assert strength is None and untouched.method == "shift_and_add"


def test_tables_and_command_line(tmp_path, capsys):
    ov.main(["approaches/least-squares.toml", "--frames", "1,8", "--ways", "more-time", "--seeds", "2",
             "--out", str(tmp_path)])
    text = (tmp_path / "tables.md").read_text()
    assert "Readings per point" in text and "Table O1" in text and text.count("\n| ") >= 2
    assert (tmp_path / "oversampling.svg").exists() and (tmp_path / "results.json").exists()
    with pytest.raises(SystemExit):
        ov.main(["approaches/least-squares.toml", "--ways", "sideways", "--out", str(tmp_path)])


def test_explorer_answers_the_oversampling_request():
    request = gui.default_request()
    request["scene"] = "random_layout"
    request["methods"] = [{"method": "least_squares", "options": {"smoothness": 0.01}},
                          {"method": "least_squares_positions", "options": {}}]
    out = gui._no_nan(gui.respond_oversampling(request))
    assert out["ok"] and out["skipped"] == ["Least squares, solving positions"]
    assert [c["way"] for c in out["curves"]] == list(ov.WAYS)
    curve = out["curves"][0]
    assert curve["frames"] == list(gui.SWEEP_FRAMES)
    assert curve["rms_error"][-1] < curve["rms_error"][0]
    request["methods"] = [{"method": "least_squares_positions", "options": {}}]
    assert not gui.respond_oversampling(request)["ok"]
    request["methods"] = []
    assert not gui.respond_oversampling(request)["ok"]
