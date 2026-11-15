"""Run several approaches on the same scenes and conditions and compare them.

A comparison is a TOML file listing approach files, scenes, conditions and
seeds. Every approach is run on every scene under every condition with the
same seeds, each result is scored against the truth with the same measures,
and one set of tables and figures is written::

    python -m ccdsr.compare comparisons/level1-first.toml --out results/level1-first

See ``docs/comparison.md``.
"""

from __future__ import annotations

import argparse
import json
import multiprocessing
import os
import subprocess
import time
import tomllib
import warnings
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import approaches as ap
from . import level1 as l1

CONTRAST_SHARE = 0.5          # a bar group counts as shown from this share of its true pattern ...
CONTRAST_CEILING = 1.5        # ... up to this one: more than that is noise or ringing, not the bars
LOST_NM = 100.0               # frame positions wrong by more than this count as a failed run
ALIGN_PX = 3.0                # scoring may slide a reconstruction by at most this many pixels


# ----------------------------------------------------------------- scoring

def align_to_truth(estimate, truth, max_cells):
    """Slide a reconstruction along the surface to where it matches the truth best.

    A method that is not told the positions cannot know where the whole
    picture sits, so every reconstruction is allowed the same freedom before
    it is scored: one shift, of at most ``max_cells`` grid cells, found from
    the peak of the cross-correlation and applied to a fraction of a cell.
    Returns the shifted estimate and the shift in cells.
    """
    e, t = np.fft.fft(estimate - np.mean(estimate)), np.fft.fft(truth - np.mean(truth))
    corr = np.fft.ifft(t * np.conj(e)).real
    n = corr.size
    lags = np.arange(-int(max_cells), int(max_cells) + 1)
    values = corr[lags % n]
    k = int(np.argmax(values))
    shift = float(lags[k])
    if 0 < k < values.size - 1:
        a, b, c = values[k - 1], values[k], values[k + 1]
        if a - 2 * b + c < 0:
            shift += 0.5 * (a - c) / (a - 2 * b + c)
    moved = np.fft.ifft(np.fft.fft(estimate) * np.exp(-2j * np.pi * np.fft.fftfreq(n) * shift)).real
    return moved, shift


def _contrast_share(estimate, truth, group, dx_nm):
    """How much of a bar group's true pattern an estimate shows, as a share of the truth.

    The estimate and the truth are both projected onto a wave of the group's
    period over the middle of the group, and the part of the estimate's wave
    that is in step with the truth's is divided by the truth's. 1 is perfect.
    Bars drawn in the wrong place count for less or negative, and noise that
    happens to contain the period cannot count for more than its in-step part.
    """
    period, start, stop = group
    per = period / dx_nm
    cycles = int((stop - start) / per) - 2
    a = start + int(round(per))
    window = slice(a, a + int(round(cycles * per)))
    wave = np.exp(-2j * np.pi * np.arange(window.stop - window.start) / per)
    est, true = np.mean(estimate[window] * wave), np.mean(truth[window] * wave)
    return float((est * np.conj(true)).real / abs(true) ** 2)


def score(scene: ap.Scene, frames: l1.Frames1D, estimate, positions, believed):
    """The measures every result is judged by. All are against the truth."""
    max_cells = ALIGN_PX * frames.optics.pitch_nm / scene.dx_nm
    aligned, shift = align_to_truth(np.asarray(estimate, dtype=float), scene.surface, max_cells)
    out = {"rms_error": float(np.sqrt(np.mean((aligned - scene.surface) ** 2))),
           "shift_nm": float(shift * scene.dx_nm),
           "contrast_share": None, "finest_period_nm": None, "wrong_material_percent": None}
    out["has_bars"] = bool(scene.groups)
    if scene.groups:
        shares = [_contrast_share(aligned, scene.surface, group, scene.dx_nm) for group in scene.groups]
        out["contrast_share"] = [float(s) for s in shares]
        finest = None
        for group, share in sorted(zip(scene.groups, shares), key=lambda gs: -gs[0][0]):
            if not CONTRAST_SHARE <= share <= CONTRAST_CEILING:
                break
            finest = group[0]
        out["finest_period_nm"] = float(finest) if finest else None      # None: not even the coarsest group
    if scene.levels is not None:
        middle = 0.5 * (scene.levels[0] + scene.levels[1])
        high = scene.surface > middle
        missed = np.mean(aligned[high] <= middle) if high.any() else 0.0
        invented = np.mean(aligned[~high] > middle) if (~high).any() else 0.0
        out["wrong_material_percent"] = float(100 * 0.5 * (missed + invented))
    used = believed if positions is None else positions
    out["position_error_nm"] = l1.position_error(frames, used)
    return out


