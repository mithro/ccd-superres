"""Run the oversampling study and draw the figures for docs/oversampling.md.

Run from the repository root:

    python docs/diagrams/make_oversampling_diagrams.py            # figures from the stored runs
    python docs/diagrams/make_oversampling_diagrams.py --rerun    # run the study again first (about 15 minutes)

The runs are stored in ``results/oversampling/runs.json`` with their tables
in ``results/oversampling/tables.md``. Figures are written next to this
file as SVG (used by the page) and PNG, with the prefix ``oversampling-``.
Every number comes from ``ccdsr/oversampling.py``.
"""

import json
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from ccdsr import approaches as ap  # noqa: E402
from ccdsr import oversampling as ov  # noqa: E402

OUT = Path(__file__).resolve().parent
STORE = ROOT / "results" / "oversampling"
SEEDS = (0, 1, 2, 3, 4)
FRAMES = (1, 4, 16, 64, 256, 1024, 4096)
SOFT = "optics.edge_sigma_nm=127.4"       # the baseline pixel's soft edges (0.3 µm full width)

#: name, what it shows, scene, approach files, changed settings, ways
STUDY = [
    ("gap-300", "Gap 300 nm (pixel top layers removed), baseline pixel, surface of 100 nm cells", "fine_layout",
     ["least-squares"], [SOFT], ov.WAYS),
    ("methods", "The same with three other approaches", "fine_layout",
     ["wiener", "two-materials", "narrow-opening"], [SOFT], ("more-time",)),
    ("gap-1000", "Gap 1 µm (sensor as sold, touching), baseline pixel, surface of 100 nm cells", "fine_layout",
     ["least-squares"], [SOFT, "optics.gap_nm=1000"], ("more-time",)),
    ("gap-100", "Gap 100 nm, baseline pixel, surface of 100 nm cells", "fine_layout",
     ["least-squares"], [SOFT, "optics.gap_nm=100"], ("more-time",)),
    ("noisy-sensor", "Gap 300 nm, baseline pixel, read noise 10 electrons instead of 2, surface of 100 nm cells",
     "fine_layout", ["least-squares"], [SOFT, "noise.read_e=10"], ("same-time",)),
    ("coarse-cells", "Gap 300 nm, baseline pixel, surface of 240 nm cells", "random_layout",
     ["least-squares", "two-materials"], [SOFT], ("more-time",)),
]

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#dddcd6"
COLOURS = {"least-squares": "#2a78d6", "wiener": "#eb6834", "two-materials": "#1baf7a", "narrow-opening": "#eda100"}
WAY_STYLE = {"more-time": "-", "same-time": "--", "repeat": ":"}
WAY_LABEL = {"more-time": "more frames, same light in each (longer scan)",
             "same-time": "more frames in the same time (less light in each)",
             "repeat": "more frames with the sensor held still (plain averaging)"}


def rerun():
    runs = []
    for name, about, scene, files, changes, ways in STUDY:
        for file in files:
            approach = ap.load_approach(ROOT / "approaches" / f"{file}.toml", changes)
            for record in ov.sweep(approach, scene, ways, FRAMES, SEEDS):
                runs.append({"study": name, **{k: ov._rounded(v) for k, v in record.items()}})
            print(f"done {name} {file}", flush=True)
    STORE.mkdir(parents=True, exist_ok=True)
    (STORE / "runs.json").write_text(json.dumps({"seeds": list(SEEDS), "runs": runs}, indent=1) + "\n")


def load():
    runs = json.loads((STORE / "runs.json").read_text())["runs"]
    for r in runs:
        for key in ("recovered_period_nm", "level0_period_nm"):
            r[key] = math.inf if r[key] is None else r[key]
    return runs


def tables(runs):
    parts, first = [], 1
    for name, about, *_ in STUDY:
        mine = [r for r in runs if r["study"] == name]
        text = ov.tables_markdown(mine, SEEDS, first)
        first += text.count("*Table O")
        parts.append(f"### {about}\n\n{text}")
    (STORE / "tables.md").write_text("\n".join(parts))


def _axes(ax, ylabel):
    ax.set_facecolor(SURFACE)
    ax.set_xscale("log")
    ax.set_xlabel("readings of each point of the surface", fontsize=9, color=INK)
    ax.set_ylabel(ylabel, fontsize=9, color=INK)
    ax.grid(True, which="both", lw=0.4, color=GRID)
    ax.tick_params(labelsize=8, colors=INK2)
    ax.set_xticks([3, 10, 30, 100, 300, 1000, 3000, 10000],
                  ["3", "10", "30", "100", "300", "1,000", "3,000", "10,000"])
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def _log_y(ax, values):
    ax.set_yscale("log")
    ax.set_yticks(values, [f"{v:,}" for v in values])
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())


