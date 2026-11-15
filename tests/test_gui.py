"""The interactive explorer: the functions behind the page, the server, and the page in a real browser."""

import json
import shutil
import subprocess
import threading
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import pytest

from ccdsr import approaches as ap
from ccdsr import compare as cp
from ccdsr import gui

ROOT = Path(__file__).parent.parent


def all_methods(request):
    request["methods"] = [{"method": m["name"], "options": m["options"]} for m in gui.describe()["methods"]]
    return request


def test_describe_offers_every_registered_part_and_every_approach_file():
    told = gui.describe()
    assert [m["name"] for m in told["methods"]] == list(ap.RECONSTRUCTIONS)
    assert [s["name"] for s in told["scenes"]] == list(ap.SCENES)
    assert {p["file"] for p in told["presets"]} == {p.name for p in (ROOT / "approaches").glob("*.toml")}
    offered = {c["key"] for c in told["controls"]}
    for part, cls in ap._PARTS.items():                       # every setting of the simulator has a control
        for f in __import__("dataclasses").fields(cls):
            assert f"{part}.{f.name}" in offered or f.name == "start_nm"
    json.dumps(told, allow_nan=False)


def test_answer_matches_the_command_line_and_the_comparison_runner():
    out = gui.respond(gui.default_request())
    assert out["ok"] and [r["method"] for r in out["results"]] == ["least_squares"]
    same = cp.run_one(ap.load_approach(ROOT / "approaches" / "least-squares.toml"), "bars", ap.Condition("as set"), 0)
    scores = out["results"][0]["scores"]
    assert all(scores[k] == pytest.approx(same[k]) for k in ("rms_error", "finest_period_nm", "position_error_nm"))
    assert len(out["scene"]["truth"]) == len(out["results"][0]["estimate"]) == len(out["seen"])
    assert len(out["readings"]["values"]) == out["readings"]["n_frames"] * out["readings"]["n_pixels"] == 12800
    json.dumps(gui._no_nan(out), allow_nan=False)


def test_every_preset_gives_what_its_approach_file_gives():
    for preset in gui.describe()["presets"]:
        out = gui.respond(preset["request"])
        assert out["ok"] and out["results"][0]["ok"], preset["name"]
        same = cp.run_one(ap.load_approach(ROOT / "approaches" / preset["file"]), "bars", ap.Condition("as set"), 0)
        assert out["results"][0]["scores"]["rms_error"] == pytest.approx(same["rms_error"]), preset["name"]


def test_settings_change_the_answer_in_the_expected_direction():
    def rms(**changes):
        request = gui.default_request()
        for key, value in changes.items():
            part, name = key.split("__")
            request[part][name] = value
        out = gui.respond(request)
        assert out["ok"], out
        return out["results"][0]["scores"]["rms_error"], out
    usual, out = rms()
    assert rms(optics__gap_nm=2000)[0] > usual + 0.03
    assert rms(noise__full_e=50)[0] > usual + 0.03
    assert rms(scan__exposure_fraction=1.0, scan__shift_px=2.0)[0] > usual
    wide, narrow = out["blur"], rms(optics__aperture_nm=300)[1]["blur"]
    at = int(np.argmin(np.abs(np.array(wide["periods_nm"]) - 800)))
    assert narrow["pixel"][at] > wide["pixel"][at] + 0.3 and narrow["gap"][at] == wide["gap"][at]
    product = np.array(wide["gap"]) * np.array(wide["pixel"]) * np.array(wide["motion"])
    assert np.allclose(product, wide["total"], atol=2e-4)
    assert rms(scan__n_frames=50)[1]["readings"]["n_frames"] == 50
    assert rms(noise__photon=False, noise__read_e=0)[1]["readings"]["values"] != out["readings"]["values"]


def test_methods_share_one_set_of_readings_and_fail_one_at_a_time():
    request = all_methods(gui.default_request())
    request["scene"] = "soft_ramps"                       # not a two-material surface
    out = gui.respond(request)
    by = {r["method"]: r for r in out["results"]}
    assert out["ok"] and by["least_squares"]["ok"] and by["wiener"]["ok"]
    assert not by["two_materials"]["ok"] and "two materials" in by["two_materials"]["error"].replace("\n", " ")
    request["scene"] = "bars"
    request["scan"]["wander_px"] = 1.0
    request["positions"] = "unknown"
    by = {r["method"]: r for r in gui.respond(request)["results"]}
    assert all(r["ok"] for r in by.values())
    assert by["two_materials_positions"]["scores"]["position_error_nm"] < 50 < by["least_squares"]["scores"]["position_error_nm"]
    assert "path_nm" in by["two_materials_positions"] and "path_nm" not in by["least_squares"]
    request["methods"][2]["options"]["nonsense"] = 1
    by = {r["method"]: r for r in gui.respond(request)["results"]}
    assert "no option" in by["least_squares"]["error"] and by["wiener"]["ok"]