# ----------------------------------------------------------------- running

@dataclass(frozen=True)
class Comparison:
    name: str
    description: str
    approaches: tuple
    scenes: tuple
    conditions: tuple
    seeds: tuple


def load_comparison(path) -> Comparison:
    path = Path(path)
    data = tomllib.loads(path.read_text())
    root = path.parent
    found = []
    for entry in data["approaches"]:
        found.append(ap.load_approach(entry if Path(entry).is_absolute() else _find(root, entry)))
    names = [a.name for a in found]
    if len(set(names)) != len(names):
        raise ap.InvalidApproach(f"{path.name}: approach names are not unique: {names}")
    conditions = tuple(ap.Condition(c["name"], c.get("description", ""), dict(c.get("optics", {})),
                                    dict(c.get("scan", {})), dict(c.get("noise", {})))
                       for c in data["conditions"])
    return Comparison(data["name"], data.get("description", ""), tuple(found), tuple(data["scenes"]),
                      conditions, tuple(int(s) for s in data["seeds"]))


def _find(root, entry):
    """An approach path is looked for beside the comparison file, then one folder up."""
    for base in (root, root.parent):
        if (base / entry).exists():
            return base / entry
    raise FileNotFoundError(f"approach file {entry!r} not found from {root}")


def run_one(approach: ap.Approach, scene_name, condition: ap.Condition, seed):
    """One approach on one scene under one condition with one seed. Returns a record."""
    record = {"approach": approach.name, "scene": scene_name, "condition": condition.name, "seed": int(seed)}
    scene = ap.get_scene(scene_name)
    try:
        frames = ap.simulate(approach, scene, condition, seed)
    except ap.InvalidApproach as reason:
        return {**record, "refused": str(reason)}
    believed = ap.believed_frames(approach, frames).positions_nm
    started = time.perf_counter()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        estimate, positions = ap.reconstruct(approach, scene, frames)
    record["seconds"] = time.perf_counter() - started
    record["warnings"] = sorted({str(w.message)[:120] for w in caught})
    record["readings"] = int(frames.readings.size)
    # readings of each point of the surface, counted by pixel pitch (see ccdsr.oversampling)
    record["readings_per_point"] = float(frames.readings.size * frames.optics.pitch_nm
                                         / (frames.n_grid * frames.dx_nm))
    record.update(score(scene, frames, estimate, positions, believed))
    return record


def _job(args):
    return run_one(*args)


def run(comparison: Comparison, workers=1):
    """Every approach on every scene under every condition with every seed."""
    jobs = [(a, s, c, seed) for a in comparison.approaches for s in comparison.scenes
            for c in comparison.conditions for seed in comparison.seeds]
    if workers > 1:
        # Fresh processes with one maths thread each. Several processes that each start a
        # thread per core get in each other's way and can run hundreds of times slower.
        limits = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
        before = {k: os.environ.get(k) for k in limits}
        os.environ.update({k: "1" for k in limits})
        try:
            with ProcessPoolExecutor(workers, mp_context=multiprocessing.get_context("spawn")) as pool:
                return list(pool.map(_job, jobs, chunksize=4))
        finally:
            for k, v in before.items():
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
    return [_job(j) for j in jobs]