def _save(fig, name):
    fig.savefig(OUT / f"{name}.svg", metadata={"Date": None})
    fig.savefig(OUT / f"{name}.png", dpi=150, metadata={"Software": None})
    plt.close(fig)


def _line(runs, study, approach, way):
    mine = [r for r in runs if (r["study"], r["approach"], r["way"]) == (study, approach, way)]
    x = np.array([r["readings_per_point"] for r in mine])
    period = np.array([r["recovered_period_nm"] for r in mine])
    return x, np.array([r["rms_error"] for r in mine]), np.where(np.isfinite(period), period / 2, np.nan)


def figure_ways(runs):
    """Three ways of getting more readings, one method, one gap."""
    fig, (left, right) = plt.subplots(1, 2, figsize=(11, 4.3), facecolor=SURFACE)
    for way in ov.WAYS:
        x, error, width = _line(runs, "gap-300", "least-squares", way)
        left.plot(x, width, WAY_STYLE[way], color=COLOURS["least-squares"], marker="o", ms=3.5, lw=1.4,
                  label=WAY_LABEL[way])
        right.plot(x, error, WAY_STYLE[way], color=COLOURS["least-squares"], marker="o", ms=3.5, lw=1.4)
    _axes(left, "finest line width recovered (nm)")
    _log_y(left, [200, 300, 400, 500, 700])
    left.axhline(280, color=INK2, lw=0.8, ls=(0, (1, 3)))
    left.text(left.get_xlim()[0] * 1.15, 274, "lines of half the pixel width average out inside each pixel",
              fontsize=7.5, color=INK2, va="top")
    _axes(right, "error against the true surface (rms, reflectance)")
    left.set_ylim(190, 760)
    left.legend(frameon=False, fontsize=8, loc="lower left")
    fig.suptitle("Three ways of taking more readings: least squares, gap 300 nm, surface of 100 nm cells "
                 "(lower is better)", x=0.01, ha="left", fontsize=10.5, color=INK)
    fig.tight_layout()
    _save(fig, "oversampling-ways")


def figure_gaps(runs):
    """Gaps and methods, readings added by scanning longer."""
    fig, (left, right) = plt.subplots(1, 2, figsize=(11, 4.3), facecolor=SURFACE)
    for study, label, style in (("gap-100", "gap 100 nm", ":"), ("gap-300", "gap 300 nm", "-"),
                                ("gap-1000", "gap 1 µm", "--")):
        x, error, width = _line(runs, study, "least-squares", "more-time")
        left.plot(x, width, style, color=COLOURS["least-squares"], marker="o", ms=3.5, lw=1.4,
                  label=f"least squares, {label}")
    for study, approach, label in (("gap-300", "least-squares", "least squares"), ("methods", "wiener", "Wiener filter"),
                                   ("methods", "two-materials", "two known materials"),
                                   ("methods", "narrow-opening", "least squares, pixel opening narrowed")):
        x, error, width = _line(runs, study, approach, "more-time")
        right.plot(x, width, "-", color=COLOURS[approach], marker="o", ms=3.5, label=label,
                   lw=3.2 if approach == "least-squares" else 1.4, alpha=0.55 if approach == "least-squares" else 1)
    for ax in (left, right):
        _axes(ax, "finest line width recovered (nm)")
        _log_y(ax, [150, 200, 300, 400, 500, 700, 1000])
        ax.set_ylim(130, 1150)
        ax.legend(frameon=False, fontsize=8, loc="lower left")
    left.set_title("the gap", loc="left", fontsize=9.5, color=INK)
    right.set_title("the method, at a gap of 300 nm", loc="left", fontsize=9.5, color=INK)
    fig.suptitle("Finest line recovered against readings per point, for three gaps and four approaches "
                 "(lower is better)", x=0.01, ha="left", fontsize=10.5, color=INK)
    fig.tight_layout()
    _save(fig, "oversampling-gaps")


if __name__ == "__main__":
    plt.rcParams["svg.hashsalt"] = "oversampling"
    if "--rerun" in sys.argv:
        rerun()
    runs = load()
    tables(runs)
    figure_ways(runs)
    figure_gaps(runs)
    print((STORE / "tables.md").read_text())
