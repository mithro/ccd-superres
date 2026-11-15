"""Generate the figures and numbers for docs/slot-waves.md.

Run from the repository root:

    python docs/diagrams/make_slot_wave_diagrams.py            # figures from saved runs
    python docs/diagrams/make_slot_wave_diagrams.py --rerun    # redo the wave runs (about 4 minutes)

Writes SVG and PNG figures next to this file with the prefix ``slot-waves-``,
and with ``--rerun`` the file ``results/edge-scatter/runs.json`` that the
page's tables are taken from.
"""

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from ccdsr.edge_scatter import run  # noqa: E402
from ccdsr.light_entry import ALUMINIUM, GLASS, light_under_sensor  # noqa: E402
from ccdsr.slot_modes import slot_modes, wave_light  # noqa: E402

OUT = Path(__file__).resolve().parent
RUNS = ROOT / "results" / "edge-scatter" / "runs.json"

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#dddcd6"
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
YELLOW = "#eda100"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "text.color": INK,
    "axes.labelcolor": INK2, "axes.edgecolor": INK2, "xtick.color": INK2,
    "ytick.color": INK2, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "svg.fonttype": "path",
})

CASES = [
    ("Aluminium line 100 nm high", dict(height_nm=100.0)),
    ("Aluminium line 300 nm high", dict(height_nm=300.0)),
    ("Aluminium line 1,000 nm high", dict(height_nm=1000.0)),
    ("Glass line 300 nm high", dict(height_nm=300.0, material=GLASS)),
    ("Aluminium 300 nm, second mode", dict(height_nm=300.0, mode=2)),
    ("Aluminium 300 nm, gap 3 µm", dict(height_nm=300.0, gap_nm=3000.0)),
    ("Aluminium 300 nm, gap 10 µm", dict(height_nm=300.0, gap_nm=10000.0)),
]


def save(fig, name):
    for ext in ("svg", "png"):
        fig.savefig(OUT / f"slot-waves-{name}.{ext}", dpi=160, bbox_inches="tight")
    plt.close(fig)


def rerun():
    out = []
    for label, kw in CASES:
        r = run(**kw)
        first, last = r.extent_nm()
        keep = r._inside()
        out.append({
            "label": label,
            "gap_nm": r.gap_nm,
            "thrown_up": r.thrown_up(),
            "peak_ratio": r.peak_ratio(),
            "peak_offset_nm": r.peak_offset_nm(),
            "extent_first_nm": first,
            "extent_last_nm": last,
            "run_from_nm": float(r.x_nm[keep][0]),
            "run_to_nm": float(r.x_nm[keep][-1]),
            "x_nm": [float(v) for v in r.x_nm[keep][::10]],
            "ratio": [float(v) for v in r.ratio()[keep][::10]],
        })
        print(label, {k: v for k, v in out[-1].items() if k not in ("x_nm", "ratio")}, flush=True)
    RUNS.parent.mkdir(parents=True, exist_ok=True)
    RUNS.write_text(json.dumps(out, indent=1))


def modes_figure():
    gaps = np.array([0.3, 0.5, 0.75, 1, 1.5, 2, 3, 4, 5, 7, 10, 15, 20, 30]) * 1000.0
    fig, (a, b) = plt.subplots(1, 2, figsize=(10.5, 4.2))
    for pol, c, name in (("s", BLUE, "field along the surfaces"), ("p", ORANGE, "field across the surfaces")):
        reach = [max(m.reach_nm for m in slot_modes(g, polarisation=pol)) / 1000.0 for g in gaps]
        a.loglog(gaps / 1000, reach, "o-", color=c, lw=1.6, ms=3.5, label=name)
    a.axhline(1380, color=INK2, lw=0.8, ls="--")
    a.text(0.32, 1700, "middle of the sensor, 1,380 µm in", fontsize=8.5, color=INK2)
    a.set_xlabel("Gap between chip and sensor (µm)")
    a.set_ylabel("Distance for the longest-lived wave to fall to 1 % (µm)")
    a.set_title("How far side light can travel", loc="left", fontsize=11)
    a.legend(frameon=False, fontsize=9, loc="lower right")
    wave = [wave_light(g).reading for g in gaps]
    ray = [light_under_sensor(g).reading for g in gaps]
    b.loglog(gaps / 1000, ray, "--", color=INK2, lw=1.6, label="straight rays (light entry page)")
    b.loglog(gaps / 1000, np.maximum(wave, 1e-30), "o-", color=AQUA, lw=1.8, ms=3.5, label="waves (this page)")
    b.set_ylim(1e-9, 1e-2)
    b.set_xlabel("Gap between chip and sensor (µm)")
    b.set_ylabel("Reading at the middle, share of an uncovered pixel's")
    b.set_title("How much arrives at the middle", loc="left", fontsize=11)
    b.legend(frameon=False, fontsize=9, loc="lower right")
    for ax in (a, b):
        ax.grid(True, which="major", color=GRID, lw=0.6)
        ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
        ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    fig.tight_layout()
    save(fig, "reach")


def scatter_figure(runs):
    fig, ax = plt.subplots(figsize=(9.5, 4.2))
    for r, c in zip(runs[:3], (BLUE, ORANGE, AQUA)):
        ax.plot(np.array(r["x_nm"]) / 1000, r["ratio"], color=c, lw=1.5, label=r["label"])
    ax.axhline(1.0, color=INK2, lw=0.8)
    ax.axvline(0.0, color=INK2, lw=0.8, ls="--")
    ax.text(0.2, ax.get_ylim()[1] * 0.93, "the line\nis here", fontsize=8.5, color=INK2, va="top")
    ax.text(-15, 0.22, "light travels from left to right", color=INK2, fontsize=8.5, va="center")
    ax.set_xlabel("Position along the slot, from the line (µm)")
    ax.set_ylabel("Pixel reading with the line ÷ without it")
    ax.set_yscale("log")
    ax.set_yticks([0.2, 0.5, 1, 2, 5])
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.grid(True, which="major", color=GRID, lw=0.6)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    fig.tight_layout()
    save(fig, "scatter")


if __name__ == "__main__":
    if "--rerun" in sys.argv:
        rerun()
    modes_figure()
    scatter_figure(json.loads(RUNS.read_text()))
    for g in (300, 600, 1000, 2000, 3000, 5000, 10000, 30000):
        s = slot_modes(g, polarisation="s")
        p = slot_modes(g, polarisation="p")
        w = wave_light(g)
        r = light_under_sensor(g)
        print(f"gap {g}: modes {len(s)}+{len(p)}  flattest {s[0].grazing_deg:.1f} deg  "
              f"reach s {s[0].reach_nm / 1000:.1f} um p {max(m.reach_nm for m in p) / 1000:.1f} um  "
              f"left at middle {s[0].left_after(1.38e6):.2g}  wave reading {w.reading:.2g}  "
              f"ray reading {r.reading:.2g}  last touch {w.last_touch_nm / 1000:.0f} um")
