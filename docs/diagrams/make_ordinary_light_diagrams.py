"""Generate the diagrams for docs/research/ordinary-light-routes.md.

Run from the repository root:

    python docs/diagrams/make_ordinary_light_diagrams.py          # everything, about 3 minutes
    python docs/diagrams/make_ordinary_light_diagrams.py --fast   # skip the two simulations

Writes SVG (used by the page) and PNG copies next to this file, with the
prefix ``olr-``, and prints the numbers of the page's tables. The estimates
come from ``ccdsr/near_contact.py`` and ``ccdsr/resolution.py``; the two
simulations use ``ccdsr/level1.py`` and a small two-dimensional solver
written here.
"""

import math
import sys
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle
from scipy.special import k1

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ccdsr import level1 as l1  # noqa: E402
from ccdsr.near_contact import (absorption_depth_nm, contact_band_wedge,  # noqa: E402
                                contact_zone_sphere, fade_length_nm, finest_line, hole_light,
                                near_field_transfer, oversampling_exponent, readings_needed,
                                silicon_pattern_survival, slit_light, through_sensor_contrast)

OUT = Path(__file__).resolve().parent
FAST = "--fast" in sys.argv

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#dddcd6"
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
YELLOW = "#eda100"
PURPLE = "#7a4fc9"
SILICON = "#c9c8c1"
SAMPLE = "#e9e4d4"
METAL = "#3b3a37"
RED = "#b3261e"
GLASS = "#dcebf5"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "text.color": INK,
    "axes.labelcolor": INK2, "axes.edgecolor": INK2, "xtick.color": INK2,
    "ytick.color": INK2, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "svg.fonttype": "path",
})

BASE = 13_000.0          # readings per pixel area in the baseline scan (design, section 5.2)
FPS = 30.0               # baseline frame rate


def save(fig, name):
    for ext in ("svg", "png"):
        fig.savefig(OUT / f"olr-{name}.{ext}", dpi=160, bbox_inches="tight")
    plt.close(fig)


def matt(period, distance):
    u = 2 * np.pi * np.asarray(distance, dtype=float) / period
    return np.where(u < 1e-8, 1.0, u * k1(np.maximum(u, 1e-300)))


# ------------------------------------------------------------ 1. fading

def fading():
    """How the fine detail fades with distance from the chip."""
    d = np.linspace(0, 1200, 600)
    fig, ax = plt.subplots(figsize=(9.2, 4.8))
    bands = [(0, 140, AQUA, "bare silicon face,\nnearly touching"),
             (250, 350, YELLOW, "top layers\nstripped"),
             (900, 1100, ORANGE, "sensor as sold,\ntouching")]
    for a, b, colour, label in bands:
        ax.axvspan(a, b, color=colour, alpha=0.18, lw=0)
        ax.text((a + b) / 2, 2.2, label, ha="center", va="bottom", fontsize=8.5, color=INK2)
    for period, colour in ((200, RED), (400, BLUE), (1000, INK2)):
        ax.plot(d, matt(period, d), color=colour, lw=2,
                label=f"lines {period // 2} nm wide (repeat {period} nm), light from all directions")
    ax.plot(d, near_field_transfer(200, d, 450.0), color=RED, lw=1.4, ls="--",
            label="lines 100 nm wide, blue light straight on (wave formula)")
    ax.axhline(0.02, color=GRID, lw=1)
    ax.text(1195, 0.023, "1 part in 50: one baseline reading can just see it", ha="right",
            fontsize=8, color=INK2)
    ax.set_yscale("log")
    ax.set_ylim(1e-6, 2)
    ax.set_xlim(0, 1200)
    ax.set_xlabel("distance from the chip's features to the light-sensitive silicon (nm)")
    ax.set_ylabel("share of the pattern's strength that arrives")
    ax.grid(True, which="major", color=GRID, lw=0.6)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2, fontsize=8.5, frameon=False)
    save(fig, "fading")


# ----------------------------------------------------- 2. distance x softness