def test_truth_is_not_given_to_a_method_that_is_told_only_the_plan():
    request = gui.default_request()
    request["scan"]["wander_px"] = 1.0
    known = gui.respond(request)["results"][0]["scores"]
    request["positions"] = "unknown"
    out = gui.respond(request)
    assert out["results"][0]["scores"]["rms_error"] > known["rms_error"] + 0.03
    assert max(abs(v) for v in out["path"]["believed_nm"]) == 0 < max(abs(v) for v in out["path"]["true_nm"])


def test_approach_text_reads_back_as_the_same_approach():
    request = all_methods(gui.default_request())
    request["optics"].update(gap_nm=500.0, aperture_nm=400.0)
    request["scan"].update(exposure_fraction=0.5, code=[1, 0, 1, 1], n_frames=120)
    request["noise"].update(photon=False, full_e=900.0)
    request["positions"] = "unknown"
    for result in gui.respond(request)["results"]:
        again = ap.parse_approach(result["file"])
        assert (again.method, again.positions) == (result["method"], "unknown")
        assert again.optics == {"gap_nm": 500.0, "aperture_nm": 400.0} and again.scan["code"] == (1, 0, 1, 1)
        assert again.noise == {"photon": False, "full_e": 900.0}
        rerun = cp.run_one(again, "bars", ap.Condition("as set"), 0)
        assert rerun["rms_error"] == pytest.approx(result["scores"]["rms_error"])


@pytest.mark.parametrize("change, message", [
    (lambda r: r["optics"].update(gap_nm=-5), "'Gap between sensor and surface' (optics.gap_nm) must be at least 0"),
    (lambda r: r["optics"].update(aperture_nm=2000), "cannot be wider"),
    (lambda r: r["scan"].update(n_frames=10**6), "at most"),
    (lambda r: r["scan"].update(n_pixels=gui.MAX_PIXELS + 1), "at most"),
    (lambda r: r["scan"].update(wander_frames=1e7), "at most"),
    (lambda r: r["scan"].update(code=[1] * 65), "at most 64"),
    (lambda r: r["scan"].update(n_frames=1e400), "must be a number"),
    (lambda r: r["noise"].update(full_e=1e30), "at most"),
    (lambda r: r.update(seed=10**20), "seed"),
    (lambda r: r.update(methods="all"), "list"),
    (lambda r: r["scan"].update(code=[0, 0]), "at least one 1"),
    (lambda r: r["scan"].update(shift_px=0), "must not be 0"),
    (lambda r: r.update(scene="nowhere"), "unknown scene"),
    (lambda r: r.update(seed=-1), "seed"),
    (lambda r: r.update(positions="guessed"), "known"),
    (lambda r: r["noise"].update(full_e="lots"), "must be a number"),
    (lambda r: r.update(optics=3), "group of settings"),
])
def test_unusable_requests_get_a_reason_and_not_a_crash(change, message):
    request = gui.default_request()
    change(request)
    out = gui.respond(request)
    assert out["ok"] is False and message in out["error"]
    assert gui.respond("nonsense")["ok"] is False


def test_two_dimensions_tilt_recovers_lines_across_the_scan():
    tilted, flat = gui.respond_2d({}), gui.respond_2d({"tilt_deg": 0.0})
    assert tilted["ok"] and flat["ok"]
    share = lambda out, direction: [g["share"] for g in out["groups"] if g["direction"] == direction][1]
    assert share(tilted, "across") > 0.8 > 0.3 > share(flat, "across")
    assert flat["largest_gap_across_nm"] == pytest.approx(1120.0) and tilted["largest_gap_across_nm"] < 100
    assert gui.respond_2d({"tilt_deg": 0.02})["largest_gap_across_nm"] > 1000       # too little tilt to help
    picture = np.array(tilted["truth"]).reshape(tilted["shape"])
    estimate = np.array([np.nan if v is None else v for v in tilted["estimate"]]).reshape(tilted["shape"])
    assert tilted["rms_error"] == pytest.approx(np.sqrt(np.nanmean((estimate - picture) ** 2)), abs=2e-3)
    assert tilted["scanned_share"] == pytest.approx(np.mean(~np.isnan(estimate)))
    assert picture[64, 30] != picture[64, 10] and estimate.shape == (256, 512)
    corners = np.array(tilted["footprint"]).reshape(4, 2)
    assert np.allclose(np.linalg.norm(corners[1] - corners[0]), 15 * 1120, atol=1)       # one side of 16 pixels
    assert corners[1][1] == pytest.approx(15 * 1120 * np.sin(np.deg2rad(3.58)), abs=1)
    small = gui.respond_2d({"n_side": 4, "n_frames": 40})                 # a sensor that covers little of the picture
    assert small["ok"] and small["scanned_share"] < 0.5 and None in small["estimate"]
    assert all(g["share"] is None for g in small["groups"] if g["direction"] == "across")
    assert all(g["share"] is None or -0.5 < g["share"] < 1.5 for g in small["groups"])
    assert len(tilted["truth"]) == len(tilted["estimate"]) == tilted["shape"][0] * tilted["shape"][1]
    assert gui.respond_2d({"gap_nm": 3000.0})["rms_error"] > tilted["rms_error"]
    assert "unknown setting" in gui.respond_2d({"gap": 3})["error"]
    assert "n_frames" in gui.respond_2d({"n_frames": 10**6})["error"]
    assert "method" in gui.respond_2d({"method": "magic"})["error"]


