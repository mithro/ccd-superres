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
    More frames with the same light in each, but the sensor does not move,
    so every frame lands on the same places. This is plain averaging: it
    lowers noise and adds no new positions.

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
BAND_HALF_WIDTH = 1.09        # the level 0 rule judges a period over a band this far either side
MIN_WAVES = 3                  # a band of periods must hold at least this many waves of the surface


def readings_per_point(frames: l1.Frames1D) -> float:
    """Average number of readings whose pixel covers a point of the surface.

    See :func:`ccdsr.level1.readings_per_point`, which this calls.
    """
    return l1.readings_per_point(frames)


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


def scan_for(way, n_frames, base: l1.Scan1D, base_noise: l1.Noise1D, surface_px=None):
    """The scan and noise settings for one oversampling level.

    ``surface_px`` is the length of the repeating test surface in pixel
    widths. It matters for ``repeat`` only. A sensor longer than the surface
    laps it, and its far pixels then land between its near ones, so that
    even a still sensor reads several places per pixel. To keep ``repeat``
    as plain averaging the sensor is cut to the pixels that fit on the
    surface once, and the number of frames is raised in proportion so that
    the number of readings stays about the same. Position errors are
    switched off too: a sensor that shakes is not held still.
    """
    if way not in WAYS:
        raise ValueError(f"unknown way {way!r}; known: {WAYS}")
    scan = dataclasses.replace(base, n_frames=int(n_frames))
    noise = base_noise
    if way == "repeat":
        pixels = base.n_pixels if surface_px is None else max(1, min(base.n_pixels, int(surface_px)))
        frames = max(1, int(round(n_frames * base.n_pixels / pixels)))
        scan = dataclasses.replace(scan, shift_px=0.0, jitter_px=0.0, wander_px=0.0, n_pixels=pixels,
                                   n_frames=frames)
    if way == "same-time":
        noise = dataclasses.replace(base_noise, full_e=base_noise.full_e * REFERENCE_FRAMES / n_frames)
    return scan, noise


def period_bands(n_grid, dx_nm, bands=28, longest_nm=8000.0, min_waves=MIN_WAVES):
    """The bands of periods used by :func:`recovered_period`, as ``(low, high)`` frequencies.

    The bands are equal steps of about 18 % in period from ``longest_nm``
    down to four grid cells. A surface of finite length holds only certain
    waves (one, two, three ... periods along its length), and a band with
    too few of them gives an unsteady answer, so neighbouring bands are
    joined until each holds at least ``min_waves``.
    """
    freq = np.fft.rfftfreq(n_grid, dx_nm)
    edges = np.geomspace(1.0 / longest_nm, 1.0 / (4 * dx_nm), bands + 1)
    out, low = [], edges[0]
    for high in edges[1:]:
        if np.count_nonzero((freq >= low) & (freq < high)) >= min_waves:
            out.append((float(low), float(high)))
            low = high
    return out


def recovered_period(estimates, truth, dx_nm, bands=28, longest_nm=8000.0):
    """Finest period down to which the reconstructions agree with the truth.

    The estimates (one per run) and the truth are split into waves. In each
    band of periods (:func:`period_bands`), the part of the estimates that
    is in step with the truth is divided by the geometric mean of the two
    strengths, which gives 1 for a perfect copy and about 0 for noise. The
    answer is the short end of the last band, going from long periods to
    short, that still reaches ``COHERENCE_SHARE``; ``inf`` if not even the
    longest band does.

    What the measure cannot do: it asks for agreement of a half, not
    for a faithful copy, so a reconstruction that is partly right in a band
    (for instance from readings too far apart to fix that period, helped by
    the smoothing) can pass. Mistakes that are the same in every run are not
    averaged away by having several runs. It moves in steps of one band, and
    with five runs neighbouring steps are not told apart reliably.
    """
    truth = np.asarray(truth, dtype=float)
    t = np.fft.rfft(truth - truth.mean())
    e = np.array([np.fft.rfft(np.asarray(x, dtype=float) - np.mean(x)) for x in estimates])
    freq = np.fft.rfftfreq(truth.size, dx_nm)
    finest = math.inf
    for lo, hi in period_bands(truth.size, dx_nm, bands, longest_nm):
        pick = (freq >= lo) & (freq < hi)
        cross = np.sum((e[:, pick] * np.conj(t[pick])).real)
        power = math.sqrt(np.sum(np.abs(e[:, pick]) ** 2) * e.shape[0] * np.sum(np.abs(t[pick]) ** 2))
        if power == 0 or cross / power < COHERENCE_SHARE:
            break
        finest = 1.0 / hi
    return finest