def distance_softness_map():
    dist = np.linspace(0, 400, 41)
    soft = np.linspace(0, 330, 34)
    z = {}
    for n in (BASE, BASE * 1000):
        z[n] = np.array([[finest_line(d, s, n) for d in dist] for s in soft])
    fig, ax = plt.subplots(figsize=(8.6, 5.4))
    cf = ax.contourf(dist, soft, z[BASE], levels=[0, 50, 75, 100, 125, 150, 200, 250, 300],
                     cmap="YlGnBu_r", alpha=0.85)
    cb = fig.colorbar(cf, ax=ax, pad=0.02)
    cb.set_label("finest line width, baseline scan of 13,000 readings (nm)")
    c1 = ax.contour(dist, soft, z[BASE], levels=[100], colors=[INK], linewidths=2.2)
    c2 = ax.contour(dist, soft, z[BASE * 1000], levels=[100], colors=[RED], linewidths=2.0,
                    linestyles="--")
    ax.clabel(c1, fmt="100 nm, baseline scan", fontsize=8)
    ax.clabel(c2, fmt="100 nm, 1,000 times more readings", fontsize=8)
    marks = [(300, 300, "top layers stripped,\nbaseline pixel", "s"),
             (100, 100, "bare silicon face,\nwalls between pixels", "o"),
             (50, 30, "metal mask with\nslits, touching", "^")]
    for x, y, label, m in marks:
        ax.plot(x, y, m, color=ORANGE, ms=9, mec=INK, zorder=5)
        ax.annotate(label, (x, y), textcoords="offset points", xytext=(9, 6), fontsize=8.5)
    ax.set_xlabel("distance from features to the sensing plane (nm)")
    ax.set_ylabel("softness of the pixel's edge (nm, full width at half height)")
    save(fig, "distance-softness")


# ------------------------------------------------------------ 3. oversampling

CASES = [
    (0, 0, "touching, ideally sharp pixel (not buildable)", INK2, ":"),
    (50, 30, "50 nm away, edge soft over 30 nm", AQUA, "-"),
    (100, 100, "100 nm away, edge soft over 100 nm", BLUE, "-"),
    (200, 100, "200 nm away, edge soft over 100 nm", PURPLE, "-"),
    (300, 300, "300 nm away, edge soft over 300 nm", YELLOW, "-"),
    (1000, 300, "1,000 nm away (sensor as sold, touching)", ORANGE, "-"),
]


def oversampling():
    n = np.logspace(2, 12, 61)
    fig, ax = plt.subplots(figsize=(9.2, 5.2))
    for d, s, label, colour, ls in CASES:
        ax.plot(n, [finest_line(d, s, x) for x in n], color=colour, lw=2, ls=ls, label=label)
    ax.axhline(100, color=RED, lw=1.2)
    ax.text(1.3e2, 104, "target: lines 100 nm wide", color=RED, fontsize=8.5)
    ax.axvline(BASE, color=GRID, lw=1.2)
    ax.text(BASE * 1.15, 12, "baseline scan", fontsize=8.5, color=INK2, rotation=90, va="bottom")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_ylim(10, 1500)
    ax.set_yticks([10, 20, 50, 100, 200, 500, 1000])
    ax.set_yticklabels(["10", "20", "50", "100", "200", "500", "1,000"])
    ax.set_xlabel("readings of each pixel-sized patch of the chip")
    ax.set_ylabel("finest line width (nm)")
    ax.grid(True, which="major", color=GRID, lw=0.6)
    ax.legend(fontsize=8.5, frameon=False, loc="upper right", ncol=2)
    top = ax.secondary_xaxis("top", functions=(lambda x: x / FPS / 3600, lambda h: h * FPS * 3600))
    top.set_xlabel("time the sensor spends over each point at 30 frames per second (hours)")
    save(fig, "oversampling")


# ---------------------------------------------------------------- 4. stacks

