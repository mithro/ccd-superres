"""Interactive explorer: change a setting and see the simulation respond.

Start it with::

    python -m ccdsr.gui

and a page opens in the browser. It shows the setup drawn to the current
settings, the raw readings the sensor would record, and the reconstruction
of every method that is ticked, drawn over the true surface with its scores.
Moving a control reruns the real simulator (:mod:`ccdsr.level1`, or
:mod:`ccdsr.level1_2d` on the two-dimensional tab), so the page shows what
the code does and not a separate formula.

The page talks to this module through two functions that can also be called
directly: :func:`describe` lists what can be chosen and :func:`respond` runs
one request. Nothing about any one approach is built in: scenes, methods and
their options are read from the registries of :mod:`ccdsr.approaches`, and
the approach files in ``approaches/`` are offered as starting points.
"""

from __future__ import annotations

import argparse
import dataclasses
import inspect
import json
import threading
import time
import warnings
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np
from scipy.ndimage import maximum_filter

from . import approaches as ap
from . import compare as cp
from . import level1 as l1
from . import level1_2d as l2
from .resolution import gap_transfer

STATIC = Path(__file__).parent / "gui_static"
APPROACH_DIR = Path(__file__).parent.parent / "approaches"

# Sizes above these would make the page slow to respond; the command line has no such limit.
MAX_FRAMES, MAX_PIXELS = 1000, 256
MAX_CODE, MAX_WANDER_FRAMES, MAX_LIGHT_E, MAX_SEED = 64, 10000, 1e9, 2**31 - 1
_LOCK = threading.Lock()                 # one request at a time: the warning capture below is not thread-safe
MAX_FRAMES_2D, MAX_SIDE_2D = 600, 32

# How each setting is offered on the page: (key, label, unit, lowest, highest, step, scale, help).
CONTROLS = [
    ("optics.gap_nm", "Gap between sensor and surface", "nm", 20, 20000, None, "log",
     "The further the sensor is from the surface, the more the light from one point spreads."),
    ("optics.gap_model", "Kind of surface and light", "", None, None, None, "choice",
     "diffuse: a matt surface that glows evenly. collimated: a mirror-like surface under a straight beam."),
    ("optics.wavelength_nm", "Wavelength of the light", "nm", 200, 800, 5, "linear",
     "Only matters for the collimated kind."),
    ("optics.pitch_nm", "Pixel spacing", "nm", 500, 3000, 10, "linear",
     "Distance from one pixel to the next. 1,120 nm is the Raspberry Pi Camera Module 2."),
    ("optics.aperture_nm", "Opening of each pixel", "nm", 50, 3000, 10, "linear",
     "Width that takes in light. Narrower sees finer detail but collects less light. "
     "It cannot be wider than the pixel spacing."),
    ("optics.edge_sigma_nm", "Softness of the pixel edges", "nm", 0, 500, 5, "linear",
     "0 is a pixel with perfectly sharp edges."),
    ("scan.shift_px", "Movement between frames", "pixel", 0.02, 4, 0.01, "linear",
     "How far the sensor moves from one frame to the next, in pixel spacings."),
    ("scan.n_frames", "Number of frames", "", 10, 600, 1, "linear", "How many times the sensor is read."),
    ("scan.n_pixels", "Pixels along the scan", "", 8, 128, 1, "linear", "Length of the line of pixels."),
    ("scan.exposure_fraction", "Share of each frame the light is on", "", 0, 1, 0.01, "linear",
     "0 is a brief flash that freezes the motion. 1 smears each reading over the whole movement of a frame."),
    ("scan.code", "On-off pattern of the light within the exposure", "", None, None, None, "code",
     "For instance 1,0,1,1,0,1. Leave empty for light that is simply on."),
    ("scan.jitter_px", "Random position error of every frame", "pixel, rms", 0, 1, 0.01, "linear",
     "Shake that differs from frame to frame."),
    ("scan.wander_px", "Slow wandering of the path", "pixel, rms", 0, 3, 0.01, "linear",
     "Drift of the stage away from the planned constant speed."),
    ("scan.wander_frames", "How many frames one wander lasts", "frames", 2, 200, 1, "linear",
     "Larger is a smoother, slower wander."),
    ("noise.full_e", "Light collected at full brightness", "electrons", 10, 100000, None, "log",
     "More light means less noise in proportion."),
    ("noise.read_e", "Read noise of the sensor", "electrons, rms", 0, 50, 0.5, "linear",
     "Noise added to every reading whatever the light."),
    ("noise.gain_sigma", "Spread of pixel sensitivities", "fraction", 0, 0.2, 0.005, "linear",
     "How much pixels differ from each other. The reconstructions here do not correct it."),
    ("noise.photon", "Photon noise", "", None, None, None, "bool",
     "The unavoidable randomness of light arriving as separate photons."),
]