# --------------------------------------------------------------- reporting

MEASURES = [
    ("rms_error", "median", "Error against the true surface (rms, reflectance), median", "{:.3f}"),
    ("rms_error", "worst", "Error against the true surface (rms, reflectance), worst run", "{:.3f}"),
    ("finest_period_nm", "median", "Finest bar period shown (nm), median; \"none\" if not even the coarsest", "{:,.0f}"),
    ("wrong_material_percent", "median", "Surface assigned to the wrong material (%, average of the two materials), "
                                         "median", "{:.1f}"),
    ("position_error_nm", "median", "Error of the frame positions used (nm, rms), median", "{:.1f}"),
    ("position_error_nm", "lost", f"Runs in which the frame positions used were wrong by more than {LOST_NM:.0f} nm "
                                  "rms (count)", "{:.0f}"),
]


def summarise(records, measure, how="median"):
    """One figure per cell over the seeds, as ``{(scene, approach, condition): float or "refused"}``.

    ``how`` is "median", "worst" (the largest) or "lost" (how many runs
    exceeded ``LOST_NM``). For the finest period, a run that showed no bar
    group counts as infinitely coarse, so a median can come out infinite.
    """
    cells = {}
    for r in records:
        key = (r["scene"], r["approach"], r["condition"])
        if "refused" in r:
            cells[key] = "refused"
            continue
        value = r.get(measure)
        if measure == "finest_period_nm" and r.get("has_bars") and value is None:
            value = np.inf
        if value is not None:
            cells.setdefault(key, []).append(value)
    # the finest period is one of a few fixed values, so its median is taken as the coarser of
    # the two middle runs when their number is even, never a value between two bar groups
    median = (lambda v: np.percentile(v, 50, method="higher")) if measure == "finest_period_nm" else np.median
    pick = {"median": median, "worst": np.max, "lost": lambda v: np.sum(np.array(v) > LOST_NM)}[how]
    return {k: (v if isinstance(v, str) else float(pick(v))) for k, v in cells.items()}


def tables_markdown(comparison: Comparison, records):
    """The result tables as Markdown text. The same records always give the same text."""
    lines = []
    number = 0
    conditions = [c.name for c in comparison.conditions]
    solvers = {a.name for a in comparison.approaches if a.positions == "unknown"}
    for scene in comparison.scenes:
        for measure, how, title, fmt in MEASURES:
            cells = summarise(records, measure, how)
            chosen = [a for a in comparison.approaches if measure != "position_error_nm" or a.name in solvers]
            rows = [(a.name, [cells.get((scene, a.name, c)) for c in conditions]) for a in chosen]
            if not any(isinstance(v, float) for _, values in rows for v in values):
                continue
            number += 1
            lines += [f"| Approach | {' | '.join(conditions)} |", "|---|" + "---:|" * len(conditions)]
            for name, values in rows:
                shown = ["not run" if v == "refused" else "" if v is None else "none" if np.isinf(v)
                         else fmt.format(v) for v in values]
                lines.append(f"| `{name}` | {' | '.join(shown)} |")
            note = " Only approaches with no position readout are listed." if measure == "position_error_nm" else ""
            lines += ["", f"*Table R{number}. Scene `{scene}`: {title[0].lower() + title[1:]}. Simulated, level 1; "
                          f"{len(comparison.seeds)} runs per cell, one per seed. Columns are the conditions.{note}*", ""]
    refused = sorted({(r["approach"], r["scene"], r["refused"]) for r in records if "refused" in r})
    if refused:
        number += 1
        lines += ["| Approach | Scene | Why it was not run |", "|---|---|---|"]
        lines += [f"| `{a}` | `{s}` | {why.split(': ', 1)[-1]} |" for a, s, why in refused]
        lines += ["", f"*Table R{number}. Combinations that were refused, with the reason.*", ""]
    number += 1
    lines += ["| Approach | Readings used per run | Readings of each point of the surface | Runs that gave a warning |",
              "|---|---:|---:|---:|"]
    for a in comparison.approaches:
        mine = [r for r in records if r["approach"] == a.name and "refused" not in r]
        if mine:
            warned = sum(bool(r["warnings"]) for r in mine)
            per_point = sorted({round(r["readings_per_point"]) for r in mine if "readings_per_point" in r})
            shown = "" if not per_point else f"{per_point[0]:,}" if len(per_point) == 1 \
                else f"{per_point[0]:,} to {per_point[-1]:,}"
            lines.append(f"| `{a.name}` | {mine[0]['readings']:,} | {shown} | {warned} of {len(mine)} |")
    lines += ["", f"*Table R{number}. Data used by each approach, and solver warnings. The readings of each point "
                  "are the readings times the pixel spacing divided by the length of the test surface, so they "
                  "differ between surfaces of different length; the range over the scenes is given. How the "
                  "result changes with this number is the subject of the oversampling page.*", ""]
    return "\n".join(lines)