def stacks():
    """Four sensor faces above the same chip. Heights to a common scale."""
    fig, ax = plt.subplots(figsize=(10.5, 5.0))
    ax.set_xlim(-0.2, 17.6)
    ax.set_ylim(-520, 1750)
    ax.axis("off")
    width = 3.6
    cols = [0.2, 4.6, 9.0, 13.4]
    titles = ["As sold, touching", "Top layers stripped", "Bare silicon face,\nwalls between pixels",
              "Metal mask with\nnarrow slits"]
    dists = [1000, 300, 100, 50]
    for x0, title, dist in zip(cols, titles, dists):
        # chip
        ax.add_patch(Rectangle((x0, -400), width, 400, facecolor=SAMPLE, edgecolor=INK2))
        for i in range(9):
            ax.add_patch(Rectangle((x0 + 0.1 + i * 0.4, -60), 0.2, 60, facecolor=METAL, edgecolor="none"))
        ax.text(x0 + width / 2, -250, "chip, lines 100 nm wide", ha="center", fontsize=8, color=INK2)
        ax.text(x0 + width / 2, 1640, title, ha="center", va="center", fontsize=9.5, weight="bold")
        top = dist
        if dist == 1000:
            ax.add_patch(Rectangle((x0, 30), width, 520, facecolor="#f6d9c9", edgecolor=INK2, lw=0.6))
            ax.text(x0 + width / 2, 290, "tiny lenses", ha="center", fontsize=8)
            ax.add_patch(Rectangle((x0, 550), width, 300, facecolor="#cfe3c4", edgecolor=INK2, lw=0.6))
            ax.text(x0 + width / 2, 700, "colour filter", ha="center", fontsize=8)
            ax.add_patch(Rectangle((x0, 850), width, 150, facecolor=GLASS, edgecolor=INK2, lw=0.6))
            ax.text(x0 + width / 2, 925, "clear layers", ha="center", fontsize=8)
        elif dist == 300:
            ax.add_patch(Rectangle((x0, 150), width, 150, facecolor=GLASS, edgecolor=INK2, lw=0.6))
            ax.text(x0 + width / 2, 225, "clear layers, residue", ha="center", fontsize=8)
            ax.text(x0 + width / 2, 75, "air gap", ha="center", fontsize=8, color=INK2)
        elif dist == 100:
            ax.add_patch(Rectangle((x0, 80), width, 20, facecolor=GLASS, edgecolor=INK2, lw=0.6))
        else:
            top = 110
            ax.add_patch(Rectangle((x0, 50), width, 60, facecolor=METAL, edgecolor="none"))
            for i in range(3):
                ax.add_patch(Rectangle((x0 + 0.55 + i * 1.2, 50), 0.12, 60, facecolor=SURFACE,
                                       edgecolor="none"))
        # silicon with pixels
        ax.add_patch(Rectangle((x0, top), width, 1500 - top, facecolor=SILICON, edgecolor=INK2))
        for i in range(1, 3):
            xx = x0 + i * 1.2
            if dist in (100, 50):
                ax.add_patch(Rectangle((xx - 0.06, top), 0.12, 1500 - top, facecolor=GLASS,
                                       edgecolor="none"))
            else:
                ax.plot([xx, xx], [top, 1500], color=INK2, lw=0.8, ls=":")
        ax.text(x0 + width / 2, 1300, "pixel silicon", ha="center", fontsize=8.5)
        # dimension
        xa = x0 + width + 0.18
        ax.add_patch(FancyArrowPatch((xa, 0), (xa, dist), arrowstyle="<->", color=RED,
                                     mutation_scale=8, lw=1.2))
        ax.text(xa + 0.08, dist / 2, f"{dist:,} nm", color=RED, fontsize=8.5, va="center",
                rotation=90)
    ax.text(0.2, -480, "Heights are drawn to one scale. Widths are not: a pixel is 1,120 nm wide.",
            fontsize=8, color=INK2)
    save(fig, "stacks")


# ----------------------------------------------------- 5. pattern in silicon

def silicon_survival():
    w = np.linspace(400, 1000, 301)
    fig, ax = plt.subplots(figsize=(8.8, 4.6))
    for period, colour in ((150, RED), (200, ORANGE), (300, BLUE), (400, AQUA)):
        ax.plot(w, [float(silicon_pattern_survival(period, x)) for x in w], color=colour, lw=2,
                label=f"lines {period // 2} nm wide")
    ax.set_xlabel("wavelength of the light (nm)")
    ax.set_ylabel("share of the pattern's contrast kept\ninside silicon with no walls")
    ax.set_ylim(0, 1)
    ax.set_xlim(400, 1000)
    ax.grid(True, color=GRID, lw=0.6)
    ax.legend(frameon=False, fontsize=9, loc="center right")
    ax2 = ax.twinx()
    ax2.plot(w, [absorption_depth_nm(x) / 1000 for x in w], color=INK2, lw=1.2, ls="--")
    ax2.set_yscale("log")
    ax2.set_ylabel("depth the light reaches in silicon (µm, dashed)")
    for x, name in ((405, "violet"), (450, "blue"), (530, "green"), (630, "red"), (850, "near-infrared")):
        ax.axvline(x, color=GRID, lw=0.8)
        ax.text(x + 4, 0.96, name, fontsize=8, color=INK2, rotation=90, va="top")
    save(fig, "silicon-survival")


# ------------------------------------------------------------ 6. contact zone

