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

CONTRAST_SHARE = 0.5          # a bar group counts as resolved at this share of its true contrast
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


def score(scene: ap.Scene, frames: l1.Frames1D, estimate, positions, believed):
    """The measures every result is judged by. All are against the truth."""
    max_cells = ALIGN_PX * frames.optics.pitch_nm / scene.dx_nm
    aligned, shift = align_to_truth(np.asarray(estimate, dtype=float), scene.surface, max_cells)
    out = {"rms_error": float(np.sqrt(np.mean((aligned - scene.surface) ** 2))),
           "shift_nm": float(shift * scene.dx_nm),
           "contrast_share": None, "finest_period_nm": None, "wrong_material_percent": None}
    if scene.groups:
        shares = []
        for group in scene.groups:
            true = l1.bar_contrast(scene.surface, group, scene.dx_nm)
            shares.append(l1.bar_contrast(aligned, group, scene.dx_nm) / true)
        out["contrast_share"] = [float(s) for s in shares]
        finest = None
        for group, share in sorted(zip(scene.groups, shares), key=lambda gs: -gs[0][0]):
            if share < CONTRAST_SHARE:
                break
            finest = group[0]
        # nothing resolved is recorded as twice the coarsest period, so that medians stay defined
        out["finest_period_nm"] = float(finest) if finest else 2.0 * max(g[0] for g in scene.groups)
    if scene.levels is not None:
        middle = 0.5 * (scene.levels[0] + scene.levels[1])
        out["wrong_material_percent"] = float(100 * np.mean((aligned > middle) != (scene.surface > middle)))
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
    ("rms_error", "Error against the true surface (rms, reflectance)", "{:.3f}"),
    ("finest_period_nm", "Finest bar period shown at half its true contrast or better (nm)", "{:,.0f}"),
    ("wrong_material_percent", "Surface assigned to the wrong material (%)", "{:.1f}"),
    ("position_error_nm", "Error of the frame positions used (nm, rms)", "{:.1f}"),
]


def summarise(records, measure):
    """Median over seeds of one measure, as ``{(scene, approach, condition): value or None or str}``."""
    cells = {}
    for r in records:
        key = (r["scene"], r["approach"], r["condition"])
        if "refused" in r:
            cells[key] = "refused"
        elif r.get(measure) is not None:
            cells.setdefault(key, []).append(r[measure])
    return {k: (v if isinstance(v, str) else float(np.median(v))) for k, v in cells.items()}


def tables_markdown(comparison: Comparison, records):
    """All result tables as Markdown text."""
    lines = []
    number = 0
    conditions = [c.name for c in comparison.conditions]
    for scene in comparison.scenes:
        for measure, title, fmt in MEASURES:
            cells = summarise(records, measure)
            rows = [(a.name, [cells.get((scene, a.name, c)) for c in conditions]) for a in comparison.approaches]
            if not any(isinstance(v, float) for _, values in rows for v in values):
                continue
            number += 1
            lines += [f"| Approach | {' | '.join(conditions)} |", "|---|" + "---:|" * len(conditions)]
            for name, values in rows:
                shown = ["not run" if v == "refused" else "" if v is None else fmt.format(v) for v in values]
                lines.append(f"| `{name}` | {' | '.join(shown)} |")
            lines += ["", f"*Table R{number}. Scene `{scene}`: {title[0].lower() + title[1:]}. Simulated, level 1; "
                          f"median of {len(comparison.seeds)} seeds. Columns are the conditions.*", ""]
    refused = sorted({(r["approach"], r["scene"], r["refused"]) for r in records if "refused" in r})
    if refused:
        number += 1
        lines += ["| Approach | Scene | Why it was not run |", "|---|---|---|"]
        lines += [f"| `{a}` | `{s}` | {why.split(': ', 1)[-1]} |" for a, s, why in refused]
        lines += ["", f"*Table R{number}. Combinations that were refused, with the reason.*", ""]
    number += 1
    lines += ["| Approach | Typical time for one reconstruction (s) | Readings used | Runs that gave a warning |",
              "|---|---:|---:|---:|"]
    for a in comparison.approaches:
        mine = [r for r in records if r["approach"] == a.name and "refused" not in r]
        if mine:
            seconds = float(np.median([r["seconds"] for r in mine]))
            warned = sum(bool(r["warnings"]) for r in mine)
            lines.append(f"| `{a.name}` | {float(f'{seconds:.1g}'):g} | {mine[0]['readings']:,} | "
                         f"{warned} of {len(mine)} |")
    lines += ["", f"*Table R{number}. Cost of each approach. Times are for one core of the machine that ran the "
                  "comparison and are rounded to one figure.*", ""]
    return "\n".join(lines)


def figures(comparison: Comparison, records, out_dir):
    """A grid of error by approach and condition, and reconstructions beside the truth."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams["svg.hashsalt"] = comparison.name
    ink, paper = "#1f2430", "#fcfcfa"
    conditions = [c.name for c in comparison.conditions]
    names = [a.name for a in comparison.approaches]
    cells = summarise(records, "rms_error")
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
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                              cwd=Path(__file__).parent, check=True).stdout.strip()
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