CONTROLS_2D = [
    ("gap_nm", "Gap between sensor and surface", "nm", 20, 20000, None, "log", CONTROLS[0][7]),
    ("aperture_nm", "Opening of each pixel", "nm", 50, 1120, 10, "linear", CONTROLS[4][7]),
    ("tilt_deg", "Sensor tilt", "degrees", 0, 45, 0.02, "linear",
     "Turning the sensor makes its rows trace different lines across the scan."),
    ("shift_px", "Movement between frames", "pixel", 0.02, 4, 0.01, "linear", CONTROLS[6][7]),
    ("n_frames", "Number of frames", "", 40, MAX_FRAMES_2D, 1, "linear", "How many times the sensor is read."),
    ("n_side", "Pixels along each side of the sensor", "", 8, MAX_SIDE_2D, 1, "linear",
     "The sensor is square in this view."),
    ("exposure_fraction", "Share of each frame the light is on", "", 0, 1, 0.01, "linear", CONTROLS[9][7]),
    ("row_delay_px", "Extra movement per sensor row", "pixel", 0, 0.2, 0.002, "linear",
     "A sensor that reads its rows one after another sees each row slightly later."),
    ("jitter_px", "Random position error of every frame", "pixel, rms", 0, 1, 0.01, "linear",
     "Shake that differs from frame to frame. On this tab the reconstruction is told the exact position of "
     "every frame, shake included, so this changes the sampling and does not test position finding."),
    ("full_e", "Light collected at full brightness", "electrons", 10, 100000, None, "log", CONTROLS[14][7]),
    ("read_e", "Read noise of the sensor", "electrons, rms", 0, 50, 0.5, "linear", CONTROLS[15][7]),
    ("smoothness", "Smoothing in least squares", "", 1e-5, 10, None, "log",
     "How strongly the reconstruction prefers a smooth picture."),
]
DEFAULTS_2D = {"gap_nm": 300.0, "aperture_nm": 1120.0, "tilt_deg": 3.58, "shift_px": 0.37, "n_frames": 300,
               "n_side": 16, "exposure_fraction": 0.0, "row_delay_px": 0.0, "jitter_px": 0.0, "full_e": 2500.0,
               "read_e": 2.0, "smoothness": 1e-2, "method": "least_squares", "seed": 0}
PERIODS_2D = (1960.0, 1400.0, 980.0, 700.0)
DX_2D, SHAPE_2D = 70.0, (256, 512)
ITERATIONS_2D = 100                     # solver steps on the two-dimensional tab, so that no change takes long

METHOD_LABELS = {
    "shift_and_add": "Shift and add",
    "wiener": "Wiener filter",
    "least_squares": "Least squares",
    "least_squares_positions": "Least squares, solving positions",
    "two_materials": "Two known materials",
    "two_materials_positions": "Two known materials, solving positions",
}
SCENE_LABELS = {
    "bars": "Bar groups",
    "random_layout": "Random two-material layout",
    "isolated_lines": "Isolated narrow lines",
    "soft_ramps": "Smooth waves of many reflectances",
}


class BadRequest(ValueError):
    """A request the page should show as a message and not as a failure of the program."""


# ----------------------------------------------------------------- describe

def _method_options(name):
    fn = ap.RECONSTRUCTIONS[name].fn
    return {p.name: p.default for p in list(inspect.signature(fn).parameters.values())[2:]}