def contact_zone():
    x = np.linspace(-1840, 1840, 800)          # micrometres across the sensor's long side
    fig, ax = plt.subplots(figsize=(9.0, 4.6))
    for radius, colour in ((0.1, ORANGE), (1.0, BLUE), (10.0, AQUA)):
        gap = (x * 1e3) ** 2 / (2 * radius * 1e9)
        ax.plot(x, np.maximum(gap, 1), color=colour, lw=2,
                label=f"domed sensor, radius of curvature {radius:g} m")
    wedge = (x + 1840) * 1e3 * 1000 / 3.68e6
    ax.plot(x, np.maximum(wedge, 1), color=PURPLE, lw=2, ls="--",
            label="flat sensor tilted to rise 1,000 nm across its length")
    ax.axhspan(1, 100, color=AQUA, alpha=0.15, lw=0)
    ax.text(-1800, 45, "within 100 nm of the chip", fontsize=8.5, color=INK2)
    ax.axhline(5000, color=GRID, lw=1)
    ax.text(1800, 5600, "above 5,000 nm light can get in from the side", ha="right", fontsize=8,
            color=INK2)
    ax.set_yscale("log")
    ax.set_ylim(1, 3e4)
    ax.set_xlabel("position across the sensor (µm); the sensor is 3,680 µm long")
    ax.set_ylabel("air gap between sensor face and chip (nm)")
    ax.grid(True, which="major", color=GRID, lw=0.6)
    ax.legend(frameon=False, fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2)
    save(fig, "contact-zone")


# ------------------------------------------------------------- 7. light paths

def light_paths():
    fig, axes = plt.subplots(1, 3, figsize=(11.0, 4.2))
    titles = ["Lamp behind the chip", "Lamp behind the sensor", "Light from the side"]
    for ax, title in zip(axes, titles):
        ax.set_xlim(0, 10)
        ax.set_ylim(-2.4, 7.4)
        ax.axis("off")
        ax.set_title(title, fontsize=10, weight="bold")
        ax.add_patch(Rectangle((0.5, 3.0), 9, 2.0, facecolor=SILICON, edgecolor=INK2))
        ax.text(5, 4.3, "sensor", ha="center", fontsize=9)
        ax.add_patch(Rectangle((0.5, 3.0), 9, 0.5, facecolor="#b9b8b0", edgecolor=INK2, lw=0.5))
        ax.text(5, 3.25, "pixels", ha="center", va="center", fontsize=7.5)
        ax.add_patch(Rectangle((0.5, 0.6), 9, 2.2, facecolor=SAMPLE, edgecolor=INK2))
        ax.text(5, 1.3, "chip", ha="center", fontsize=9)
        for xm, wm in ((1.4, 1.0), (3.6, 0.6), (5.2, 1.3), (7.6, 0.8)):
            ax.add_patch(Rectangle((xm, 2.55), wm, 0.25, facecolor=METAL, edgecolor="none"))
    ax = axes[0]
    for x in np.arange(1.0, 9.5, 0.8):
        blocked = any(a <= x <= a + b for a, b in ((1.4, 1.0), (3.6, 0.6), (5.2, 1.3), (7.6, 0.8)))
        ax.annotate("", xy=(x, 2.52 if blocked else 3.05), xytext=(x, -1.2),
                    arrowprops=dict(arrowstyle="->", color=RED, lw=1, alpha=0.45 if blocked else 0.95))
    ax.text(5, -1.9, "near-infrared light passes the chip's silicon;\nthe metal casts a shadow", ha="center",
            fontsize=8.5, color=RED)
    ax = axes[1]
    for x in np.arange(1.0, 9.5, 0.8):
        ax.annotate("", xy=(x, 2.85), xytext=(x, 6.6), arrowprops=dict(arrowstyle="->", color=RED, lw=1))
        ax.annotate("", xy=(x + 0.25, 3.3), xytext=(x + 0.05, 2.85),
                    arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1))
    ax.text(5, 7.0, "near-infrared lamp", ha="center", fontsize=8.5, color=RED)
    ax.text(5, -1.9, "light crosses each pixel twice: once going down,\nonce reflected by the chip", ha="center",
            fontsize=8.5, color=RED)
    ax = axes[2]
    ax.annotate("", xy=(1.5, 2.9), xytext=(-0.0, 2.9), arrowprops=dict(arrowstyle="->", color=RED, lw=1.4))
    ax.annotate("", xy=(8.5, 2.9), xytext=(10.0, 2.9), arrowprops=dict(arrowstyle="->", color=RED, lw=1.4))
    ax.text(5, 2.9, "×", ha="center", va="center", fontsize=26, color=RED)
    ax.text(5, -1.9, "a slot under 5,000 nm high swallows the light\nbefore it reaches the middle", ha="center",
            fontsize=8.5, color=RED)
    save(fig, "light-paths")


# ---------------------------------------------- 8. level 1 at near contact