def noise_limit_period(optics: l1.Optics1D, scan: l1.Scan1D, noise: l1.Noise1D, n_per_point,
                       contrast=0.8, mean=0.6):
    """Level 0 estimate of the finest period the noise allows, for a line scan.

    The same kind of rule as :func:`ccdsr.resolution.recoverable_period`,
    in one dimension: a period ``L`` is judged over half a period of
    surface, which holds ``n * L / (2 p)`` readings, and counts as
    recoverable when the wave left after blurring stands above the noise of
    their average. The wave has half the ``contrast`` between the two
    materials as its height, and the noise of one reading is photon noise
    at the ``mean`` brightness plus read noise (the design's version takes
    full contrast and a fixed signal-to-noise).

    A pixel wipes out patterns that repeat a whole number of times across
    its opening, so the wave can sink below the noise, come back and sink
    again as the period shrinks. Two choices deal with that, both made to
    match :func:`recovered_period`. The strength of the wave is taken as
    its rms over a band of periods 18 % wide, so that a blind period of no
    width does not count as a failure. And the answer is the first period,
    going from coarse to fine, at which the wave sinks below the noise:
    detail beyond a failed band is not counted. It does not look at where the readings fall, so it is
    the same for a sensor held still. A rule of thumb for scale, not a
    prediction of what a particular reconstruction shows.
    """
    from scipy.optimize import brentq

    aperture = optics.pitch_nm if optics.aperture_nm is None else optics.aperture_nm
    light = noise.full_e * aperture / optics.pitch_nm
    sigma = math.sqrt((light * mean if noise.photon else 0.0) + noise.read_e ** 2)
    smear = scan.exposure_fraction * scan.shift_px * optics.pitch_nm

    def margin(log_period):
        period = math.exp(log_period)
        around = period * np.geomspace(1 / BAND_HALF_WIDTH, BAND_HALF_WIDTH, 15)
        h = math.sqrt(float(np.mean(np.abs(l1.transfer(1.0 / around, optics, smear, scan.code)) ** 2)))
        n_cell = n_per_point * period / (2 * optics.pitch_nm)
        return math.log(h * 0.5 * contrast * light / sigma * math.sqrt(n_cell) + 1e-300)

    grid = np.linspace(math.log(1e9), math.log(10.0), 6000)       # coarse to fine, steps of 0.3 %
    values = np.array([margin(g) for g in grid])
    if values[0] < 0:
        return math.inf
    below = np.nonzero(values < 0)[0]
    if below.size == 0:
        return math.exp(grid[-1])
    k = int(below[0])
    return math.exp(brentq(margin, grid[k], grid[k - 1]))


SMOOTHNESS_LADDER = tuple(10.0 ** -k for k in range(-2, 9))
TUNING_SEEDS = (1000, 1001, 1002)   # the smoothing is chosen on runs that are not scored
TUNED_OPTIONS = ("smoothness", "noise_to_signal")


def tuned(approach: ap.Approach, scene, optics, scan, noise, seeds=TUNING_SEEDS):
    """The approach with the strength of its smoothing chosen for these settings.

    More readings lower the noise, and a reconstruction can then smooth less
    and show finer detail. An approach file fixes one strength, which suits
    one number of readings. Here the strength (the option ``smoothness`` or
    ``noise_to_signal``) is tried over a ladder of powers of ten on separate
    runs and the one with the lowest median error against the true surface
    is kept. The truth is used to choose, so the result is close to the
    lowest error this method can reach, which an instrument would have to
    approach by another rule (for instance from its measured noise). It is
    the error that is made small, not the finest period recovered. Approaches with neither
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
            scan, noise = scan_for(way, n, base_scan, base_noise, scene.surface.size * scene.dx_nm / optics.pitch_nm)
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
                "approach": approach.name, "smoothness": smoothness, "scene": scene.name, "way": way,
                "level": int(n), "frames": int(scan.n_frames), "pixels": int(scan.n_pixels),
                "readings_per_point": per_point,
                "distinct_positions_per_pixel": distinct_positions_per_pixel(first),
                "light_per_reading_e": float(noise.full_e),
                "light_per_point_e": float(noise.full_e * per_point),
                "scan_time": float(scan.n_frames / REFERENCE_FRAMES if way != "same-time" else 1.0),
                "rms_error": float(np.median(errors)),
                "recovered_period_nm": recovered_period(estimates, scene.surface, scene.dx_nm),
                "finest_bar_period_nm": (float(np.percentile(finest, 50, method="higher")) if finest else None),
                "level0_period_nm": noise_limit_period(optics, scan, noise, per_point),
            })
    return records


# --------------------------------------------------------------- reporting

def _nm(value):
    return "none" if value is None or math.isinf(value) else f"{value:,.0f}"


def tables_markdown(records, seeds, first=1):
    """One table per approach, scene and way of getting more readings, numbered from ``first``."""
    lines, number = [], first - 1
    keys = []
    for r in records:
        key = (r["approach"], r["scene"], r["way"])
        if key not in keys:
            keys.append(key)
    for approach, scene, way in keys:
        number += 1
        bars = any(r["finest_bar_period_nm"] is not None for r in records
                   if (r["approach"], r["scene"], r["way"]) == (approach, scene, way))
        head = ["Frames", "Pixels", "Readings per point", "Different positions per pixel", "Light per reading (electrons)",
                "Scan time (relative)", "Smoothing chosen", "Error (rms, reflectance)", "Finest period recovered (nm)"]
        if bars:
            head.append("Finest bar period shown (nm)")
        head.append("Level 0 estimate (nm)")
        lines += ["| " + " | ".join(head) + " |", "|" + "---:|" * len(head)]
        for r in records:
            if (r["approach"], r["scene"], r["way"]) != (approach, scene, way):
                continue
            row = [f"{r['frames']:,}", f"{r['pixels']:,}", f"{r['readings_per_point']:,.1f}", f"{r['distinct_positions_per_pixel']:,.0f}",
                   f"{r['light_per_reading_e']:,.0f}", f"{r['scan_time']:.3g}",
                   "as given" if r["smoothness"] is None else f"{r['smoothness']:.0e}", f"{r['rms_error']:.3f}",
                   _nm(r["recovered_period_nm"])]
            if bars:
                row.append(_nm(r["finest_bar_period_nm"]))
            row.append(_nm(r["level0_period_nm"]))
            lines.append("| " + " | ".join(row) + " |")
        lines += ["", f"*Table O{number}. Approach `{approach}` on scene `{scene}`, readings added the `{way}` way. "
                      f"Simulated, level 1; median of {len(seeds)} runs, and the period recovered is taken over all "
                      f"{len(seeds)} together. The smoothing is the one with the lowest error on separate runs. "
                      f"The last column is a level 0 rule of thumb (Derived here), which does not look at where "
                      f"the readings fall.*", ""]
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