def timings_markdown(comparison: Comparison, records):
    """Typical computing time per approach. Differs from run to run and machine to machine."""
    lines = ["| Approach | Typical time for one reconstruction (s) |", "|---|---:|"]
    for a in comparison.approaches:
        mine = [r["seconds"] for r in records if r["approach"] == a.name and "refused" not in r]
        if mine:
            lines.append(f"| `{a.name}` | {float(f'{np.median(mine):.1g}'):g} |")
    return "\n".join(lines) + "\n"


def figures(comparison: Comparison, records, out_dir):
    """A grid of error by approach and condition, and reconstructions beside the truth."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams["svg.hashsalt"] = comparison.name
    ink, paper = "#1f2430", "#fcfcfa"
    conditions = [c.name for c in comparison.conditions]
    names = [a.name for a in comparison.approaches]
    cells = summarise(records, "rms_error", "median")
    fig, axes = plt.subplots(1, len(comparison.scenes), figsize=(4.1 * len(comparison.scenes) + 2.2, 0.42 * len(names) + 2.3),
                             sharey=True, facecolor=paper)
    axes = np.atleast_1d(axes)
    for ax, scene in zip(axes, comparison.scenes):
        grid = np.array([[cells.get((scene, n, c)) if isinstance(cells.get((scene, n, c)), float) else np.nan
                          for c in conditions] for n in names])
        image = ax.imshow(grid, cmap="viridis_r", vmin=0, vmax=0.4, aspect="auto")
        for i in range(grid.shape[0]):
            for j in range(grid.shape[1]):
                text = "not run" if np.isnan(grid[i, j]) else f"{grid[i, j]:.2f}"
                ax.text(j, i, text, ha="center", va="center", fontsize=7.5,
                        color="white" if (not np.isnan(grid[i, j]) and grid[i, j] > 0.2) else ink)
        ax.set_xticks(range(len(conditions)), conditions, rotation=35, ha="right", fontsize=8)
        ax.set_yticks(range(len(names)), names, fontsize=8)
        ax.set_title(f"scene: {scene}", loc="left", fontsize=9.5, color=ink)
    fig.colorbar(image, ax=axes.tolist(), fraction=0.025, pad=0.01, label="error against the true surface (rms)")
    fig.suptitle("Error of each approach under each condition (lower is better)", x=0.01, ha="left",
                 fontsize=11, color=ink)
    _save(fig, out_dir, "error-grid")

    # reconstructions beside the truth: first scene, first seed, first two conditions
    scene = ap.get_scene(comparison.scenes[0])
    shown = list(comparison.conditions[:2])
    fig, axes = plt.subplots(1, len(shown), figsize=(6.2 * len(shown), 0.72 * len(names) + 2.0), sharey=True,
                             facecolor=paper)
    x = np.arange(scene.surface.size) * scene.dx_nm / 1e3
    for ax, condition in zip(np.atleast_1d(axes), shown):
        ax.set_facecolor(paper)
        ax.plot(x, scene.surface + 1.7 * len(names), color=ink, lw=1.0)
        ax.text(x[0], 1.7 * len(names) + 1.3, "true surface", fontsize=7.5, color=ink)
        for k, approach in enumerate(comparison.approaches):
            base = 1.7 * (len(names) - 1 - k)
            record = run_one(approach, scene.name, condition, comparison.seeds[0])
            if "refused" in record:
                ax.text(x[0], base + 0.4, f"{approach.name}: not run", fontsize=7.5, color="#888888")
                continue
            frames = ap.simulate(approach, scene, condition, comparison.seeds[0])
            estimate, _ = ap.reconstruct(approach, scene, frames)
            moved, _ = align_to_truth(np.asarray(estimate, dtype=float), scene.surface,
                                      ALIGN_PX * frames.optics.pitch_nm / scene.dx_nm)
            ax.plot(x, np.clip(moved, -0.15, 1.25) + base, color=plt.cm.tab10(k % 10), lw=0.9)
            ax.text(x[0], base + 1.3, approach.name, fontsize=7.5, color=ink)
        ax.set_title(f"condition: {condition.name}", loc="left", fontsize=9.5, color=ink)
        ax.set_xlabel("position along the scan (µm)", fontsize=9)
        ax.set_yticks([])
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
    fig.suptitle(f"Reconstructions of scene '{scene.name}' beside the truth, seed {comparison.seeds[0]} "
                 "(each trace offset upward)", x=0.01, ha="left", fontsize=11, color=ink)
    _save(fig, out_dir, "reconstructions")


def _save(fig, out_dir, name):
    import matplotlib.pyplot as plt
    fig.savefig(Path(out_dir) / f"{name}.svg", metadata={"Date": None}, bbox_inches="tight")
    fig.savefig(Path(out_dir) / f"{name}.png", dpi=150, bbox_inches="tight", metadata={"Software": None})
    plt.close(fig)


def _rounded(value, figures=6):
    if isinstance(value, float):
        return float(f"{value:.{figures}g}")
    if isinstance(value, list):
        return [_rounded(v, figures) for v in value]
    return value


def _code_version():
    """The commit the code was at, with "-dirty" if code or inputs had uncommitted changes."""
    def git(*args):
        return subprocess.run(["git", *args], capture_output=True, text=True, check=True,
                              cwd=Path(__file__).parent.parent).stdout.strip()
    try:
        changed = git("status", "--porcelain", "--", "ccdsr", "approaches", "comparisons")
        return git("rev-parse", "--short", "HEAD") + ("-dirty" if changed else "")
    except Exception:
        return "unknown"


def write_results(comparison: Comparison, records, out_dir, comparison_text=""):
    """Write records, tables, figures and the inputs that produced them."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    # timings left out and numbers rounded, so that a rerun writes the same file
    stable = [{k: _rounded(v) for k, v in r.items() if k != "seconds"} for r in records]
    (out / "results.json").write_text(json.dumps(
        {"comparison": comparison.name, "description": comparison.description, "code_version": _code_version(),
         "approach_files": {a.name: a.source for a in comparison.approaches}, "comparison_file": comparison_text,
         "records": stable}, indent=1) + "\n")
    (out / "tables.md").write_text(tables_markdown(comparison, records))
    (out / "timings.md").write_text(timings_markdown(comparison, records))
    figures(comparison, records, out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("comparison", help="comparison file (TOML)")
    parser.add_argument("--out", required=True, help="folder to write results into")
    parser.add_argument("--workers", type=int, default=1, help="processes to spread the runs over")
    args = parser.parse_args(argv)
    comparison = load_comparison(args.comparison)
    records = run(comparison, args.workers)
    write_results(comparison, records, args.out, Path(args.comparison).read_text())
    print(f"{len(records)} runs written to {args.out}")


if __name__ == "__main__":
    main()
