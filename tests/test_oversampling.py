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


def test_distinct_positions_are_counted_exactly():
    scene = ap.get_scene("random_layout")                       # 1,260 cells of 20 nm: 22.5 pixel widths
    still = l1.simulate(scene.surface, scene.dx_nm, l1.Optics1D(), l1.Scan1D(n_pixels=22, n_frames=7, shift_px=0.0))
    assert ov.distinct_positions_per_pixel(still) == pytest.approx(22 * 1120.0 / 25200.0)      # one place per pixel
    # a sensor longer than the surface laps it: 45 pixels fall on 45 different places, 23 more on places already used
    lapped = l1.simulate(scene.surface, scene.dx_nm, l1.Optics1D(), l1.Scan1D(n_pixels=68, n_frames=1, shift_px=0.0))
    assert ov.distinct_positions_per_pixel(lapped) == pytest.approx(45 * 1120.0 / 25200.0)
    # steps of a quarter pixel give four places per pixel, on a coarser count as well
    quarter = l1.simulate(scene.surface, scene.dx_nm, l1.Optics1D(), l1.Scan1D(n_pixels=22, n_frames=4, shift_px=0.25))
    assert ov.distinct_positions_per_pixel(quarter) == pytest.approx(4 * 22 * 1120.0 / 25200.0)
    assert ov.distinct_positions_per_pixel(quarter, cell_nm=280.0) == pytest.approx(4 * 22 * 1120.0 / 25200.0)


def test_a_sensor_held_still_adds_no_new_positions_and_does_not_lap_the_surface():
    scene = ap.get_scene("fine_layout")                         # 23.2 pixel widths long
    base, noise = l1.Scan1D(jitter_px=0.3, wander_px=1.0), l1.Noise1D()
    surface_px = scene.surface.size * scene.dx_nm / 1120.0
    count = lambda scan: ov.distinct_positions_per_pixel(l1.simulate(scene.surface, scene.dx_nm, l1.Optics1D(), scan))
    few, _ = ov.scan_for("repeat", 4, base, noise, surface_px)
    many, _ = ov.scan_for("repeat", 64, base, noise, surface_px)
    spread, _ = ov.scan_for("more-time", 64, dataclasses.replace(base, jitter_px=0.0, wander_px=0.0), noise, surface_px)
    assert few.n_pixels == many.n_pixels == 23 and many.shift_px == 0.0
    assert many.jitter_px == 0.0 and many.wander_px == 0.0      # a sensor that shakes is not held still
    assert many.n_frames == round(64 * 64 / 23)                 # about the same number of readings as 64 full frames
    assert count(few) == count(many) == pytest.approx(23 * 1120.0 / 26000.0)
    assert count(spread) > 10 * count(many)
    whole, _ = ov.scan_for("repeat", 64, base, noise)           # without the surface length the sensor is kept whole
    assert whole.n_pixels == 64 and whole.n_frames == 64


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


def test_recovered_period_uses_all_runs_and_its_threshold():
    scene = ap.get_scene("fine_layout")
    truth, dx = scene.surface, scene.dx_nm
    bands = ov.period_bands(truth.size, dx)
    freq = np.fft.rfftfreq(truth.size, dx)
    assert all(np.count_nonzero((freq >= lo) & (freq < hi)) >= ov.MIN_WAVES for lo, hi in bands)
    assert bands[0][0] == pytest.approx(1 / 8000.0) and all(a[1] == b[0] for a, b in zip(bands, bands[1:]))
    # the answer is the short end of the last good band, not its long end
    spectrum = np.fft.rfft(truth)
    lo, hi = bands[5]
    spectrum[freq >= hi] = 0
    kept = np.fft.irfft(spectrum, truth.size)
    assert ov.recovered_period([kept], truth, dx) == pytest.approx(1 / hi)
    # one good run among noise of the same strength: agreement falls below a half with enough bad runs
    rng = np.random.default_rng(1)
    noise = [rng.standard_normal(truth.size) * truth.std() for _ in range(8)]
    assert ov.recovered_period([truth], truth, dx) < 100.0
    assert math.isinf(ov.recovered_period([truth] + noise, truth, dx))
    # a copy at 0.6 of full agreement passes, at 0.4 it does not: the mark is a half
    def mixed(share):
        other = np.fft.irfft(np.fft.rfft(truth - truth.mean()) * 1j, truth.size)      # same strength, out of step
        return share * (truth - truth.mean()) + math.sqrt(1 - share ** 2) * other
    assert ov.recovered_period([mixed(0.6)], truth, dx) < 100.0
    assert math.isinf(ov.recovered_period([mixed(0.4)], truth, dx))


