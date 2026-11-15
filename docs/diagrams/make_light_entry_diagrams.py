"""Generate the diagrams for docs/light-entry.md.

Run from the repository root:

    python docs/diagrams/make_light_entry_diagrams.py

Writes SVG (used by the page) and PNG copies next to this file, with the
prefix ``light-entry-``. Every curve comes from ``ccdsr/light_entry.py``.
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ccdsr.light_entry import light_under_sensor  # noqa: E402

OUT = Path(__file__).resolve().parent

# Same palette as make_diagrams.py so the figures match.
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#dddcd6"
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
YELLOW = "#eda100"
SILICON = "#c9c8c1"
SAMPLE = "#e9e4d4"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "text.color": INK,
    "axes.labelcolor": INK2, "axes.edgecolor": INK2, "xtick.color": INK2,
    "ytick.color": INK2, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "svg.fonttype": "path",
})


def save(fig, name):
    for ext in ("svg", "png"):
        fig.savefig(OUT / f"light-entry-{name}.{ext}", dpi=160, bbox_inches="tight")
    plt.close(fig)


def slot():
    """Side view of the slot with one ray, not to scale."""
    fig, ax = plt.subplots(figsize=(9.2, 3.4))
    ax.set_xlim(-2.2, 10.4)
    ax.set_ylim(-1.5, 2.9)
    ax.axis("off")
    ax.add_patch(Rectangle((0, 1.0), 10, 0.9, facecolor=SILICON, edgecolor=INK2))
    ax.add_patch(Rectangle((0, -0.9), 10, 0.9, facecolor=SAMPLE, edgecolor=INK2))
    ax.text(5, 1.45, "sensor (pixels face down)", ha="center", va="center")
    ax.text(5, -0.45, "chip being looked at", ha="center", va="center")
    # the ray
    xs = np.arange(0, 10.01, 1.25)
    ys = np.where(np.arange(len(xs)) % 2 == 0, 0.0, 1.0)
    ax.plot([-1.9, 0], [1.52, 0.0], color=ORANGE, lw=1.6)
    for k in range(len(xs) - 1):
        ax.plot(xs[k:k + 2], ys[k:k + 2], color=ORANGE, lw=1.6, alpha=max(0.25, 1 - 0.1 * k))
    ax.text(-2.1, 1.75, "ordinary light\nfrom the side", ha="left", va="bottom", color=ORANGE)
    # labels
    ax.annotate("", xy=(10.2, 1.0), xytext=(10.2, 0.0),
                arrowprops=dict(arrowstyle="<->", color=INK2))
    ax.text(10.3, 0.5, "gap", va="center", color=INK2)
    ax.annotate("", xy=(2.5, -1.15), xytext=(5.0, -1.15),
                arrowprops=dict(arrowstyle="<->", color=BLUE))
    ax.text(3.75, -1.42, "one hop: from one touch of the chip to the next", ha="center",
            va="center", color=BLUE)
    ax.annotate("a little is lost\nat every touch", xy=(2.5, 0.0), xytext=(0.6, 2.25),
                arrowprops=dict(arrowstyle="->", color=INK2), color=INK2, va="bottom")
    ax.annotate("what a pixel absorbs\nhere is its reading", xy=(6.25, 1.0), xytext=(6.6, 2.25),
                arrowprops=dict(arrowstyle="->", color=INK2), color=INK2, va="bottom")
    ax.annotate("its light last touched\nthe chip half a hop back", xy=(5.0, 0.0), xytext=(7.2, -1.42),
                arrowprops=dict(arrowstyle="->", color=AQUA), color=AQUA, va="center")
    save(fig, "slot")


def curves():
    """Reading and last-touch distance against distance from the edge."""
    dist_um = np.logspace(0, np.log10(1380), 40)
    gaps_um = [0.3, 1.0, 3.0, 10.0]
    colours = [BLUE, ORANGE, AQUA, YELLOW]
    fig, (a, b) = plt.subplots(1, 2, figsize=(10.5, 4.2))
    for gap, c in zip(gaps_um, colours):
        got = [light_under_sensor(gap * 1000, distance_nm=d * 1000) for d in dist_um]
        a.loglog(dist_um, [g.reading for g in got], color=c, lw=1.8, label=f"gap {gap:g} µm")
        b.loglog(dist_um, [g.hop_in_gaps * gap / 2 for g in got], color=c, lw=1.8,
                 label=f"gap {gap:g} µm")
        b.axhline(gap, color=c, lw=0.9, ls=":")
    a.set_xlabel("Distance in from the open edge (µm)")
    a.set_ylabel("Reading, as a share of an uncovered pixel's")
    a.set_title("How much light a pixel gets", loc="left", fontsize=11)
    b.set_xlabel("Distance in from the open edge (µm)")
    b.set_ylabel("Distance to where the light last touched the chip (µm)")
    b.set_title("How far away that light last touched the chip", loc="left", fontsize=11)
    b.text(1.1, 0.33, "dotted: the gap itself, which is the\nblur in the best case of design Table 4.11b",
           fontsize=8.5, color=INK2, va="bottom")
    for ax in (a, b):
        ax.grid(True, which="major", color=GRID, lw=0.6)
        ax.axvline(1380, color=INK2, lw=0.8, ls="--")
        ax.legend(frameon=False, fontsize=9)
    a.text(1300, a.get_ylim()[1] * 0.5, "middle of\nthe sensor", ha="right", va="top", fontsize=8.5, color=INK2)
    fig.tight_layout()
    save(fig, "curves")


if __name__ == "__main__":
    slot()
    curves()
    for gap in (300, 1000, 3000, 10000, 30000, 100000, 500000):
        r = light_under_sensor(gap)
        print(f"gap {gap:>7} nm  ratio {r.ratio:7.0f}  reading {r.reading:.1e}  "
              f"arrives at {r.arrival_deg:.1f} deg  last touch {r.hop_in_gaps * gap / 2000:.0f} um")