def default_request():
    """The request the page starts from: every setting at its default, least squares ticked."""
    parts = {}
    for part, cls in (("optics", l1.Optics1D), ("scan", l1.Scan1D), ("noise", l1.Noise1D)):
        parts[part] = {f.name: f.default for f in dataclasses.fields(cls) if f.name != "start_nm"}
    parts["optics"]["aperture_nm"] = parts["optics"]["pitch_nm"]
    return {"scene": "bars", "seed": 0, "positions": "known", **parts,
            "methods": [{"method": "least_squares", "options": _method_options("least_squares")}]}


def _preset(approach: ap.Approach):
    """An approach file as a full request, so that loading it sets every control."""
    request = default_request()
    for part in ("optics", "scan", "noise"):
        mine = dict(getattr(approach, part))
        if "code" in mine:
            mine["code"] = list(mine["code"])
        request[part].update(mine)
    if "aperture_nm" not in approach.optics:
        request["optics"]["aperture_nm"] = request["optics"]["pitch_nm"]
    request["positions"] = approach.positions
    request["methods"] = [{"method": approach.method, "options": {**_method_options(approach.method),
                                                                  **approach.options}}]
    return request


def presets(directory=None):
    """The approach files found, each as ``{"name", "description", "request"}``."""
    directory = APPROACH_DIR if directory is None else Path(directory)
    found = []
    for path in sorted(directory.glob("*.toml")) if directory.is_dir() else []:
        try:
            approach = ap.load_approach(path)
        except (ap.InvalidApproach, ValueError):
            continue
        found.append({"name": approach.name, "description": approach.description, "file": path.name,
                      "request": _preset(approach)})
    return found


def _control(row):
    key, label, unit, low, high, step, scale, help_text = row
    return {"key": key, "label": label, "unit": unit, "min": low, "max": high, "step": step, "scale": scale,
            "help": help_text}


def describe(directory=None):
    """Everything the page needs to draw its controls."""
    methods = []
    for name, recon in ap.RECONSTRUCTIONS.items():
        methods.append({"name": name, "label": METHOD_LABELS.get(name, name.replace("_", " ")),
                        "needs_materials": "materials" in recon.needs,
                        "solves_positions": recon.solves_positions, "options": _method_options(name)})
    scenes = []
    for name in ap.SCENES:
        scene = ap.get_scene(name)
        about = f"{scene.surface.size * scene.dx_nm / 1e3:,.1f} µm long"
        if scene.groups:
            about += f", bars repeating every {max(g[0] for g in scene.groups):,.0f} down to " \
                     f"{min(g[0] for g in scene.groups):,.0f} nm"
        about += ", two materials" if scene.levels is not None else ", many reflectances"
        scenes.append({"name": name, "label": SCENE_LABELS.get(name, name.replace("_", " ")), "about": about,
                       "two_materials": scene.levels is not None})
    return {"controls": [_control(r) for r in CONTROLS], "choices": {"optics.gap_model": list(ap._CHOICES["gap_model"])},
            "methods": methods, "scenes": scenes, "default": default_request(), "presets": presets(directory),
            "controls_2d": [_control(r) for r in CONTROLS_2D], "default_2d": dict(DEFAULTS_2D),
            "methods_2d": [{"name": "least_squares", "label": "Least squares"},
                           {"name": "shift_and_add", "label": "Shift and add"}],
            "limits": {"frames": MAX_FRAMES, "pixels": MAX_PIXELS, "code": MAX_CODE}}


# ------------------------------------------------------------ one dimension

