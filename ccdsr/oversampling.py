"""How the result changes with the number of readings of each point.

Oversampling is reading every point of the surface many times, at different
positions under the pixels. This module runs one or more approaches at a
series of oversampling levels and reports the result against the number of
readings per point, in three ways of getting more readings::

    python -m ccdsr.oversampling approaches/least-squares.toml --out results/oversampling

``more-time``
    More frames with the same light in each. The scan takes longer in
    proportion.
``same-time``
    More frames in the same total time, so each frame has less light. With
    no read noise the total light is the same; the read noise of each
    reading is what the extra frames cost.
``repeat``
    More frames with the same light in each, but the sensor steps by whole
    pixels, so every frame lands on the same places. This is plain
    averaging: it lowers noise and adds no new positions.

See ``docs/oversampling.md``.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import math
import warnings
from pathlib import Path

import numpy as np

from . import approaches as ap
from . import compare as cp
from . import level1 as l1

WAYS = ("more-time", "same-time", "repeat")
FRAMES = (1, 2, 4, 8, 16, 32, 64, 128, 256, 512)
REFERENCE_FRAMES = 64          # "same-time" gives every level the light of this many full frames
COHERENCE_SHARE = 0.5          # a band counts as recovered from this agreement with the truth


def readings_per_point(frames: l1.Frames1D) -> float:
    """Average number of readings whose pixel covers a point of the surface.

    The test surfaces repeat end to end, so every pixel of every frame lies
    on the surface and the figure is the number of readings times the pixel
    pitch divided by the length of the surface. A pixel with a narrow
    opening is counted by its pitch, so that the figure does not change with
    the opening.
    """
    return float(frames.readings.size * frames.optics.pitch_nm / (frames.n_grid * frames.dx_nm))


def distinct_positions_per_pixel(frames: l1.Frames1D, cell_nm=None) -> float:
    """How many different places within one pixel width the readings fall on.

    Positions are taken along the repeating surface and sorted into cells of
    ``cell_nm`` (by default the surface grid); the number of occupied cells
    is scaled to one pixel pitch. Readings that land on a place already
    read add nothing to this figure.
    """
    cell = frames.dx_nm if cell_nm is None else cell_nm
    length = frames.n_grid * frames.dx_nm
    cells = np.unique(np.floor((frames.positions_nm.ravel() % length) / cell).astype(np.int64))
    return float(cells.size * frames.optics.pitch_nm / length)


def scan_for(way, n_frames, base: l1.Scan1D, base_noise: l1.Noise1D):
    """The scan and noise settings for one oversampling level."""
    if way not in WAYS:
        raise ValueError(f"unknown way {way!r}; known: {WAYS}")
    scan = dataclasses.replace(base, n_frames=int(n_frames))
    noise = base_noise
    if way == "repeat":
        scan = dataclasses.replace(scan, shift_px=float(max(1, round(base.shift_px))))
    if way == "same-time":
        noise = dataclasses.replace(base_noise, full_e=base_noise.full_e * REFERENCE_FRAMES / n_frames)
    return scan, noise


def recovered_period(estimates, truth, dx_nm, bands=28, longest_nm=8000.0):
    """Finest period down to which the reconstructions agree with the truth.

    The estimates (one per run) and the truth are split into waves. In each
    band of periods, the part of the estimates that is in step with the
    truth is divided by the geometric mean of the two strengths, which gives
    1 for a perfect copy and about 0 for noise. The answer is the short end
    of the last band, going from long periods to short, that still reaches
    ``COHERENCE_SHARE``; ``inf`` if not even the longest band does. Unlike
    the finest bar group, this is a continuous measure, and it works on any
    surface with detail at all periods.
    """
    truth = np.asarray(truth, dtype=float)
    t = np.fft.rfft(truth - truth.mean())
    e = np.array([np.fft.rfft(np.asarray(x, dtype=float) - np.mean(x)) for x in estimates])
    freq = np.fft.rfftfreq(truth.size, dx_nm)
    edges = np.geomspace(1.0 / longest_nm, 1.0 / (4 * dx_nm), bands + 1)
    finest = math.inf
    for lo, hi in zip(edges[:-1], edges[1:]):
        pick = (freq >= lo) & (freq < hi)
        if not pick.any():
            continue
        cross = np.sum((e[:, pick] * np.conj(t[pick])).real)
        power = math.sqrt(np.sum(np.abs(e[:, pick]) ** 2) * e.shape[0] * np.sum(np.abs(t[pick]) ** 2))
        if power == 0 or cross / power < COHERENCE_SHARE:
            break
        finest = 1.0 / hi
    return finest


def noise_limit_period(optics: l1.Optics1D, scan: l1.Scan1D, noise: l1.Noise1D, n_per_point,
                       contrast=0.8, mean=0.6):
    """Level 0 estimate of the finest period the noise allows, for a line scan.

    The same rule as :func:`ccdsr.resolution.recoverable_period`, in one
    dimension: a period ``L`` is judged over half a period of surface, which
    holds ``n * L / (2 p)`` readings, and counts as recoverable when the
    wave left after blurring stands above the noise of their average. The
    noise of one reading is photon noise at the mean brightness plus read
    noise. This is a rule of thumb for scale, not a prediction of what a
    particular reconstruction shows.
    """
    from scipy.optimize import brentq

    aperture = optics.pitch_nm if optics.aperture_nm is None else optics.aperture_nm
    light = noise.full_e * aperture / optics.pitch_nm
    sigma = math.sqrt((light * mean if noise.photon else 0.0) + noise.read_e ** 2)
    smear = scan.exposure_fraction * scan.shift_px * optics.pitch_nm

    def margin(log_period):
        period = math.exp(log_period)
        h = abs(complex(l1.transfer(np.array([1.0 / period]), optics, smear, scan.code)[0]))
        n_cell = n_per_point * period / (2 * optics.pitch_nm)
        return math.log(h * 0.5 * contrast * light / sigma * math.sqrt(n_cell) + 1e-300)

    lo, hi = math.log(10.0), math.log(1e9)
    if margin(hi) < 0:
        return math.inf
    if margin(lo) > 0:
        return math.exp(lo)
    return math.exp(brentq(margin, lo, hi))


SMOOTHNESS_LADDER = tuple(10.0 ** -k for k in range(0, 9))
TUNING_SEEDS = (1000, 1001, 1002)   # the smoothing is chosen on runs that are not scored
TUNED_OPTIONS = ("smoothness", "noise_to_signal")


def tuned(approach: ap.Approach, scene, optics, scan, noise, seeds=TUNING_SEEDS):
    """The approach with the strength of its smoothing chosen for these settings.

    More readings lower the noise, and a reconstruction can then smooth less
    and show finer detail. An approach file fixes one strength, which suits
    one number of readings. Here the strength (the option ``smoothness`` or
    ``noise_to_signal``) is tried over a ladder of powers of ten on separate
    runs and the one with the lowest median error against the true surface
    is kept. The truth is used to choose, so the result is the best this
    method can do, which an instrument would have to approach by another
    rule (for instance from its measured noise). Approaches with neither
    option are returned unchanged. Returns ``(approach, strength or None)``.
    """
    import inspect

    options = inspect.signature(ap.RECONSTRUCTIONS[approach.method].fn).parameters
    name = next((o for o in TUNED_OPTIONS if o in options), None)
    if name is None:
        return approach, None
    runs = [l1.simulate(scene.surface, scene.dx_nm, optics, scan, noise, seed=seed) for seed in seeds]
    best = None
    for value in SMOOTHNESS_LADDER:
        trial = dataclasses.replace(approach, options={**approach.options, name: value})
        errors = []
        for fr in runs:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                estimate, positions = ap.reconstruct(trial, scene, fr)
            errors.append(cp.score(scene, fr, estimate, positions,
                                   ap.believed_frames(trial, fr).positions_nm)["rms_error"])
        error = float(np.median(errors))
        if best is None or error < best[0]:
            best = (error, value, trial)
    return best[2], best[1]


def sweep(approach: ap.Approach, scene_name="random_layout", ways=WAYS, frames=FRAMES, seeds=(0, 1, 2, 3, 4),
          tune=True, tuning_seeds=TUNING_SEEDS):
    """Run one approach at every oversampling level. Returns a list of records.

    The approach's own scan and noise settings are the starting point; only
    the number of frames, and for ``same-time`` the light per frame and for
    ``repeat`` the step, are changed. With ``tune`` the strength of the
    smoothing is chosen at every level (:func:`tuned`).
    """
    given = approach
    scene = ap.get_scene(scene_name)
    approach.check(scene)
    optics, base_scan, base_noise = ap._build(approach, ap.Condition("as set"))
    records = []
    for way in ways:
        for n in frames:
            scan, noise = scan_for(way, n, base_scan, base_noise)
            approach, smoothness = tuned(given, scene, optics, scan, noise, tuning_seeds) if tune else (given, None)
            estimates, errors, finest = [], [], []
            first = None
            for seed in seeds:
                fr = l1.simulate(scene.surface, scene.dx_nm, optics, scan, noise, seed=seed)
                first = fr if first is None else first
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    estimate, positions = ap.reconstruct(approach, scene, fr)
                believed = ap.believed_frames(approach, fr).positions_nm
                scores = cp.score(scene, fr, estimate, positions, believed)
                moved, _ = cp.align_to_truth(np.asarray(estimate, dtype=float), scene.surface,
                                             cp.ALIGN_PX * optics.pitch_nm / scene.dx_nm)
                estimates.append(moved)
                errors.append(scores["rms_error"])
                if scores["has_bars"]:
                    finest.append(math.inf if scores["finest_period_nm"] is None else scores["finest_period_nm"])
            per_point = readings_per_point(first)
            records.append({
                "approach": approach.name, "smoothness": smoothness, "scene": scene.name, "way": way, "frames": int(n),
                "readings_per_point": per_point,
                "distinct_positions_per_pixel": distinct_positions_per_pixel(first),
                "light_per_reading_e": float(noise.full_e),
                "light_per_point_e": float(noise.full_e * per_point),
                "scan_time": float(n / REFERENCE_FRAMES if way != "same-time" else 1.0),
                "rms_error": float(np.median(errors)),
                "recovered_period_nm": recovered_period(estimates, scene.surface, scene.dx_nm),
                "finest_bar_period_nm": (float(np.percentile(finest, 50, method="higher")) if finest else None),
                "level0_period_nm": noise_limit_period(optics, scan, noise, per_point),
            })
    return records


# --------------------------------------------------------------- reporting

def _nm(value):
    return "none" if value is None or math.isinf(value) else f"{value:,.0f}"


def tables_markdown(records, seeds):
    """One table per approach, scene and way of getting more readings."""
    lines, number = [], 0
    keys = []
    for r in records:
        key = (r["approach"], r["scene"], r["way"])
        if key not in keys:
            keys.append(key)
    for approach, scene, way in keys:
        number += 1
        bars = any(r["finest_bar_period_nm"] is not None for r in records
                   if (r["approach"], r["scene"], r["way"]) == (approach, scene, way))
        head = ["Frames", "Readings per point", "Different positions per pixel", "Light per reading (electrons)",
                "Scan time (relative)", "Smoothing chosen", "Error (rms, reflectance)", "Finest period recovered (nm)"]
        if bars:
            head.append("Finest bar period shown (nm)")
        head.append("Level 0 estimate (nm)")
        lines += ["| " + " | ".join(head) + " |", "|" + "---:|" * len(head)]
        for r in records:
            if (r["approach"], r["scene"], r["way"]) != (approach, scene, way):
                continue
            row = [f"{r['frames']:,}", f"{r['readings_per_point']:,.1f}", f"{r['distinct_positions_per_pixel']:,.0f}",
                   f"{r['light_per_reading_e']:,.0f}", f"{r['scan_time']:.3g}",
                   "as given" if r["smoothness"] is None else f"{r['smoothness']:.0e}", f"{r['rms_error']:.3f}",
                   _nm(r["recovered_period_nm"])]
            if bars:
                row.append(_nm(r["finest_bar_period_nm"]))
            row.append(_nm(r["level0_period_nm"]))
            lines.append("| " + " | ".join(row) + " |")
        lines += ["", f"*Table O{number}. Approach `{approach}` on scene `{scene}`, readings added the `{way}` way. "
                      f"Simulated, level 1; median of {len(seeds)} runs, and the period recovered is taken over all "
                      f"{len(seeds)} together. The last column is a level 0 rule of thumb (Derived here).*", ""]
    return "\n".join(lines)


def figure(records, path, title=None):
    """Error and finest period recovered against readings per point."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams["svg.hashsalt"] = "oversampling"
    ink, paper = "#1f2430", "#fcfcfa"
    styles = {"more-time": "-", "same-time": "--", "repeat": ":"}
    names = list(dict.fromkeys(r["approach"] for r in records))
    fig, (left, right) = plt.subplots(1, 2, figsize=(11, 4.4), facecolor=paper)
    for k, name in enumerate(names):
        colour = plt.cm.tab10(k % 10)
        for way in dict.fromkeys(r["way"] for r in records):
            mine = [r for r in records if r["approach"] == name and r["way"] == way]
            x = [r["readings_per_point"] for r in mine]
            left.plot(x, [r["rms_error"] for r in mine], styles[way], color=colour, marker="o", ms=3, lw=1.2,
                      label=f"{name}, {way}")
            y = [r["recovered_period_nm"] if math.isfinite(r["recovered_period_nm"]) else np.nan for r in mine]
            right.plot(x, y, styles[way], color=colour, marker="o", ms=3, lw=1.2)
    for ax, label in ((left, "error against the true surface (rms, reflectance)"),
                      (right, "finest period recovered (nm)")):
        ax.set_facecolor(paper)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("readings per point of the surface", fontsize=9)
        ax.set_ylabel(label, fontsize=9)
        ax.grid(True, which="both", lw=0.3, color="#cccccc")
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    left.legend(frameon=False, fontsize=7.5)
    fig.suptitle(title or "Result against the number of readings of each point (lower is better)",
                 x=0.01, ha="left", fontsize=11, color=ink)
    fig.tight_layout()
    path = Path(path)
    fig.savefig(path.with_suffix(".svg"), metadata={"Date": None})
    fig.savefig(path.with_suffix(".png"), dpi=150, metadata={"Software": None})
    plt.close(fig)