@pytest.fixture
def address():
    server = gui.make_server(port=0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


def test_server_serves_the_page_and_answers_requests(address):
    read = lambda path: urllib.request.urlopen(address + path, timeout=30).read()
    assert b"Interactive explorer" in read("/") and b"makeRunner" in read("/app.js") and read("/style.css")
    assert json.loads(read("/api/describe"))["default"] == gui.default_request()
    def post(path, body):
        ask = urllib.request.Request(address + path, data=body, headers={"Content-Type": "application/json"})
        return json.loads(urllib.request.urlopen(ask, timeout=60).read())
    assert post("/api/run", json.dumps(gui.default_request()).encode())["ok"]
    assert post("/api/run2d", b'{"n_frames": 40}')["ok"]
    for path in ("/../pyproject.toml", "/gui.py", "/nothing.html"):
        with pytest.raises(urllib.error.HTTPError):
            read(path)
    with pytest.raises(urllib.error.HTTPError):
        post("/api/run", b"not json")
    with pytest.raises(urllib.error.HTTPError):
        read("/../gui.py")
    for headers in ({"Origin": "http://evil.example"}, {"Host": "evil.example"}):          # another site's page
        ask = urllib.request.Request(address + "/api/run", data=b"{}", headers=headers)
        with pytest.raises(urllib.error.HTTPError):
            urllib.request.urlopen(ask, timeout=30)
    ask = urllib.request.Request(address + "/api/run", data=b"{}", headers={"Content-Length": "abc"})
    with pytest.raises(urllib.error.HTTPError):
        urllib.request.urlopen(ask, timeout=30)
    assert post("/api/run", b'{"noise": {"read_e": 1e300}}')["results"] == []       # no method ticked: still an answer
    huge = gui.default_request()
    huge["noise"]["read_e"] = 1e300
    assert post("/api/run", json.dumps(huge).encode())["results"][0]["scores"]["rms_error"] is None    # not-a-number sent as none


def test_server_listens_on_this_computer_only():
    server = gui.make_server(port=0)
    try:
        assert server.server_address[0] == "127.0.0.1"
    finally:
        server.server_close()


def test_one_broken_part_does_not_take_the_page_down():
    @ap.reconstruction("breaks_for_test")
    def _breaks(frames, levels, strength=1.0):
        raise RuntimeError("deliberate")

    @ap.scene("flat_for_test")
    def _flat():
        return ap.Scene("flat_for_test", np.full(600, 0.5), 20.0)
    try:
        told = gui.describe()
        assert "breaks_for_test" in [m["name"] for m in told["methods"]]
        assert "flat_for_test" in [k["name"] for k in told["scenes"]]
        request = gui.default_request()
        request["scene"] = "flat_for_test"
        request["methods"].append({"method": "breaks_for_test", "options": {"strength": 2.0}})
        out = gui.respond(request)
        good, bad = out["results"]
        assert out["ok"] and good["ok"] and good["scores"]["rms_error"] < 0.05
        assert not bad["ok"] and "RuntimeError: deliberate" in bad["error"]
    finally:
        del ap.RECONSTRUCTIONS["breaks_for_test"], ap.SCENES["flat_for_test"]


def test_what_is_drawn_is_what_was_computed():
    from ccdsr import level1 as l1
    from ccdsr import run

    request = gui.default_request()
    request["optics"].update(gap_nm=500.0, aperture_nm=560.0)
    request["scan"].update(shift_px=0.5, n_frames=100, exposure_fraction=0.5, code=[1, 0, 1, 1], wander_px=0.5)
    request["noise"].update(full_e=1000.0)
    request["positions"] = "unknown"
    request["seed"] = 3
    request["methods"] = [{"method": "least_squares_positions", "options": {}}]
    out = gui.respond(request)
    scene = ap.get_scene("bars")
    approach = ap.parse_approach(out["results"][0]["file"])
    _, frames, estimate, scores = run.run(approach, "bars", seed=3)                 # the command line's own path
    result = out["results"][0]
    assert result["scores"]["rms_error"] == pytest.approx(scores["rms_error"])
    aligned, _ = cp.align_to_truth(np.asarray(estimate), scene.surface, cp.ALIGN_PX * 1120 / scene.dx_nm)
    assert np.allclose(result["estimate"], aligned, atol=1e-4) and not np.allclose(aligned, aligned[::-1], atol=0.05)
    assert np.allclose(np.array(out["readings"]["values"]).reshape(100, 64), frames.readings, atol=0.06)
    plan = l1.nominal_positions(frames)
    assert np.allclose(out["path"]["true_nm"], (frames.positions_nm - plan)[:, 0], atol=0.06)
    assert np.std(out["path"]["true_nm"]) > 100 and np.allclose(out["path"]["believed_nm"], 0)
    assert np.std(np.array(result["path_nm"]) - np.array(out["path"]["true_nm"])) < 60 < np.std(result["path_nm"])
    seen = l1.blur(scene.surface, scene.dx_nm, frames.optics, frames.scan)
    assert np.allclose(out["seen"], seen, atol=1e-4) and np.abs(seen - scene.surface).max() > 0.2
    facts = {f["label"]: f["value"] for f in out["facts"]}
    assert facts["Readings taken"] == "6,400" and facts["Share of the test surface that a pixel passed over"] == "100"
    short = gui.respond({**request, "scan": {**request["scan"], "n_frames": 10, "n_pixels": 8, "wander_px": 0.0}})
    covered = (8 * 1120 + 9 * 560) / 73800                                          # sensor length plus travel
    assert float(short["facts"][2]["value"]) == pytest.approx(100 * covered, abs=2)
    assert facts["Readings whose opening covers any one point, on average"] == f"{6400 * 560 / 73800:,.0f}"
    assert facts["Distance travelled"] == f"{0.5 * 1120 * 99 / 1e3:,.1f}"
    assert facts["Movement between frames"] == "560" and facts["Motion smear in one reading"] == "280"
    assert facts["Light per reading at full brightness"] == "500"
    assert out["setup"]["step_nm"] == 560 and out["setup"]["aperture_nm"] == 560 and out["setup"]["smear_nm"] == 280
    again = gui.respond({**request, "seed": 4})
    assert again["readings"]["values"] != out["readings"]["values"]
    plain = gui.respond({**request, "scan": {**request["scan"], "code": None}})
    assert plain["blur"]["motion"] != out["blur"]["motion"]


def test_blur_width_and_sample_gap_facts():
    def facts(**scan):
        request = gui.default_request()
        request["scan"].update(scan)
        out = gui.respond(request)
        return {f["label"]: float(f["value"].replace(",", "")) for f in out["facts"]}, out
    gap = "Largest gap between neighbouring sample positions, all frames and pixels together"
    width = "Width of the blur of one point (at half height)"
    usual, out = facts()
    assert usual[gap] < 50 < usual["Movement between frames"]              # many frames interleave finely
    assert 1100 <= usual[width] <= 1300 and out["setup"]["blur_width_nm"] == usual[width]
    request = gui.default_request()
    request["optics"]["gap_nm"] = 0.0
    request["optics"]["aperture_nm"] = 400.0
    assert gui.respond(request)["setup"]["blur_width_nm"] == pytest.approx(400, abs=15)      # the opening alone
    request["optics"]["gap_nm"] = 100000.0
    assert gui.respond(request)["setup"]["blur_width_nm"] > 100000                          # no ceiling from the grid


def test_page_works_in_a_real_browser(address):
    """Drives the page with Playwright if Node and Playwright are installed; skipped otherwise."""
    node = shutil.which("node")
    if node is None or subprocess.run([node, "-e", "require('playwright')"], capture_output=True).returncode != 0:
        pytest.skip("Node with Playwright is not installed")
    done = subprocess.run([node, str(ROOT / "tests" / "gui_browser.js"), address], capture_output=True, text=True,
                          timeout=180)
    assert done.returncode == 0, done.stdout + done.stderr