def test_level0_estimate_by_hand():
    # A pixel with no gap blur, no soft edges and a narrow opening passes every period in range at nearly
    # full strength, so the rule reduces to 0.5 c F / sigma * sqrt(n L / 2p) = 1 with one known answer.
    optics = l1.Optics1D(gap_nm=0.0, aperture_nm=1.0, edge_sigma_nm=0.0)
    noise = l1.Noise1D(full_e=1120.0 * 100, read_e=3.0)          # 100 electrons through the 1 nm opening
    light, sigma = 100.0, math.sqrt(100.0 * 0.6 + 9.0)
    n = 2.0
    expected = 2 * 1120.0 / n * (sigma / (0.5 * 0.8 * light)) ** 2
    assert ov.noise_limit_period(optics, l1.Scan1D(), noise, n) == pytest.approx(expected, rel=2e-3)
    silent = dataclasses.replace(noise, read_e=0.0)
    assert ov.noise_limit_period(optics, l1.Scan1D(), silent, n) == pytest.approx(expected * 60 / 69, rel=2e-3)


def test_level0_estimate_stops_at_the_first_failure_going_from_coarse():
    optics, scan, noise = l1.Optics1D(gap_nm=300.0, edge_sigma_nm=127.4), l1.Scan1D(), l1.Noise1D()
    periods = [ov.noise_limit_period(optics, scan, noise, n) for n in (3, 30, 300, 3000, 30000)]
    assert all(b <= a for a, b in zip(periods, periods[1:]))    # never coarser with more readings
    assert periods[0] > 1000.0 and periods[-1] < 560.0          # past the blind periods at 1,120 nm and 560 nm


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
    by = {(r["way"], r["level"]): r for r in records}
    assert by[("more-time", 64)]["readings_per_point"] == pytest.approx(by[("repeat", 64)]["readings_per_point"], rel=0.01)
    assert by[("more-time", 64)]["rms_error"] < 0.9 * by[("repeat", 64)]["rms_error"]
    assert by[("more-time", 64)]["recovered_period_nm"] < by[("repeat", 64)]["recovered_period_nm"]
    assert by[("more-time", 64)]["rms_error"] < by[("more-time", 1)]["rms_error"]
    assert by[("more-time", 64)]["scan_time"] == 1.0 and by[("more-time", 1)]["scan_time"] == pytest.approx(1 / 64)
    held = by[("repeat", 64)]
    assert held["pixels"] == 22 and held["frames"] == round(64 * 64 / 22)
    assert held["scan_time"] == pytest.approx(held["frames"] / 64)
    assert held["light_per_point_e"] == pytest.approx(2500.0 * held["readings_per_point"])
    assert held["distinct_positions_per_pixel"] == pytest.approx(22 * 1120.0 / 25200.0)


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
    assert max(ov.SMOOTHNESS_LADDER) >= 100.0 and min(ov.SMOOTHNESS_LADDER) <= 1e-8
    assert not set(ov.TUNING_SEEDS) & set(range(100))           # never the runs that are scored


def test_tuning_keeps_the_strength_with_the_lowest_median_error(monkeypatch):
    scene = ap.get_scene("random_layout")
    seen = []

    def fake_score(scene, frames, estimate, positions, believed):
        return {"rms_error": float(estimate[0])}

    def fake_reconstruct(approach, scene, frames):
        seen.append(approach.options["smoothness"])
        # error is lowest at 1e-3, except in one run where 1e-6 looks best by a wide margin
        lucky = len(seen) % 3 == 0 and approach.options["smoothness"] == 1e-6
        return np.array([0.0 if lucky else abs(math.log10(approach.options["smoothness"]) + 3) + 1]), None

    monkeypatch.setattr(ov.cp, "score", fake_score)
    monkeypatch.setattr(ov.ap, "reconstruct", fake_reconstruct)
    _, strength = ov.tuned(_approach(), scene, l1.Optics1D(), l1.Scan1D(n_frames=2), l1.Noise1D())
    assert strength == pytest.approx(1e-3)
    assert sorted(set(seen)) == sorted(ov.SMOOTHNESS_LADDER) and len(seen) == 3 * len(ov.SMOOTHNESS_LADDER)


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