def _rounded(value):
    if isinstance(value, float):
        return None if math.isinf(value) or math.isnan(value) else float(f"{value:.6g}")
    return value


def write_results(records, out_dir, seeds):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stable = [{k: _rounded(v) for k, v in r.items()} for r in records]
    (out / "results.json").write_text(json.dumps({"code_version": cp._code_version(), "seeds": list(seeds),
                                                  "records": stable}, indent=1) + "\n")
    (out / "tables.md").write_text(tables_markdown(records, seeds))
    figure(records, out / "oversampling")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("approaches", nargs="+", help="approach files (TOML)")
    parser.add_argument("--scene", default="random_layout", help="test surface (default: random_layout)")
    parser.add_argument("--set", action="append", default=[], metavar="PART.SETTING=VALUE",
                        help="change one setting of every approach; may be repeated")
    parser.add_argument("--ways", default=",".join(WAYS), help="comma-separated: " + ", ".join(WAYS))
    parser.add_argument("--frames", default=",".join(str(n) for n in FRAMES), help="comma-separated frame counts")
    parser.add_argument("--seeds", type=int, default=5, help="runs per level (default: 5)")
    parser.add_argument("--fixed", action="store_true",
                        help="keep each approach's own smoothing instead of choosing it at every level")
    parser.add_argument("--out", required=True, help="folder to write results into")
    args = parser.parse_args(argv)
    seeds = tuple(range(args.seeds))
    records = []
    try:
        for path in args.approaches:
            approach = ap.load_approach(path, args.set)
            records += sweep(approach, args.scene, tuple(args.ways.split(",")),
                             tuple(int(n) for n in args.frames.split(",")), seeds, tune=not args.fixed)
    except (ap.InvalidApproach, ValueError, TypeError, OSError) as reason:
        raise SystemExit(f"cannot run: {reason}")
    write_results(records, args.out, seeds)
    print(tables_markdown(records, seeds))
    print(f"{len(records)} levels written to {args.out}")


if __name__ == "__main__":
    main()