L1_CASES = [(50, 0), (100, 0), (100, 100), (140, 0), (140, 100), (200, 0), (300, 0), (300, 300)]
L1_FRAMES = (400, 4000, 40000)
L1_PERIODS = [400, 300, 240, 200, 160]


def _l1_run(surface, groups, dx, gap, fwhm, frames, seed, want_estimate=False):
    optics = l1.Optics1D(gap_nm=gap, edge_sigma_nm=fwhm / 2.355)
    scan = l1.Scan1D(n_pixels=32, n_frames=frames, shift_px=0.0731, jitter_px=0.3)
    data = l1.simulate(surface, dx, optics, scan, l1.Noise1D(), seed=seed)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        estimate = l1.least_squares(data, smoothness=0.04 / frames, iterations=3000)[0]
    contrasts = [l1.bar_contrast(estimate, g, dx) for g in groups]
    return (contrasts, estimate) if want_estimate else contrasts


def level1_near_contact():
    dx = 10.0
    surface, groups = l1.bar_groups(L1_PERIODS, dx, cycles=8, margin_nm=1500.0)
    per_frame = 32 * 1120.0 / (surface.size * dx)
    truth = l1.bar_contrast(surface, groups[3], dx)
    print("\nLevel 1 in one dimension, bars 100 nm wide (repeat 200 nm). True contrast %.2f." % truth)
    print("readings of each pixel-sized stretch:", [round(f * per_frame) for f in L1_FRAMES])
    table = {}
    for gap, fwhm in L1_CASES:
        row = []
        for frames in L1_FRAMES:
            c = np.array([_l1_run(surface, groups, dx, gap, fwhm, frames, s)[3] for s in range(6)])
            row.append((c.mean(), c.std()))
        table[(gap, fwhm)] = row
        print(f"  distance {gap:4d} nm, edge {fwhm:3d} nm: " +
              "   ".join(f"{m:.2f} +/- {s:.2f}" for m, s in row))
    # figure: the group of 100 nm bars, three cases, at the largest number of readings
    fig, axes = plt.subplots(1, 3, figsize=(11.0, 3.6), sharey=True)
    shown = [(100, 0, AQUA), (140, 100, BLUE), (300, 300, ORANGE)]
    x = np.arange(surface.size) * dx
    _, a, b = groups[3]
    lo, hi = a - 40, b + 40
    for ax, (gap, fwhm, colour) in zip(axes, shown):
        _, est = _l1_run(surface, groups, dx, gap, fwhm, L1_FRAMES[-1], 0, want_estimate=True)
        ax.plot(x[lo:hi] - x[lo], surface[lo:hi], color=INK2, lw=1.2, label="true surface")
        ax.plot(x[lo:hi] - x[lo], est[lo:hi], color=colour, lw=2.0, label="reconstruction")
        ax.set_ylim(-0.4, 1.9)
        ax.set_title(f"{gap} nm away, edge soft over {fwhm} nm", fontsize=9.5)
        ax.set_xlabel("position along the scan (nm)")
        ax.grid(True, color=GRID, lw=0.5)
        ax.legend(frameon=False, fontsize=8, loc="upper right", ncol=2)
    axes[0].set_ylabel("reflectance")
    save(fig, "level1-near-contact")
    return table


# ------------------------------------------- 9. slits at several angles, in 2D

def _layout(n, cell, rng):
    """A random layout of lines one cell wide on a grid, running both ways."""
    img = np.zeros((n, n))
    y = 0
    while y < n:
        band = int(rng.integers(8, 16)) * cell
        horizontal = rng.random() < 0.5
        x = 0
        while x < n:
            length = int(rng.integers(5, 14)) * cell
            block = np.zeros((band, length))
            tracks = range(0, band if horizontal else length, 2 * cell)
            for t in tracks:
                if rng.random() < 0.8:
                    if horizontal:
                        block[t:t + cell, cell:length - cell] = 1
                    else:
                        block[cell:band - cell, t:t + cell] = 1
            h, w = img[y:y + band, x:x + length].shape
            img[y:y + band, x:x + length] = block[:h, :w]
            x += length
        y += band
    return 0.2 + 0.8 * img