def _clean_parts(request):
    """The optics, scan and noise settings of a request, as the approach reader wants them."""
    parts = {}
    for part in ("optics", "scan", "noise"):
        given = request.get(part, {})
        if not isinstance(given, dict):
            raise BadRequest(f"{part} must be a group of settings")
        parts[part] = dict(given)
    optics, scan = parts["optics"], parts["scan"]
    if optics.get("aperture_nm") is None or optics.get("aperture_nm") == optics.get("pitch_nm", 1120.0):
        optics.pop("aperture_nm", None)                # the whole pixel: the simulator's own default
    elif ap._is_number(optics["aperture_nm"]) and ap._is_number(optics.get("pitch_nm", 1120.0)):
        if optics["aperture_nm"] > optics.get("pitch_nm", 1120.0):
            raise BadRequest("the opening of a pixel cannot be wider than the pixel spacing "
                             f"({optics['aperture_nm']:g} nm against {optics.get('pitch_nm', 1120.0):g} nm)")
    if scan.get("code") in (None, [], ""):
        scan.pop("code", None)
    else:
        scan["code"] = tuple(scan["code"]) if isinstance(scan["code"], (list, tuple)) else scan["code"]
    for name in ("n_frames", "n_pixels"):
        if isinstance(scan.get(name), float) and np.isfinite(scan[name]) and scan[name] == int(scan[name]):
            scan[name] = int(scan[name])
    caps = (("scan", "n_frames", MAX_FRAMES), ("scan", "n_pixels", MAX_PIXELS),
            ("scan", "wander_frames", MAX_WANDER_FRAMES), ("noise", "full_e", MAX_LIGHT_E))
    for part, name, most in caps:
        value = parts[part].get(name, 0)
        if ap._is_number(value) and value > most:
            raise BadRequest(f"{part}.{name} can be at most {most:,.0f} on this page, not {value:g}; "
                             "the command line has no such limit")
    if isinstance(scan.get("code"), tuple) and len(scan["code"]) > MAX_CODE:
        raise BadRequest(f"scan.code can have at most {MAX_CODE} entries on this page")
    return parts


def _approach(entry, parts, positions):
    """The :class:`ccdsr.approaches.Approach` for one ticked method."""
    if not isinstance(entry, dict) or "method" not in entry:
        raise BadRequest("each method is written {'method': name, 'options': {...}}")
    method = entry["method"]
    if method not in ap.RECONSTRUCTIONS:
        raise BadRequest(f"unknown method {method!r}; known: {sorted(ap.RECONSTRUCTIONS)}")
    return ap.Approach(
        name=METHOD_LABELS.get(method, method), description="Made in the interactive explorer.", hardware=(),
        positions=positions, method=method, options=dict(entry.get("options") or {}), optics=parts["optics"],
        scan=parts["scan"], noise=parts["noise"], knows_materials="materials" in ap.RECONSTRUCTIONS[method].needs)


def approach_text(approach: ap.Approach):
    """The approach as the text of an approach file, ready to save under ``approaches/``."""
    def value(v):
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, str):
            return json.dumps(v)
        if isinstance(v, (list, tuple)):
            return "[" + ", ".join(value(x) for x in v) + "]"
        return repr(float(v)) if isinstance(v, float) else repr(v)

    slug = approach.method.replace("_", "-") + "-from-explorer"
    lines = [f"name = {json.dumps(slug)}", f"description = {json.dumps(approach.description)}", "hardware = []",
             f"positions = {json.dumps(approach.positions)}"]
    defaults = {"optics": l1.Optics1D(), "scan": l1.Scan1D(), "noise": l1.Noise1D()}
    for part in ("optics", "scan", "noise"):
        changed = {k: v for k, v in getattr(approach, part).items() if getattr(defaults[part], k) != v}
        if changed:
            lines += ["", f"[{part}]"] + [f"{k} = {value(v)}" for k, v in changed.items()]
    lines += ["", "[reconstruction]", f"method = {json.dumps(approach.method)}"]
    lines += [f"{k} = {value(v)}" for k, v in approach.options.items()]
    if approach.knows_materials:
        lines += ["", "[knowledge]", "materials = true"]
    return "\n".join(lines) + "\n"


def _blur_curves(optics: l1.Optics1D, scan: l1.Scan1D):
    """How much of a detail of each size survives each cause of blur, and all three together."""
    periods = np.geomspace(100.0, 20000.0, 280)
    freq = 1 / periods
    smear = abs(scan.shift_px) * optics.pitch_nm * scan.exposure_fraction
    gap = np.abs(gap_transfer(periods, optics.gap_nm, optics.gap_model, optics.wavelength_nm))
    pixel = np.abs(l1.transfer(freq, dataclasses.replace(optics, gap_nm=0.0)))
    motion = np.abs(l1.motion_kernel_transfer(freq, smear, scan.code))
    total = np.abs(l1.transfer(freq, optics, smear, scan.code))
    return {"periods_nm": _list(periods, 1), "gap": _list(gap), "pixel": _list(pixel), "motion": _list(motion),
            "total": _list(total), "smear_nm": float(smear)}


