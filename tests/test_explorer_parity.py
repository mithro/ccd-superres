"""The JavaScript model behind the explorer must agree with the Python package."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from ccdsr.resolution import explore, gap_transfer
from ccdsr.sampling import Scan, Sensor

MODEL = Path(__file__).resolve().parents[1] / "explorer" / "model.js"

CASES = [
    dict(fractionPerS=0.2, fps=10, exposureFraction=1, tiltTan=0, gapNm=3000),
    dict(fractionPerS=0.2, fps=10, exposureFraction=0.003, tiltTan=0.0625, gapNm=300),
    dict(fractionPerS=0.2, fps=10, exposureFraction=0.003, tiltTan=0.0625, gapNm=30000),
    dict(fractionPerS=0.01, fps=30, exposureFraction=0.1, tiltTan=0.03, gapNm=1000,
         snrSingle=20, contrast=0.3, edgeSigmaNm=300, passes=4),
    dict(fractionPerS=0.2, fps=10, exposureFraction=0.003, tiltTan=0, gapNm=100),
    dict(fractionPerS=0.002, fps=30, exposureFraction=0.05, tiltTan=0.0625, gapNm=80,
         apertureNm=100, gapModel="collimated", wavelengthNm=405, passes=10),
    dict(fractionPerS=0.002, fps=30, exposureFraction=0.05, tiltTan=0.0625, gapNm=5000,
         gapModel="collimated", wavelengthNm=193),
]


def run_js(expr: str):
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    script = f"const M = require({json.dumps(str(MODEL))}); console.log(JSON.stringify({expr}));"
    return json.loads(subprocess.run([node, "-e", script], check=True, capture_output=True,
                                     text=True).stdout)


def test_gap_transfer_matches_scipy():
    periods = [50, 300, 1000, 5000, 1e5, 1e7]
    js = run_js(f"{json.dumps(periods)}.map(p => M.gapTransfer(p, 1000))")
    for p, v in zip(periods, js):
        assert v == pytest.approx(float(gap_transfer(p, 1000.0)), rel=1e-5, abs=1e-300)


@pytest.mark.parametrize("case", CASES)
def test_explore_matches_python(case):
    sensor = Sensor()
    js = run_js(
        "(() => { const r = M.explore(Object.assign({sensor: M.SENSORS.imx219}, "
        f"{json.dumps(case)}), {{maxSamples: 100000, grid: 96}}); delete r.phases; return r; }})()"
    )
    scan = Scan(fps=case["fps"], fraction_per_s=case["fractionPerS"],
                exposure_s=case["exposureFraction"] / case["fps"], tilt_tan=case["tiltTan"])
    py = explore(sensor, scan, case["gapNm"], case.get("snrSingle", 50),
                 case.get("contrast", 1), case.get("edgeSigmaNm", 0), case.get("passes", 1),
                 aperture_nm=case.get("apertureNm"), gap_model=case.get("gapModel", "diffuse"),
                 wavelength_nm=case.get("wavelengthNm", 550))
    b = py.budget
    assert js["shiftPx"] == pytest.approx(b.shift_px)
    assert js["samplesPerPoint"] == pytest.approx(b.samples_per_point)
    assert js["blurPx"] == pytest.approx(b.blur_px)
    assert js["coverage"]["distinct"] == b.coverage.distinct_phases
    assert js["coverage"]["gapAlongPx"] == pytest.approx(b.coverage.largest_gap_along_px, abs=1e-6)
    assert js["coverage"]["holePx"] == pytest.approx(b.coverage.largest_hole_px, abs=0.01)
    assert js["noiseLimitedNm"] == pytest.approx(py.noise_limited_nm, rel=1e-3)
    assert js["recoverableNm"] == pytest.approx(py.recoverable_nm, rel=0.05)
    assert js["limitedBy"] == py.limited_by
