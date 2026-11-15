"""Generate the diagrams for docs/backlight.md.

Run from the repository root:

    python docs/diagrams/make_backlight_diagrams.py

Writes SVG (used by the page) and PNG copies next to this file, with the
prefix ``backlight-``, and prints the numbers of the page's tables. Every
curve comes from ``ccdsr/backlight.py``.
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
from matplotlib.patches import Rectangle

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ccdsr.backlight import (absorption_per_um, backlight_period, backlight_reading,  # noqa: E402
                             best_wavelength, chip_transmission, depth_washout,
                             pixel_absorption)
from ccdsr.resolution import recoverable_period  # noqa: E402

OUT = Path(__file__).resolve().parent

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
METAL = "#3b3a37"
RED = "#b3261e"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "text.color": INK,
    "axes.labelcolor": INK2, "axes.edgecolor": INK2, "xtick.color": INK2,
    "ytick.color": INK2, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "svg.fonttype": "path",
})

SIGMA = 300 / 2.355     # baseline pixel edge softness, nm


def save(fig, name):
    for ext in ("svg", "png"):
        fig.savefig(OUT / f"backlight-{name}.{ext}", dpi=160, bbox_inches="tight")
    plt.close(fig)


def layout():
    """Side view: lamp below, chip, gap, sensor. Not to scale."""
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    ax.set_xlim(-0.3, 12.8)
    ax.set_ylim(-1.7, 5.2)
    ax.axis("off")
    ax.add_patch(Rectangle((0, 3.5), 10, 1.0, facecolor=SILICON, edgecolor=INK2))
    ax.text(5, 4.0, "sensor (pixels face down)", ha="center", va="center")
    ax.add_patch(Rectangle((0, 0.6), 10, 1.9, facecolor=SAMPLE, edgecolor=INK2))
    ax.text(5, 1.3, "the chip's silicon", ha="center", va="center")
    ax.add_patch(Rectangle((0, 2.5), 10, 0.5, facecolor="#f4f1e6", edgecolor=INK2))
    metal = [(0.6, 1.2), (2.6, 0.7), (4.2, 1.6), (6.9, 0.5), (8.2, 1.3)]
    for x, w in metal:
        ax.add_patch(Rectangle((x, 2.6), w, 0.28, facecolor=METAL, edgecolor="none"))
    for x in np.arange(0.3, 10, 0.6):
        blocked = any(m <= x <= m + w for m, w in metal)
        top = 2.58 if blocked else 3.5
        ax.annotate("", xy=(x, top), xytext=(x, -0.9),
                    arrowprops=dict(arrowstyle="->", color=RED, lw=1.0,
                                    alpha=0.9 if not blocked else 0.45))
    ax.text(5, -1.35, "plain near-infrared lamp behind the chip", ha="center", color=RED)
    ax.text(10.25, 4.0, "catches under 1 %\nof this light", va="center", color=INK2, fontsize=9)
    ax.text(10.25, 3.25, "gap", va="center", color=INK2, fontsize=9)
    ax.text(10.25, 2.75, "metal wiring in glass:\nblocks the light", va="center", color=INK2, fontsize=9)
    ax.text(10.25, 1.5, "lets part of the\nlight through", va="center", color=INK2, fontsize=9)
    save(fig, "layout")


def spectrum():
    """Chip transmission, pixel absorption and their product against wavelength."""
    w = np.arange(800.0, 1200.5, 2.0)
    fig, (a, b) = plt.subplots(1, 2, figsize=(10.5, 4.2))
    a.semilogy(w, chip_transmission(w, 500.0), color=BLUE, lw=1.8,
               label="gets through a chip 500 µm thick")
    a.semilogy(w, pixel_absorption(w), color=ORANGE, lw=1.8,
               label="caught by a pixel 3 µm deep")
    a.set_ylim(1e-5, 1.5)
    a.set_xlabel("Wavelength (nm)")
    a.set_ylabel("Share of the light")
    a.set_title("The two losses pull opposite ways", loc="left", fontsize=11)
    a.legend(frameon=False, fontsize=9, loc="lower center")
    for t, c in ((100.0, AQUA), (300.0, YELLOW), (500.0, BLUE), (750.0, INK2)):
        b.semilogy(w, backlight_reading(w, t), color=c, lw=1.8, label=f"chip {t:.0f} µm thick")
    b.set_ylim(1e-6, 1e-2)
    b.set_xlabel("Wavelength (nm)")
    b.set_ylabel("Reading, as a share of all the lamp's light")
    b.set_title("What a pixel detects", loc="left", fontsize=11)
    b.legend(frameon=False, fontsize=9, loc="upper right")
    for ax in (a, b):
        ax.grid(True, which="major", color=GRID, lw=0.6)
    fig.tight_layout()
    save(fig, "spectrum")


def sharpness():
    """Finest line width against gap, from behind and the visible best case."""
    gaps = np.logspace(np.log10(100), np.log10(10000), 40)
    back = [backlight_period(1.3e4, g, 1050.0, 3.0, edge_sigma_nm=SIGMA) / 2 for g in gaps]
    matt = [recoverable_period(1.3e4, g, edge_sigma_nm=SIGMA) / 2 for g in gaps]
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    ax.loglog(gaps / 1000, matt, color=INK2, lw=1.8, ls="--",
              label="visible light, best case of design Table 4.11b\n(no workable way to light it is known)")
    ax.loglog(gaps / 1000, back, color=RED, lw=2.0, label="near-infrared from behind, 1,050 nm")
    ax.set_xlabel("Gap between chip and sensor (µm)")
    ax.set_ylabel("Finest line width (nm)")
    ax.grid(True, which="major", color=GRID, lw=0.6)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    ax.set_yticks([200, 300, 500, 1000, 2000, 5000])
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    fig.tight_layout()
    save(fig, "sharpness")


if __name__ == "__main__":
    layout()
    spectrum()
    sharpness()
    print("rate per um:", {w: f"{float(absorption_per_um(w)):.2e}" for w in (550, 850, 950, 1000, 1050, 1100, 1150)})
    for t in (100, 300, 500, 750):
        bw, br = best_wavelength(t)
        print(f"thickness {t}: best {bw:.0f} nm reading {br:.1e};",
              {w: f"{float(backlight_reading(w, t)):.1e}" for w in (850, 950, 1000, 1050, 1100)})
    for w in (950, 1000, 1050, 1100):
        print(w, f"chip500 {float(chip_transmission(w, 500)):.3f} pixel {float(pixel_absorption(w)):.4f}")
    for p in (400, 500, 700, 1000, 1500, 2000):
        print("washout", p, f"{float(depth_washout(p, 1050)):.2f}")
    for g in (300, 1000, 3000, 10000):
        print("gap", g, "behind", round(backlight_period(1.3e4, g, 1050, 3, edge_sigma_nm=SIGMA) / 2),
              "depth 2:", round(backlight_period(1.3e4, g, 1050, 2, edge_sigma_nm=SIGMA) / 2),
              "depth 4:", round(backlight_period(1.3e4, g, 1050, 4, edge_sigma_nm=SIGMA) / 2),
              "matt visible", round(recoverable_period(1.3e4, g, edge_sigma_nm=SIGMA) / 2))