def _kernel_ft(n, dx, long_nm, short_nm, angle_deg, soft_fwhm_nm, distance_nm):
    """Fourier transform of one pixel's footprint on the chip.

    A rectangle ``long_nm`` by ``short_nm`` turned by ``angle_deg``, its edges
    softened, then blurred by the distance with the matt model. Normalised so
    that an open pixel of 1,120 nm square has a value of 1 at zero frequency.
    """
    f = np.fft.fftfreq(n, d=dx)
    fx, fy = np.meshgrid(f, f)
    a = math.radians(angle_deg)
    fu = fx * math.cos(a) + fy * math.sin(a)
    fv = -fx * math.sin(a) + fy * math.cos(a)
    rect = np.sinc(fu * long_nm) * np.sinc(fv * short_nm) * (long_nm * short_nm / 1120.0**2)
    fr = np.hypot(fx, fy)
    sigma = soft_fwhm_nm / 2.355
    soft = np.exp(-2 * np.pi**2 * sigma**2 * fr**2)
    u = 2 * np.pi * distance_nm * fr
    blur = np.where(u < 1e-8, 1.0, u * k1(np.maximum(u, 1e-300)))
    return rect * soft * blur


def _solve(kernels, readings, weights, lam, iterations=400):
    """Least squares over all pixel kinds by conjugate gradients, in Fourier space."""
    n = readings[0].shape[0]
    f = np.fft.fftfreq(n)
    fx, fy = np.meshgrid(f, f)
    lap = (2 * np.sin(np.pi * fx)) ** 2 + (2 * np.sin(np.pi * fy)) ** 2

    def normal(v):
        vf = np.fft.fft2(v)
        out = lam * lap * vf
        for k, w in zip(kernels, weights):
            out = out + w * np.abs(k) ** 2 * vf
        return np.fft.ifft2(out).real

    b = sum(w * np.fft.ifft2(np.conj(k) * np.fft.fft2(r)).real
            for k, r, w in zip(kernels, readings, weights))
    x = np.zeros_like(b)
    r = b - normal(x)
    p = r.copy()
    rs = float(np.sum(r * r))
    for _ in range(iterations):
        ap = normal(p)
        alpha = rs / float(np.sum(p * ap))
        x += alpha * p
        r -= alpha * ap
        rs_new = float(np.sum(r * r))
        if rs_new < 1e-18 * float(np.sum(b * b)):
            break
        p = r + rs_new / rs * p
        rs = rs_new
    return x


def slit_demo():
    """Pixels behind narrow slits at several angles, against open pixels."""
    rng = np.random.default_rng(3)
    n, dx, cell = 256, 20.0, 5                       # 5.12 um square, lines 100 nm wide
    truth = _layout(n, cell, rng)
    electrons = 2500.0 * 40                          # 40 readings of 2,500 electrons at every position
    angles = np.arange(0, 180, 15)
    setups = {
        "Slits 100 nm wide at 12 angles,\n50 nm away, metal edge soft over 30 nm":
            [(_kernel_ft(n, dx, 1120, 100, a, 30, 50), 0.5) for a in angles],
        "Open pixels with walls,\n100 nm away, edge soft over 100 nm":
            [(_kernel_ft(n, dx, 1120, 1120, 0, 100, 100), 1.0)] * 12,
        "Baseline pixels, layers stripped,\n300 nm away, edge soft over 300 nm":
            [(_kernel_ft(n, dx, 1120, 1120, 0, 300, 300), 1.0)] * 12,
    }
    fig, axes = plt.subplots(1, 4, figsize=(12.5, 3.9))
    view = slice(60, 180)
    axes[0].imshow(truth[view, view], cmap="gray", vmin=0, vmax=1.2, interpolation="nearest")
    axes[0].set_title("True layout, lines 100 nm wide", fontsize=9)
    print("\nSlits at several angles, two dimensions: error of the picture (rms, reflectance units)")
    scores = {}
    for ax, (name, parts) in zip(axes[1:], setups.items()):
        kernels, readings, weights = [], [], []
        for kern, polar in parts:
            kern = kern * polar                      # a slit passes half the unpolarised light
            clean = electrons * np.fft.ifft2(kern * np.fft.fft2(truth)).real
            noisy = rng.poisson(np.maximum(clean, 0)) + rng.normal(0, 2.0 * math.sqrt(40), clean.shape)
            kernels.append(kern)
            readings.append(noisy / electrons)
            weights.append(1.0)
        best = None
        for lam in (1e-3, 1e-4, 1e-5, 1e-6, 1e-7, 1e-8):
            est = _solve(kernels, readings, weights, lam)
            err = float(np.sqrt(np.mean((est - truth) ** 2)))
            if best is None or err < best[0]:
                best = (err, est, lam)
        scores[name] = best[0]
        print(f"  {name.splitlines()[0]:45s} rms error {best[0]:.3f} (smoothing {best[2]:g})")
        ax.imshow(best[1][view, view], cmap="gray", vmin=0, vmax=1.2, interpolation="nearest")
        ax.set_title(name, fontsize=8.5)
    for ax in axes:
        ax.set_xticks([])
        ax.set_yticks([])
    axes[0].set_xlabel("area shown: 2.4 µm square", fontsize=8.5)
    save(fig, "slit-demo")
    return scores


