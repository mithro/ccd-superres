"""Generate the design-document diagrams.

Run from the repository root:

    python docs/diagrams/make_diagrams.py

Writes SVG (used by docs/design.md) and PNG copies next to this file.
The numbers used here are the illustrative baseline from the design
document, not results from the simulator.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle
from scipy.special import k1

OUT = Path(__file__).resolve().parent

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#dddcd6"
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
YELLOW = "#eda100"
BLUE_RAMP = ["#9cc4f2", "#2a78d6", "#123f78"]
SILICON = "#c9c8c1"
MASK = "#3b3a37"
SAMPLE = "#e9e4d4"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "text.color": INK,
        "axes.labelcolor": INK2,
        "axes.edgecolor": INK2,
        "xtick.color": INK2,
        "ytick.color": INK2,
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "svg.fonttype": "path",
    }
)


def save(fig, name):
    fig.savefig(OUT / f"{name}.svg", bbox_inches="tight")
    fig.savefig(OUT / f"{name}.png", bbox_inches="tight", dpi=160)
    plt.close(fig)


def arrow(ax, p0, p1, color=INK, lw=1.4, style="-|>", scale=12, **kw):
    ax.add_patch(
        FancyArrowPatch(
            p0, p1, arrowstyle=style, mutation_scale=scale, color=color, lw=lw,
            shrinkA=0, shrinkB=0, **kw
        )
    )


def rot(points, theta):
    c, s = np.cos(theta), np.sin(theta)
    return np.asarray(points) @ np.array([[c, s], [-s, c]])


# --------------------------------------------------------------------------
# 1. Scan geometry, top view
# --------------------------------------------------------------------------
def scan_geometry():
    fig, ax = plt.subplots(figsize=(10, 5.4))
    ax.set_aspect("equal")
    ax.axis("off")

    # Surface under test
    ax.add_patch(Rectangle((-1.5, -3.6), 16.5, 7.2, fc=SAMPLE, ec=INK2, lw=1))
    ax.text(-1.3, 3.25, "surface under test (top view)", color=INK2, va="top")

    n_cols, n_rows, p = 6, 4, 1.0
    theta = np.arctan(1 / n_cols)
    origin = np.array([1.2, -1.9])

    centres = {}
    for i in range(n_cols):
        for j in range(n_rows):
            corners = np.array([[i, j], [i + 1, j], [i + 1, j + 1], [i, j + 1]]) * p
            ax.add_patch(
                Polygon(rot(corners, theta) + origin, closed=True, fc="#ffffff",
                        ec=INK2, lw=0.9, alpha=0.9)
            )
            c = rot([[(i + 0.5) * p, (j + 0.5) * p]], theta)[0] + origin
            centres[(i, j)] = c

    # Tracks swept by the pixels of one sensor row, and their sample points
    j = 1
    for i in range(n_cols):
        c = centres[(i, j)]
        ax.plot([c[0], 14.6], [c[1], c[1]], color=BLUE, lw=0.9, ls=(0, (4, 3)))
        xs = np.arange(c[0], 14.6, 0.37)
        ax.plot(xs[1:], np.full(xs.size - 1, c[1]), ".", color=BLUE, ms=3.2)
    for (i, jj), c in centres.items():
        ax.plot(*c, "o", color=ORANGE if jj == j else INK2, ms=4.5 if jj == j else 3)

    # Scan direction
    arrow(ax, (8.6, 2.7), (12.6, 2.7), lw=2.2, scale=18)
    ax.text(10.6, 2.95, "scan direction, constant velocity v", ha="center")

    # Pitch annotation along the top edge of the sensor
    a = rot([[0, n_rows * p]], theta)[0] + origin
    b = rot([[p, n_rows * p]], theta)[0] + origin
    off = rot([[0, 0.28]], theta)[0]
    arrow(ax, a + off, b + off, style="<|-|>", lw=1, scale=8)
    ax.text(*(0.5 * (a + b) + 2.3 * off), "pitch p", ha="center", va="center",
            rotation=np.degrees(theta))

    # Tilt annotation
    corner = origin
    ax.plot([corner[0], corner[0] + 3.2], [corner[1], corner[1]], color=INK2, lw=0.8)
    arc_t = np.linspace(0, theta, 30)
    ax.plot(corner[0] + 2.6 * np.cos(arc_t), corner[1] + 2.6 * np.sin(arc_t),
            color=INK, lw=1)
    ax.text(corner[0] + 3.35, corner[1] + 0.02, "tilt θ", va="bottom")

    # Track spacing annotation
    c0, c1 = centres[(n_cols - 2, j)], centres[(n_cols - 1, j)]
    xa = 13.6
    arrow(ax, (xa, c0[1]), (xa, c1[1]), style="<|-|>", lw=1, scale=6)
    ax.text(14.75, 0.5 * (c0[1] + c1[1]) + 0.55,
            "track spacing\np·sin θ", ha="left", va="center")
    ax.plot([xa + 0.05, 14.7], [0.5 * (c0[1] + c1[1]), 0.5 * (c0[1] + c1[1]) + 0.45],
            color=INK2, lw=0.7)

    # Sample step annotation
    c = centres[(0, j)]
    xs = np.arange(c[0], 14.6, 0.37)
    k = 24
    ax.annotate("", (xs[k + 1], c[1] - 0.3), (xs[k], c[1] - 0.3),
                arrowprops=dict(arrowstyle="<|-|>", color=INK, lw=1, mutation_scale=6))
    ax.text(xs[k] + 0.18, c[1] - 0.72, "sample step d = v / f", ha="center")

    ax.text(5.6, -3.2, "tilted pixel array (6 × 4 shown; thousands in practice)",
            color=INK2)
    ax.plot([], [], "o", color=ORANGE, ms=4.5, label="centres of the pixels in one sensor row")
    ax.plot([], [], ls=(0, (4, 3)), color=BLUE, lw=0.9, marker=".", ms=3.2,
            label="track and samples of each of those pixels")
    ax.legend(loc="upper left", frameon=False, bbox_to_anchor=(0.03, 0.02), ncol=2)

    ax.set_xlim(-1.7, 17.3)
    ax.set_ylim(-3.8, 3.8)
    save(fig, "scan-geometry")


# --------------------------------------------------------------------------
# 2. Cross-section, side view
# --------------------------------------------------------------------------
def cross_section():
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.axis("off")

    # Sensor die
    ax.add_patch(Rectangle((0, 2.0), 12, 1.6, fc=SILICON, ec=INK2, lw=1))
    ax.text(0.15, 3.45, "sensor die", va="top", color=INK2)
    p = 3.0
    for i in range(4):
        x0 = i * p
        ax.add_patch(Rectangle((x0 + 0.25, 2.25), p - 0.5, 0.75, fc="#ffffff",
                               ec=INK2, lw=0.9))
        ax.text(x0 + p / 2, 2.62, f"pixel {i + 1}", ha="center", va="center",
                color=INK2, fontsize=9)
    # Bare die face: module lens, microlenses and colour filters removed
    ap = p - 0.5
    ax.text(12.15, 2.05, "sensor face (module lens removed;\nsee the sensor stack diagram)",
            va="center", color=INK2, fontsize=9)

    # Surface with height features and reflectance patches
    xs = np.linspace(-0.5, 12.5, 1300)
    h = np.zeros_like(xs)
    for x0, w, hh in [(1.4, 0.5, 0.22), (2.5, 0.25, 0.3), (4.35, 0.6, 0.16),
                      (7.2, 0.3, 0.26), (7.8, 0.3, 0.26), (10.3, 0.9, 0.12)]:
        h += hh * ((xs > x0) & (xs < x0 + w))
    base = 0.55
    ax.fill_between(xs, 0, base + h, color=SAMPLE, lw=0)
    ax.plot(xs, base + h, color=INK2, lw=1.1)
    for x0, w in [(5.6, 0.9), (9.0, 0.5)]:
        ax.plot([x0, x0 + w], [base, base], color=ORANGE, lw=3.5, solid_capstyle="butt")
    ax.text(6.05, 0.3, "reflectance ρ(x, y)", ha="center", color=INK2, fontsize=9)
    ax.text(1.65, 0.3, "height h(x, y)", ha="center", color=INK2, fontsize=9)
    ax.text(12.15, 0.3, "surface under test", va="center", color=INK2)

    # Collection cone for pixel 2
    xc = p + p / 2
    ax.add_patch(Polygon([[xc - ap / 2, 2.0], [xc + ap / 2, 2.0],
                          [xc + 2.3, base], [xc - 2.3, base]],
                         closed=True, fc=BLUE, alpha=0.22, ec="none"))
    ax.text(xc, 1.25, "light collected by one pixel", color=INK,
            fontsize=9, va="center", ha="center")

    # Dimensions
    arrow(ax, (10.0, base + 0.12), (10.0, 2.0), style="<|-|>", lw=1, scale=7)
    ax.text(10.12, 1.3, "gap z₀ (constant: motion is\nparallel to the surface)",
            va="center", fontsize=9)
    arrow(ax, (0, 3.85), (p, 3.85), style="<|-|>", lw=1, scale=7)
    ax.text(p / 2, 4.0, "pitch p", ha="center")

    # Motion
    arrow(ax, (7.2, 4.05), (10.6, 4.05), lw=2.2, scale=18)
    ax.text(8.9, 4.25, "sensor moves at constant velocity v", ha="center")

    ax.set_xlim(-0.6, 15.6)
    ax.set_ylim(-0.05, 4.6)
    save(fig, "cross-section")


# --------------------------------------------------------------------------
# 3. Sampling pattern
# --------------------------------------------------------------------------
def sampling_pattern():
    p, d = 1120.0, 130.0          # nm
    n_cols = 16
    theta = np.arctan(1 / n_cols)
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.9), sharex=True, sharey=True)
    titles = ["One pixel: fine along the scan, one line across it",
              f"All {n_cols} pixels of a sensor row: fine in both directions"]
    for ax, title, cols in zip(axes, titles, [[0], range(n_cols)]):
        ax.set_aspect("equal", adjustable="box")
        for i in cols:
            x0 = i * p * np.cos(theta)
            y0 = i * p * np.sin(theta)
            xs = (x0 + np.arange(-400, 400) * d)
            sel = (xs >= 0) & (xs <= 2 * p)
            ax.plot(xs[sel], np.full(sel.sum(), y0), ".", ms=3.4,
                    color=BLUE if i == 0 else ORANGE)
        ax.add_patch(Rectangle((560, 0), p, p, fc="none", ec=INK2, lw=1,
                               ls=(0, (4, 3))))
        ax.text(580, p + 25, "one pixel area", va="bottom", color=INK2, fontsize=9)
        ax.set_title(title, fontsize=10, loc="left", color=INK)
        ax.set_xlim(0, 2 * p)
        ax.set_ylim(-80, p + 130)
        ax.set_xlabel("along scan (nm)")
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axes[0].set_ylabel("across scan (nm)")
    axes[1].plot([], [], ".", color=BLUE, label="samples from pixel 1")
    axes[1].plot([], [], ".", color=ORANGE, label="samples from pixels 2 to 16")
    fig.legend(*axes[1].get_legend_handles_labels(), loc="lower center", ncol=2,
               frameon=False, bbox_to_anchor=(0.5, -0.04))
    fig.suptitle("Sample centres over the surface (pitch 1120 nm, step 130 nm, "
                 "tilt tan θ = 1/16)", x=0.02, ha="left", fontsize=11)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    save(fig, "sampling-pattern")


# --------------------------------------------------------------------------
# 4. Resolution budget: transfer functions
# --------------------------------------------------------------------------
def gap_transfer(period_nm, z_nm):
    u = 2 * np.pi * z_nm / period_nm
    return u * k1(u)


def box_envelope(period_nm, width_nm):
    """Upper envelope of |sinc(width / period)|."""
    x = width_nm / period_nm
    return np.minimum(np.abs(np.sinc(np.minimum(x, 0.5))), 1 / (np.pi * np.maximum(x, 1e-9)))


def soft_edge(period_nm, sigma_nm):
    return np.exp(-2 * np.pi**2 * sigma_nm**2 / period_nm**2)


def resolution_budget():
    period = np.logspace(1, 7, 700)          # nm
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.6), sharey=True)

    ax = axes[0]
    for z, c in zip([100, 3e3, 5e5], BLUE_RAMP):
        ax.loglog(period, gap_transfer(period, z), color=c, lw=2)
    ax.text(170, 2.2e-5, "gap 100 nm", color=INK, ha="right")
    ax.text(5.2e3, 2.2e-5, "3 µm", color=INK, ha="right")
    ax.text(8.5e5, 2.2e-5, "0.5 mm", color=INK, ha="right")
    ax.set_title("Gap between sensor and surface", loc="left", fontsize=10, color=INK)

    ax = axes[1]
    ax.loglog(period, box_envelope(period, 1120), color=BLUE, lw=2,
              label="1.12 µm pixel, ideal sharp edges")
    ax.loglog(period, box_envelope(period, 1120) * soft_edge(period, 300),
              color=ORANGE, lw=2, label="1.12 µm pixel, 0.3 µm soft edges")
    ax.loglog(period, box_envelope(period, 100), color=AQUA, lw=2,
              label="100 nm masked aperture")
    ax.legend(loc="lower right", frameon=False, fontsize=9,
              bbox_to_anchor=(1.0, 0.05))
    ax.set_title("Light-collecting area of a pixel", loc="left", fontsize=10,
                 color=INK)

    ticks = [10, 100, 1e3, 1e4, 1e5, 1e6, 1e7]
    for ax in axes:
        ax.axhline(1e-3, color=INK2, lw=0.9, ls=(0, (2, 3)))
        ax.set_xlim(10, 1e7)
        ax.set_ylim(1e-5, 1.6)
        ax.set_xticks(ticks)
        ax.set_xticklabels(["10 nm", "100 nm", "1 µm", "10 µm", "100 µm", "1 mm",
                            "10 mm"])
        ax.minorticks_off()
        ax.set_xlabel("feature period")
        ax.grid(True, which="major", color=GRID, lw=0.6)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axes[0].text(12, 1.25e-3, "illustrative noise floor", color=INK2, fontsize=9)
    axes[0].set_ylabel("contrast passed to the detector (1 = full)")
    fig.suptitle("How strongly each stage attenuates fine detail (analytic model, "
                 "box curves show the envelope)", x=0.02, ha="left", fontsize=11)
    fig.tight_layout()
    save(fig, "resolution-budget")


def smallest_period(z_nm, snr):
    """Period at which the gap transfer falls to 1/snr."""
    from scipy.optimize import brentq

    u = brentq(lambda u: u * k1(u) - 1 / snr, 1e-3, 60)
    return 2 * np.pi * z_nm / u


def gap_requirement():
    gap = np.logspace(0, 6, 200)             # nm
    fig, ax = plt.subplots(figsize=(7.6, 4.8))
    lo = smallest_period(gap, 1e4)
    hi = smallest_period(gap, 1e2)
    ax.fill_between(gap, lo, hi, color=BLUE, alpha=0.3, lw=0)
    ax.loglog(gap, smallest_period(gap, 1e3), color=BLUE, lw=2)
    ax.text(2.5e3, 30, "line: contrast floor 1/1000\nband: 1/100 to 1/10 000", color=INK2,
            fontsize=9, va="bottom")

    ax.axhline(1120, color=INK2, lw=0.9, ls=(0, (2, 3)))
    ax.text(1.15, 1350, "pixel pitch 1.12 µm", color=INK2, fontsize=9)

    setups = [(5e5, "cover glass\nleft on", (-12, -30), "right"),
              (3e3, "bare die,\nnear contact", (-10, 12), "right"),
              (20, "flying-head\nclass gap", (12, -22), "left")]
    for z, label, off, ha in setups:
        y = smallest_period(z, 1e3)
        ax.plot(z, y, "o", color=ORANGE, ms=8, mec=SURFACE, mew=2, zorder=5)
        ax.annotate(label, (z, y), off, textcoords="offset points", ha=ha,
                    fontsize=9, color=INK)

    ticks = [1, 10, 100, 1e3, 1e4, 1e5, 1e6]
    labels = ["1 nm", "10 nm", "100 nm", "1 µm", "10 µm", "100 µm", "1 mm"]
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels)
    ax.set_yticks(ticks)
    ax.set_yticklabels(labels)
    ax.minorticks_off()
    ax.set_xlim(1, 1e6)
    ax.set_ylim(1, 1e6)
    ax.set_xlabel("gap between sensor and surface")
    ax.set_ylabel("smallest recoverable feature period")
    ax.grid(True, which="major", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_title("The gap sets the lateral resolution; signal-to-noise barely moves it",
                 loc="left", fontsize=11, color=INK)
    fig.tight_layout()
    save(fig, "gap-requirement")


# --------------------------------------------------------------------------
# 6. Sensor stack of a Raspberry Pi camera module (schematic, not to scale)
# --------------------------------------------------------------------------
def sensor_stack():
    """Layer order follows the SEM cross-section of the IMX219 in
    Matthews et al., arXiv:1901.03807. Thicknesses are not to scale."""
    cfa = {"R": "#d9655f", "G": "#6fb36a", "B": "#5b86d6"}
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.2), sharey=True)
    titles = ["Module lens removed only",
              "Microlenses and colour filter also removed"]
    w = 2.0
    for ax, title, stripped in zip(axes, titles, [False, True]):
        ax.axis("off")
        ax.set_title(title, loc="left", fontsize=11, color=INK)
        # Wiring and carrier (back-illuminated: wiring is behind the photodiodes)
        ax.add_patch(Rectangle((0, 0), 3 * w, 0.8, fc="#a9a8a2", ec=INK2, lw=0.8))
        ax.text(3 * w / 2, 0.4, "wiring layers and carrier", ha="center",
                va="center", fontsize=9)
        # Silicon with photodiodes
        ax.add_patch(Rectangle((0, 0.8), 3 * w, 1.2, fc=SILICON, ec=INK2, lw=0.8))
        for i in range(3):
            ax.add_patch(Rectangle((i * w + 0.25, 0.95), w - 0.5, 0.9, fc="#ffffff",
                                   ec=INK2, lw=0.8))
            ax.text(i * w + w / 2, 1.4, "photodiode", ha="center", va="center",
                    fontsize=8, color=INK2)
        # Wire grid with sub-lenses
        tt = np.linspace(0, np.pi, 30)
        for i in range(4):
            ax.add_patch(Rectangle((i * w - 0.09 if i else 0, 2.0),
                                   0.18 if 0 < i < 3 else 0.09, 0.45, fc=MASK,
                                   ec="none") if i < 3 else
                         Rectangle((3 * w - 0.09, 2.0), 0.09, 0.45, fc=MASK, ec="none"))
        for i in range(3):
            xc = i * w + w / 2
            ax.fill(xc + 0.7 * np.cos(tt), 2.0 + 0.3 * np.sin(tt), fc="#ffffff",
                    ec=INK2, lw=0.7)
        top = 2.45
        if not stripped:
            for i, c in enumerate("GRG"):
                ax.add_patch(Rectangle((i * w, 2.45), w, 0.55, fc=cfa[c], ec=SURFACE,
                                       lw=1.5))
                ax.text(i * w + w / 2, 2.72, {"R": "red", "G": "green"}[c],
                        ha="center", va="center", fontsize=9, color="#ffffff")
            ax.add_patch(Rectangle((0, 3.0), 3 * w, 0.16, fc=YELLOW, alpha=0.5,
                                   ec="none"))
            for i in range(3):
                xc = i * w + w / 2
                ax.fill(xc + (w / 2 - 0.06) * np.cos(tt), 3.16 + 0.55 * np.sin(tt),
                        fc="#ffffff", ec=INK2, lw=0.9)
            top = 3.71
        else:
            xs = np.linspace(0, 3 * w, 300)
            rng = np.random.default_rng(3)
            rough = 2.45 + 0.05 * np.abs(np.convolve(rng.normal(size=300),
                                                      np.ones(9) / 9, "same")) * 4
            ax.plot(xs, rough, color=ORANGE, lw=1.2)
        # Surface under test above the sensor
        ax.add_patch(Rectangle((0, top + 0.8), 3 * w, 0.5, fc=SAMPLE, ec=INK2, lw=0.8))
        ax.text(3 * w / 2, top + 1.05, "surface under test", ha="center", va="center",
                fontsize=9)
        arrow(ax, (3 * w + 0.25, top), (3 * w + 0.25, top + 0.8), style="<|-|>", lw=1,
              scale=7)
        ax.text(3 * w + 0.4, top + 0.4, "air gap", va="center", fontsize=9)
        arrow(ax, (-0.3, 1.4), (-0.3, top + 0.8), style="<|-|>", lw=1, scale=7,
              color=BLUE)
        ax.text(-0.45, (1.4 + top + 0.8) / 2, "effective gap:\nphotodiode to surface",
                rotation=90, ha="right", va="center", fontsize=9, color=INK)
        ax.set_xlim(-1.3, 3 * w + 3.6)
        ax.set_ylim(-0.1, 5.6)

    ax = axes[0]
    x = 3 * w + 0.25
    for y, label in [(3.4, "microlens, one per pixel"), (3.08, "passivation layer"),
                     (2.72, "colour filter (Bayer pattern)"),
                     (2.2, "wire grid with sub-lens"), (1.4, "silicon"),]:
        ax.plot([3 * w, x - 0.05], [y, y], color=INK2, lw=0.6)
        ax.text(x, y, label, va="center", fontsize=9, color=INK)
    axes[1].text(3.0, 2.62, "residue and exposed wire grid", fontsize=9, color=INK,
                 ha="center", va="bottom")
    fig.suptitle("Layers on the light-facing side of the sensor (schematic, not to "
                 "scale)", x=0.02, ha="left", fontsize=11)
    fig.tight_layout()
    save(fig, "sensor-stack")


# --------------------------------------------------------------------------
# 7. How far more samples push the limit
# --------------------------------------------------------------------------
def recoverable_period(n_per_pixel_area, z_nm, pitch_nm=1120.0, snr_single=50.0):
    """Smallest period whose signal still exceeds the noise after averaging.

    Optimistic on purpose: full-contrast feature, ideal sharp pixel edges,
    perfectly known positions. A feature of period L is judged over a cell of
    (L/2)^2, which holds n * (L / 2p)^2 samples.
    """
    from scipy.optimize import brentq

    def margin(log_period):
        period = np.exp(log_period)
        n_cell = n_per_pixel_area * (period / (2 * pitch_nm)) ** 2
        signal = gap_transfer(period, z_nm) * box_envelope(period, pitch_nm)
        return np.log(signal * snr_single * np.sqrt(n_cell) + 1e-300)

    return np.exp(brentq(margin, np.log(1e-2), np.log(1e9)))


def samples_vs_resolution():
    n = np.logspace(0, 12, 121)
    gaps = [(300, "gap 0.3 µm"), (3e3, "gap 3 µm"), (3e4, "gap 30 µm")]
    fig, ax = plt.subplots(figsize=(8.2, 5.0))
    for (z, label), c in zip(gaps, BLUE_RAMP):
        y = np.array([recoverable_period(k, z) for k in n])
        ax.loglog(n, y, color=c, lw=2)
        ax.text(n[-1] * 1.5, y[-1], label, va="center", fontsize=9, color=INK)
    ax.axhline(1120, color=INK2, lw=0.9, ls=(0, (2, 3)))
    ax.text(1.3, 1350, "pixel pitch 1.12 µm", color=INK2, fontsize=9)
    n_pass = 3280 * 4
    ax.axvline(n_pass, color=INK2, lw=0.9, ls=(0, (2, 3)))
    ax.text(n_pass * 1.3, 2.2e5, "one pass of the\nbaseline sensor", color=INK2,
            fontsize=9, va="top")
    ticks = [100, 1e3, 1e4, 1e5]
    ax.set_yticks(ticks)
    ax.set_yticklabels(["100 nm", "1 µm", "10 µm", "100 µm"])
    ax.set_xticks([1, 1e3, 1e6, 1e9, 1e12])
    ax.set_xticklabels(["1", "thousand", "million", "billion", "trillion"])
    ax.minorticks_off()
    ax.set_xlim(1, 1e12)
    ax.set_ylim(60, 3e5)
    ax.set_xlabel("samples collected per pixel-sized area of surface")
    ax.set_ylabel("smallest recoverable feature period")
    ax.grid(True, which="major", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.set_title("A million times more samples buys less than a factor of two: the gap sets the floor",
                 loc="left", fontsize=11, color=INK)
    fig.tight_layout()
    save(fig, "samples-vs-resolution")


if __name__ == "__main__":
    scan_geometry()
    cross_section()
    sampling_pattern()
    resolution_budget()
    gap_requirement()
    sensor_stack()
    samples_vs_resolution()
    print("wrote diagrams to", OUT)