def _blur_width_nm(optics, scan, n=16384):
    """Width at half height of the combined blur of a single point, by the simulator's own blur."""
    dx_nm = max(10.0, optics.gap_nm / 400.0, optics.pitch_nm / 400.0)      # the grid grows with the blur
    spike = np.zeros(n)
    spike[n // 2] = 1.0
    spread = l1.blur(spike, dx_nm, optics, scan)
    above = np.flatnonzero(spread >= 0.5 * spread.max())
    return float((above[-1] - above[0] + 1) * dx_nm)


def _list(values, digits=4):
    return [round(float(v), digits) for v in np.asarray(values).ravel()]


def _facts(scene, frames, optics, scan, noise, blur_width):
    aperture = optics.pitch_nm if optics.aperture_nm is None else optics.aperture_nm
    travel = abs(scan.shift_px) * optics.pitch_nm * (scan.n_frames - 1)
    length = scene.surface.size * scene.dx_nm
    light = noise.full_e * aperture / optics.pitch_nm
    per_point = frames.readings.size * aperture / length
    where = np.sort(np.unique(np.round(frames.positions_nm.ravel() % length, 3)))
    largest_gap = float(np.max(np.diff(np.concatenate([where, [where[0] + length]]))))
    cells = np.zeros(scene.surface.size, dtype=bool)
    cells[np.round(frames.positions_nm.ravel() / scene.dx_nm).astype(int) % cells.size] = True
    passed = maximum_filter(cells, size=max(1, int(round(optics.pitch_nm / scene.dx_nm))), mode="wrap").mean()
    return [
        {"label": "Readings taken", "value": f"{frames.readings.size:,}", "unit": ""},
        {"label": "Readings whose opening covers any one point, on average", "value": f"{per_point:,.0f}", "unit": ""},
        {"label": "Share of the test surface that a pixel passed over", "value": f"{100 * passed:.0f}", "unit": "%"},
        {"label": "Distance travelled", "value": f"{travel / 1e3:,.1f}", "unit": "µm"},
        {"label": "Length of the test surface (it repeats end to end)", "value": f"{length / 1e3:,.1f}", "unit": "µm"},
        {"label": "Movement between frames", "value": f"{abs(scan.shift_px) * optics.pitch_nm:,.0f}", "unit": "nm"},
        {"label": "Largest gap between neighbouring sample positions, all frames and pixels together",
         "value": f"{largest_gap:,.0f}", "unit": "nm"},
        {"label": "Width of the blur of one point (at half height)", "value": f"{blur_width:,.0f}", "unit": "nm"},
        {"label": "Motion smear in one reading", "value":
            f"{abs(scan.shift_px) * optics.pitch_nm * scan.exposure_fraction:,.0f}", "unit": "nm"},
        {"label": "Light per reading at full brightness", "value": f"{light:,.0f}", "unit": "electrons"},
    ]


def respond(request):
    """Run one request from the page and return what it draws.

    ``request`` is shaped like :func:`default_request`. The answer holds the
    true surface, the raw readings, the blur curves and, for every method
    asked for, the reconstruction and its scores or the reason it could not
    run. A request that cannot be simulated at all gives
    ``{"ok": False, "error": reason}``.
    """
    return _guarded(_respond, request, {c[0]: c[1] for c in CONTROLS})


def _guarded(run, request, labels):
    """Run one request, one at a time, and turn any failure into a reason the page can show."""
    try:
        with _LOCK:
            return run(request)
    except (BadRequest, ap.InvalidApproach) as reason:
        return {"ok": False, "error": _plain_words(str(reason), labels)}
    except Exception as reason:                        # whatever a registered part raises, the page gets an answer
        return {"ok": False, "error": f"the simulator stopped with an error ({type(reason).__name__}: {reason})"}


def _plain_words(message, labels):
    """An error message with each setting's code name followed by its label on the page."""
    if message.startswith("settings: "):
        message = message[len("settings: "):]
    for key in sorted(labels, key=len, reverse=True):
        if key in message:
            return message.replace(key, f"'{labels[key]}' ({key})", 1)
    return message


def _respond(request):
    if not isinstance(request, dict):
        raise BadRequest("a request is a group of settings")
    parts = _clean_parts(request)
    positions = request.get("positions", "known")
    seed = request.get("seed", 0)
    if not isinstance(seed, int) or isinstance(seed, bool) or not 0 <= seed <= MAX_SEED:
        raise BadRequest(f"the seed is a whole number from 0 to {MAX_SEED:,}")
    try:
        scene = ap.get_scene(request.get("scene", "bars"))
    except (ValueError, TypeError) as reason:
        raise BadRequest(str(reason))
    methods = request.get("methods", [])
    if not isinstance(methods, list):
        raise BadRequest("methods is a list")

    base = ap.Approach(name="settings", description="", hardware=(), positions=positions, method="shift_and_add",
                       optics=parts["optics"], scan=parts["scan"], noise=parts["noise"])
    base.check()
    condition = ap.Condition("as set")
    started = time.perf_counter()
    frames = ap.simulate(base, scene, condition, seed)
    simulate_s = time.perf_counter() - started
    optics, scan, noise = frames.optics, frames.scan, frames.noise
    plan = l1.nominal_positions(frames)
    believed = ap.believed_frames(base, frames).positions_nm
    max_cells = cp.ALIGN_PX * optics.pitch_nm / scene.dx_nm

    results = []
    for entry in methods:
        name = entry.get("method") if isinstance(entry, dict) else None
        result = {"method": name, "label": METHOD_LABELS.get(name, str(name)), "ok": False}
        try:
            approach = _approach(entry, parts, positions)
            approach.check(scene)
            started = time.perf_counter()
            with warnings.catch_warnings(record=True) as raised:
                warnings.simplefilter("always")
                estimate, solved = ap.reconstruct(approach, scene, frames)
            result["seconds"] = round(time.perf_counter() - started, 3)
            result["note"] = "; ".join(sorted({str(w.message) for w in raised}))
            scores = cp.score(scene, frames, estimate, solved, believed)
            aligned, _ = cp.align_to_truth(np.asarray(estimate, dtype=float), scene.surface, max_cells)
            result.update(ok=True, estimate=_list(aligned), scores=scores, file=approach_text(approach),
                          solves_positions=solved is not None)
            if solved is not None:
                result["path_nm"] = _list((l1.align_positions(frames, solved) - plan)[:, 0], 1)
        except (BadRequest, ap.InvalidApproach) as reason:
            result["error"] = str(reason)
        except Exception as reason:                    # one method failing must not hide the others
            result["error"] = f"the method stopped with an error ({type(reason).__name__}: {reason})"
        results.append(result)

    blur_width = _blur_width_nm(optics, scan)
    aperture = optics.pitch_nm if optics.aperture_nm is None else optics.aperture_nm
    return {
        "ok": True,
        "scene": {"name": scene.name, "dx_nm": scene.dx_nm, "truth": _list(scene.surface),
                  "groups": [[g[0], int(g[1]), int(g[2])] for g in scene.groups],
                  "levels": list(scene.levels) if scene.levels else None},
        "seen": _list(l1.blur(scene.surface, scene.dx_nm, optics, scan)),
        "readings": {"n_frames": int(frames.readings.shape[0]), "n_pixels": int(frames.readings.shape[1]),
                     "values": _list(frames.readings, 1), "full": float(noise.full_e * aperture / optics.pitch_nm)},
        "path": {"true_nm": _list((frames.positions_nm - plan)[:, 0], 1),
                 "believed_nm": _list((believed - plan)[:, 0], 1), "positions": positions},
        "blur": _blur_curves(optics, scan),
        "setup": {"gap_nm": optics.gap_nm, "pitch_nm": optics.pitch_nm, "aperture_nm": aperture,
                  "step_nm": scan.shift_px * optics.pitch_nm, "blur_width_nm": blur_width,
                  "smear_nm": abs(scan.shift_px) * optics.pitch_nm * scan.exposure_fraction,
                  "n_pixels": scan.n_pixels, "gap_model": optics.gap_model},
        "facts": _facts(scene, frames, optics, scan, noise, blur_width),
        "simulate_seconds": round(simulate_s, 3),
        "results": results,
    }


# ----------------------------------------------------------- two dimensions

def respond_2d(request):
    """Run one request of the two-dimensional tab: a tilted square sensor over a picture of line groups."""
    return _guarded(_respond_2d, request, {c[0]: c[1] for c in CONTROLS_2D})


def _number(settings, name, low, high, whole=False):
    value = settings[name]
    if not ap._is_number(value) or not low <= value <= high or (whole and int(value) != value):
        kind = "a whole number" if whole else "a number"
        raise BadRequest(f"{name} must be {kind} from {low:g} to {high:g}, not {value!r}")
    return int(value) if whole else float(value)


def _respond_2d(request):
    if not isinstance(request, dict):
        raise BadRequest("a request is a group of settings")
    unknown = set(request) - set(DEFAULTS_2D)
    if unknown:
        raise BadRequest(f"unknown setting(s) {sorted(unknown)}; known: {sorted(DEFAULTS_2D)}")
    s = {**DEFAULTS_2D, **request}
    side = _number(s, "n_side", 2, MAX_SIDE_2D, whole=True)
    optics = l2.Optics(gap_nm=_number(s, "gap_nm", 0, 1e7), aperture_nm=_number(s, "aperture_nm", 1, 1120))
    shift = _number(s, "shift_px", -10, 10)
    if shift == 0:
        raise BadRequest("shift_px must not be 0: the sensor has to move between frames")
    scan = l2.Scan2D(n_rows=side, n_cols=side, n_frames=_number(s, "n_frames", 1, MAX_FRAMES_2D, whole=True),
                     shift_px=shift, tilt_deg=_number(s, "tilt_deg", -90, 90),
                     exposure_fraction=_number(s, "exposure_fraction", 0, 1),
                     row_delay_px=_number(s, "row_delay_px", -1, 1), jitter_px=_number(s, "jitter_px", 0, 10))
    noise = l2.Noise(full_e=_number(s, "full_e", 1e-9, 1e12), read_e=_number(s, "read_e", 0, 1e6))
    seed = _number(s, "seed", 0, MAX_SEED, whole=True)
    smoothness = _number(s, "smoothness", 0, 1e9)
    if s["method"] not in ("least_squares", "shift_and_add"):
        raise BadRequest(f"unknown method {s['method']!r}; known: ['least_squares', 'shift_and_add']")

    picture, groups = l2.line_groups(list(PERIODS_2D), DX_2D, SHAPE_2D)
    started = time.perf_counter()
    frames = l2.simulate(picture, DX_2D, optics, scan, noise, seed=seed)
    simulate_s = time.perf_counter() - started
    started = time.perf_counter()
    with warnings.catch_warnings(record=True) as raised:
        warnings.simplefilter("always")
        if s["method"] == "least_squares":
            estimate = l2.least_squares(frames, smoothness=smoothness, iterations=ITERATIONS_2D)[0]
        else:
            estimate = l2.shift_and_add(frames)[0]
    seconds = time.perf_counter() - started
    note = "The solver stopped at its limit of steps before fully settling." if raised else ""
    # Only what at least one pixel passed over can be judged; the rest is reported as not scanned.
    # A cell counts as scanned if the centre of some reading came within half a pixel spacing of it.
    reach = max(1, int(round(optics.pitch_nm / DX_2D)))
    scanned = maximum_filter(np.asarray(l2.shift_and_add(frames)[1]) > 0, size=reach, mode="wrap")
    estimate = np.nan_to_num(np.asarray(estimate, dtype=float), nan=0.0)
    shown = []
    for group in groups:
        _, _, y0, y1, x0, x1 = group
        share = None
        if scanned[y0:y1, x0:x1].all():
            share = float(l2.group_contrast(estimate, group, DX_2D) / l2.group_contrast(picture, group, DX_2D))
        shown.append({"period_nm": float(group[0]), "direction": str(group[1]), "share": share})
    offsets = np.sort(l2.cross_scan_offsets(scan, optics.pitch_nm))
    across_gap = float(np.max(np.diff(np.concatenate([offsets, [offsets[0] + 1.0]]))) * optics.pitch_nm)
    rms = float(np.sqrt(np.mean((estimate - picture)[scanned] ** 2))) if scanned.any() else None
    return {
        "ok": True, "shape": list(SHAPE_2D), "dx_nm": DX_2D, "note": note,
        "truth": _list(picture, 3), "estimate": [v if ok else None for v, ok in zip(_list(estimate, 3), scanned.ravel())],
        "scanned_share": float(scanned.mean()),
        "frame": {"side": side, "values": _list(frames.readings[frames.readings.shape[0] // 2], 1)},
        "rms_error": rms, "groups": shown, "largest_gap_across_nm": across_gap,
        "readings": int(frames.readings.size), "seconds": round(seconds, 3), "simulate_seconds": round(simulate_s, 3),
        "footprint": _list(frames.positions_nm[0].reshape(-1, 2)[[0, side - 1, side * side - 1, side * (side - 1)]], 1),
        "step_nm": shift * optics.pitch_nm,
    }


# ------------------------------------------------------------------- server

_TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
          ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml"}
_ROUTES = {"/api/run": respond, "/api/run2d": respond_2d}


class _Handler(BaseHTTPRequestHandler):
    timeout = 30                                       # a request that stalls does not hold a thread for ever

    def _local(self):
        """True if the request names this server and comes from its own page, not from another site."""
        port = self.server.server_address[1]
        mine = {f"127.0.0.1:{port}", f"localhost:{port}"}
        origin = self.headers.get("Origin")
        return self.headers.get("Host") in mine and (origin is None or origin in {f"http://{m}" for m in mine})

    def _send(self, status, body, kind):
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, value, status=200):
        self._send(status, json.dumps(value, allow_nan=False, default=_plain).encode(), "application/json")

    def do_GET(self):
        path = self.path.split("?")[0]
        if not self._local():
            return self._send(403, b"not allowed", "text/plain")
        if path == "/api/describe":
            return self._json(describe())
        name = "index.html" if path == "/" else path.lstrip("/")
        target = STATIC / name
        inside = target.resolve().parent == STATIC.resolve()
        if "/" in name or "\\" in name or not inside or not target.is_file() or target.suffix not in _TYPES:
            return self._send(404, b"not found", "text/plain")
        self._send(200, target.read_bytes(), _TYPES[target.suffix])

    def do_POST(self):
        route = _ROUTES.get(self.path)
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if route is None or not self._local() or not 0 < length < 1_000_000:
            return self._json({"ok": False, "error": "not a request this page understands"}, 400)
        try:
            request = json.loads(self.rfile.read(length))
        except (ValueError, RecursionError):
            return self._json({"ok": False, "error": "the request was not readable"}, 400)
        try:
            answer = _no_nan(route(request))
        except Exception as reason:                    # never leave the page without an answer
            answer = {"ok": False, "error": f"the simulator stopped with an error ({type(reason).__name__}: {reason})"}
        self._json(answer)

    def log_message(self, *args):                      # keep the terminal quiet
        pass


def _plain(value):
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"cannot send {type(value).__name__}")


def _no_nan(value):
    """Replace numbers that JSON cannot carry (not-a-number, infinity) by None."""
    if isinstance(value, dict):
        return {k: _no_nan(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_no_nan(v) for v in value]
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    return value


def make_server(port=8765, host="127.0.0.1"):
    """The web server, not yet started. ``port=0`` picks a free port."""
    return ThreadingHTTPServer((host, port), _Handler)


def main(argv=None):
    """Start the server and open the page: what ``python -m ccdsr.gui`` runs."""
    parser = argparse.ArgumentParser(description="Interactive explorer of the scanning sensor simulator.")
    parser.add_argument("--port", type=int, default=8765, help="port to serve the page on (default: 8765)")
    parser.add_argument("--no-browser", action="store_true", help="do not open the page automatically")
    args = parser.parse_args(argv)
    try:
        server = make_server(args.port)
    except OSError as reason:
        raise SystemExit(f"cannot start on port {args.port}: {reason}. Try --port with another number.")
    address = f"http://127.0.0.1:{server.server_address[1]}/"
    print(f"Interactive explorer running at {address}  (Ctrl+C to stop)")
    if not args.no_browser:
        webbrowser.open(address)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