def slit_layout():
    """Top view of pixels with slits at different angles."""
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    ax.set_aspect("equal")
    ax.axis("off")
    rng = np.random.default_rng(1)
    angles = np.arange(0, 180, 15)
    k = 0
    for j in range(4):
        for i in range(6):
            ax.add_patch(Rectangle((i, j), 1, 1, facecolor=METAL, edgecolor=SURFACE, lw=1.5))
            a = math.radians(angles[k % 12])
            k += 5
            cx, cy = i + 0.5, j + 0.5
            half_l, half_w = 0.42, 0.045
            ca, sa = math.cos(a), math.sin(a)
            pts = [(cx + sx * half_l * ca - sy * half_w * sa, cy + sx * half_l * sa + sy * half_w * ca)
                   for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            ax.add_patch(Polygon(pts, closed=True, facecolor=YELLOW, edgecolor="none"))
    ax.set_xlim(-0.1, 6.1)
    ax.set_ylim(-0.6, 4.1)
    ax.annotate("", xy=(1, -0.25), xytext=(0, -0.25), arrowprops=dict(arrowstyle="<->", color=INK2))
    ax.text(0.5, -0.5, "one pixel, 1,120 nm", ha="center", fontsize=8.5, color=INK2)
    ax.text(3.6, -0.4, "each slit about 100 nm wide; the scan carries every\nslit across every point of the chip",
            fontsize=8.5, color=INK2, va="center")
    save(fig, "slit-layout")


# ------------------------------------------------------------ 10. ranking

ROUTES = [
    # name, low, high (line width, nm), colour; in the order of the page's ranking
    ("A. Bare-silicon pixels with walls,\nnearly touching", 80, 130, AQUA),
    ("B. Metal mask with slits at many\nangles, nearly touching", 60, 110, AQUA),
    ("D. Routes A or B at 150 to 250 nm,\nwith 30 to 3,000 times the readings", 100, 170, AQUA),
    ("C. A tiny immersion lens per pixel\n(blue light, oil)", 100, 150, YELLOW),
    ("E. True picture near 170 nm, carried\nto 100 nm by elimination", 100, 170, PURPLE),
    ("F. Colour and polarisation per cell:\nwidths measured, no picture", 92, 108, PURPLE),
    ("Ordinary light today: sensor as sold,\ntouching", 432, 446, ORANGE),
]


def ranking():
    fig, ax = plt.subplots(figsize=(9.4, 4.8))
    for i, (name, lo, hi, colour) in enumerate(ROUTES[::-1]):
        ax.barh(i, hi - lo, left=lo, color=colour, edgecolor=INK2, height=0.55)
        ax.text(lo * 0.93, i, name, ha="right", va="center", fontsize=8.5)
    ax.axvline(100, color=RED, lw=1.4)
    ax.text(101, len(ROUTES) - 0.45, "target", color=RED, fontsize=8.5)
    ax.set_xscale("log")
    ax.set_xlim(12, 1200)
    ax.set_xticks([50, 100, 200, 500, 1000])
    ax.set_xticklabels(["50", "100", "200", "500", "1,000"])
    ax.set_yticks([])
    ax.set_xlabel("line width reached (nm). Estimates, not measurements")
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    handles = [Rectangle((0, 0), 1, 1, facecolor=c, edgecolor=INK2) for c in (AQUA, YELLOW, PURPLE, ORANGE)]
    ax.legend(handles, ["true picture, plain lamp", "true picture, needs liquid", "inferred or measured, not a true picture",
                        "where the project stands"], frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=2)
    save(fig, "ranking")


# ----------------------------------------------------------------- tables

def tables():
    print("Fade length (nm) of a pattern: period, in air at 450 nm, in oil (1.5) at 450 nm, in air at 1,050 nm")
    for p in (150, 200, 300, 400):
        print(f"  {p}: {fade_length_nm(p, 450):.0f}  {fade_length_nm(p, 450, 1.5):.0f}  {fade_length_nm(p, 1050):.0f}")
    print("\nShare of a 200 nm repeat left after a distance: matt model, wave formula at 450 nm, at 1,050 nm")
    for d in (30, 50, 100, 140, 200, 300, 1000):
        print(f"  {d:5d} nm: {float(matt(200, d)):.2g}  {float(near_field_transfer(200, d, 450)):.2g}"
              f"  {float(near_field_transfer(200, d, 1050)):.2g}")
    softs = (0, 30, 50, 100, 150, 300)
    print("\nFinest line (nm), baseline 13,000 readings. Columns: edge softness", softs)
    for d in (0, 30, 50, 100, 140, 200, 300, 500, 1000):
        print(f"  {d:5d}: " + " ".join(f"{finest_line(d, s):5.0f}" for s in softs))
    print("Finest line (nm), 1,000 times more readings")
    for d in (0, 30, 50, 100, 140, 200, 300, 500, 1000):
        print(f"  {d:5d}: " + " ".join(f"{finest_line(d, s, BASE * 1000):5.0f}" for s in softs))
    print("\nGain from 1,000 times more readings (factor), and power law exponent")
    for d, s in ((0, 0), (50, 30), (100, 100), (140, 100), (200, 100), (300, 300), (1000, 300), (3000, 300)):
        e = oversampling_exponent(d, s)
        print(f"  distance {d:5d}, edge {s:3d}: x{1000 ** e:.2f}  exponent {e:.3f}")
    print("\nReadings needed for 100 nm lines; and hours over each point at 30 frames per second")
    for d in (30, 50, 100, 140, 200, 250, 300, 400):
        row = []
        for s in (0, 50, 100, 150):
            r = readings_needed(100, d, s)
            row.append(f"{r:9.2g} ({r / FPS / 3600:8.2g} h)")
        print(f"  {d:4d}: " + "  ".join(row))
    print("\nPattern kept inside silicon without walls: wavelength, depth (nm), periods 150/200/300/400")
    for w in (405, 450, 530, 630, 850, 1050):
        print(f"  {w}: depth {absorption_depth_nm(w):9.0f}  " +
              " ".join(f"{float(silicon_pattern_survival(p, w)):.2f}" for p in (150, 200, 300, 400)))
    print("\nLight through openings, as a share of an open pixel's light")
    for w in (450, 1050):
        print(f"  holes at {w} nm (50, 100, 200 nm):", " ".join(f"{hole_light(d, w):.1e}" for d in (50, 100, 200)))
    print("  slits (50, 100, 200 nm):", " ".join(f"{slit_light(d):.3f}" for d in (50, 100, 200)))
    print("\nFinest line (nm) behind openings at 50 nm distance, metal edge soft over 30 nm, baseline readings")
    for name, opening, share in (("open sharp pixel", None, None),
                                 ("slit 100 nm", 100, slit_light(100)),
                                 ("slit 50 nm", 50, slit_light(50)),
                                 ("hole 100 nm, blue", 100, hole_light(100, 450)),
                                 ("hole 200 nm, blue", 200, hole_light(200, 450)),
                                 ("hole 200 nm, near-infrared", 200, hole_light(200, 1050))):
        print(f"  {name:28s}: {finest_line(50, 30, BASE, opening_nm=opening, light_share=share):6.0f}"
              f"   with 1,000x readings: {finest_line(50, 30, BASE * 1000, opening_nm=opening, light_share=share):6.0f}")
    print("\nZone held within a given gap: domed sensor (diameter um, pixels)")
    for radius in (0.1, 1.0, 10.0):
        for gap in (50, 100):
            dia, px = contact_zone_sphere(radius, gap)
            print(f"  radius {radius:5.1f} m, gap <= {gap:3d} nm: {dia:6.0f} um, {px:9.0f} pixels")
    for rise in (300, 1000, 3000):
        width, px = contact_band_wedge(rise, 3680, 100)
        print(f"  wedge rising {rise} nm over 3,680 um: band {width:6.0f} um wide, {px:9.0f} pixels")
    print("\nLamp through the sensor: contrast between metal (0.95) and bare silicon (0.31) at 1,050 nm:"
          f" {through_sensor_contrast(0.95, 0.31):.2f}")
    print("Incoherent lens limit: contrast left at a 200 nm repeat")
    for name, cutoff in (("air, 450 nm", 450 / 2), ("oil 1.5, 450 nm", 450 / 3), ("index 2.0, 450 nm", 450 / 4)):
        x = cutoff / 200
        mtf = 0.0 if x >= 1 else 2 / math.pi * (math.acos(x) - x * math.sqrt(1 - x * x))
        print(f"  {name:18s}: finest repeat {cutoff:.0f} nm, contrast at 200 nm repeat {mtf:.2f}")


if __name__ == "__main__":
    tables()
    fading()
    distance_softness_map()
    oversampling()
    stacks()
    silicon_survival()
    contact_zone()
    light_paths()
    slit_layout()
    ranking()
    if not FAST:
        level1_near_contact()
        slit_demo()
