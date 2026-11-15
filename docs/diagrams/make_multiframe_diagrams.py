"""Generate the diagrams for docs/research/multi-frame-reconstruction.md.

Run from the repository root:

    python docs/diagrams/make_multiframe_diagrams.py

Writes SVG (used by the document) and PNG copies next to this file, all with
the prefix ``mf-``, and prints the derived numbers quoted in the document.

Everything here is a formula or a small one-dimensional calculation, not a
result from the simulator. Each function says what it assumes.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, Rectangle

OUT = Path(__file__).resolve().parent

# Same palette as make_diagrams.py so all figures in the docs match.
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#dddcd6"
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
YELLOW = "#eda100"
VIOLET = "#7a5ad6"
SILICON = "#c9c8c1"
LIGHT = "#fff3c4"

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
        "svg.hashsalt": "mf",
    }
)

# Baseline sensor of the design (IMX219): pixel pitch and array size.
PITCH_UM = 1.12
ROWS = 2464
COLS = 3280


def save(fig, name):
    fig.savefig(OUT / f"mf-{name}.svg", bbox_inches="tight",
                metadata={"Date": None})
    fig.savefig(OUT / f"mf-{name}.png", bbox_inches="tight", dpi=160)
    plt.close(fig)


def arrow(ax, p0, p1, color=INK, lw=1.4, style="-|>", scale=12, **kw):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style,
                                 mutation_scale=scale, color=color, lw=lw,
                                 shrinkA=0, shrinkB=0, **kw))


def tidy(ax):
    ax.grid(True, color=GRID, lw=0.6, which="major")
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def blank(ax, xlim, ylim):
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.axis("off")


def sinc(x):
    """sin(pi x) / (pi x), the transfer function of a uniform smear."""
    return np.sinc(x)


# --------------------------------------------------------------------------
# 1. Charge shifting on the chip beside shifting in the computer
# --------------------------------------------------------------------------
def tdi_map():
    """Illustrative. Six rows stand for the many rows of a real sensor."""
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.3))
    titles = ("Time-delay integration on the chip",
              "The same sum done afterwards in the computer")
    for ax, title in zip(axes, titles):
        blank(ax, (-0.9, 11.2), (-2.6, 7.6))
        ax.set_title(title, fontsize=11, color=INK)
        for r in range(6):
            ax.add_patch(Rectangle((0, r), 4, 0.9, fc=SILICON, ec=INK2, lw=0.8))
            ax.text(-0.15, r + 0.45, f"row {6 - r}", ha="right", va="center",
                    fontsize=8, color=INK2)
        arrow(ax, (4.5, 6.0), (4.5, 0.2), color=ORANGE, lw=1.6)
        ax.text(4.5, 6.25, "image of the surface moves", fontsize=8.5,
                color=ORANGE, va="bottom", ha="center")
    ax = axes[0]
    for r in range(6):
        size = 0.10 + 0.05 * (5 - r)
        ax.add_patch(plt.Circle((2.0, r + 0.45), size, fc=BLUE, ec="none"))
        if r:
            arrow(ax, (2.0, r + 0.25), (2.0, r - 0.25), color=BLUE, lw=1.0,
                  scale=8)
    ax.text(2.0, -0.55, "one reading, at the last row", ha="center",
            fontsize=9, color=BLUE)
    ax.text(4.5, -1.75, "charge must keep step with the image:\n"
            "a speed error smears the picture for good", ha="center",
            fontsize=8.5, color=INK2)
    ax = axes[1]
    for r in range(6):
        ax.add_patch(plt.Circle((2.0, r + 0.45), 0.12, fc=BLUE, ec="none"))
        arrow(ax, (4.75, r + 0.45), (7.9, 3.0), color=BLUE, lw=0.8, scale=7)
    ax.add_patch(Rectangle((7.9, 2.2), 3.0, 1.6, fc=LIGHT, ec=INK2, lw=0.8))
    ax.text(9.4, 3.0, "measure shifts,\nthen add", ha="center", va="center",
            fontsize=8.5)
    ax.text(2.0, -0.55, "one reading per row", ha="center", fontsize=9,
            color=BLUE)
    ax.text(5.0, -1.75, "the shift of every reading is found from the data,\n"
            "so speed errors and wobble are corrected, not baked in",
            ha="center", fontsize=8.5, color=INK2)
    save(fig, "tdi-map")


# --------------------------------------------------------------------------
# 2. What a speed error does when rows are summed without correction
# --------------------------------------------------------------------------
def tdi_mismatch():
    """Uniform-smear model: N rows summed with a fractional speed error d
    slide the image by N*d pixels in total, which multiplies the contrast of a
    pattern of spatial frequency f (cycles per pixel) by |sinc(N d f)|."""
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.0))
    ax = axes[0]
    d = np.logspace(-3, 1.5, 500)  # per cent
    for n, c in ((16, AQUA), (96, BLUE), (128, VIOLET), (ROWS, ORANGE)):
        ax.plot(d, np.abs(sinc(n * d / 100 * 0.5)), color=c, lw=1.8,
                label=f"{n} rows")
    ax.axhline(0.9, color=INK2, lw=0.8, ls=":")
    ax.text(12, 0.915, "0.9", fontsize=8, color=INK2)
    ax.set_xscale("log")
    ax.set_xlabel("speed error between image and charge (%)")
    ax.set_ylabel("contrast kept for the finest\nsampled pattern (period 2 pixels)")
    ax.set_ylim(0, 1.05)
    ax.legend(frameon=False, fontsize=9, title="rows summed")
    tidy(ax)
    ax = axes[1]
    n = np.logspace(0.5, 3.6, 200)
    ax.plot(n, 100 * 0.5 / n, color=BLUE, lw=1.8)
    for nn in (16, 96, 128, ROWS):
        ax.plot([nn], [50 / nn], "o", color=ORANGE, ms=5)
        ax.annotate(f"{nn} rows: {50 / nn:.2g}%", (nn, 50 / nn),
                    textcoords="offset points", xytext=(6, 5), fontsize=8.5)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("rows summed without correction")
    ax.set_ylabel("largest speed error that keeps\n90% of that contrast (%)")
    tidy(ax)
    save(fig, "tdi-mismatch")
    print("TDI speed tolerance for 90% contrast at a 2-pixel period "
          "(smear of half a pixel):")
    for nn in (16, 32, 96, 128, ROWS):
        print(f"  {nn:5d} rows: {50 / nn:7.3f} %   "
              f"contrast at 2% error: {abs(sinc(nn * 0.02 * 0.5)):.2f}")


# --------------------------------------------------------------------------
# 3. Shift-and-add, drizzle and interlacing as filters; drizzle's noise
# --------------------------------------------------------------------------
def drizzle_kernel():
    """Transfer functions from the convolution chain of Fruchter and Hook
    (2002): pixel, then drop of size p, then output pixel of size s, all in
    units of the input pixel. Noise correlation ratio R from their equations
    9 and 10 for a filled, uniform dither pattern."""
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.0))
    ax = axes[0]
    f = np.linspace(0, 1.0, 400)
    pix = np.abs(sinc(f))
    ax.plot(f, pix, color=INK, lw=1.8, label="the pixel alone (interlacing)")
    ax.plot(f, pix * np.abs(sinc(0.6 * f) * sinc(0.5 * f)), color=BLUE, lw=1.8,
            label="drizzle, drop 0.6, output pixel 0.5")
    ax.plot(f, pix * np.abs(sinc(1.0 * f) * sinc(0.5 * f)), color=ORANGE,
            lw=1.8, label="shift-and-add, output pixel 0.5")
    ax.axvline(0.5, color=INK2, lw=0.8, ls=":")
    ax.text(0.505, 1.0, "finest pattern one\nframe can sample", fontsize=8,
            color=INK2, va="top")
    ax.set_xlabel("fineness of pattern (cycles per input pixel)")
    ax.set_ylabel("contrast kept")
    ax.legend(frameon=False, fontsize=8.5, loc="lower left")
    tidy(ax)
    ax = axes[1]
    r = np.linspace(0.02, 3, 400)
    big = np.where(r >= 1, r / (1 - 1 / (3 * np.maximum(r, 1))), np.nan)
    small = np.where(r <= 1, 1 / (1 - np.minimum(r, 1) / 3), np.nan)
    ax.plot(r, big, color=BLUE, lw=1.8)
    ax.plot(r, small, color=BLUE, lw=1.8)
    r0 = 0.6 / 0.5
    ax.plot([r0], [r0 / (1 - 1 / (3 * r0))], "o", color=ORANGE)
    ax.annotate("drop 0.6, output 0.5:\nR = 1.66", (r0, 1.662),
                textcoords="offset points", xytext=(10, -22), fontsize=8.5)
    ax.set_xlabel("drop size divided by output pixel size")
    ax.set_ylabel("true noise divided by the noise\nseen pixel to pixel (R)")
    tidy(ax)
    save(fig, "drizzle-kernel")
    print("Drizzle noise correlation ratio R:")
    for p, s in ((0.6, 0.5), (0.5, 0.5), (1.0, 0.5), (0.5, 0.4), (0.25, 0.5)):
        rr = p / s
        R = rr / (1 - 1 / (3 * rr)) if rr >= 1 else 1 / (1 - rr / 3)
        print(f"  drop {p:4.2f} output {s:4.2f}: R = {R:5.3f}")
    print("Contrast at 0.5 and 0.75 cycles per input pixel:")
    for name, p in (("interlace", 0.0), ("drizzle 0.6", 0.6), ("shift-add", 1.0)):
        for ff in (0.5, 0.75):
            v = abs(sinc(ff) * sinc(p * ff) * (sinc(0.5 * ff) if p else 1.0))
            print(f"  {name:12s} f={ff}: {v:.3f}")


# --------------------------------------------------------------------------
# 4. Noise cost of random shifts against the number of frames
# --------------------------------------------------------------------------
def random_dither_noise(trials=5000, seed=7):
    """One dimension. To sample M times finer than the pixel pitch, M aliased
    copies of each spatial frequency must be separated. Frame n, shifted by
    x_n pixels, sees copy m with phase exp(2 pi i m x_n). The noise gain is
    the root-mean-square error of the separated copies relative to N frames
    on an ideal, evenly spaced pattern. Shifts are uniform random and known
    exactly."""
    rng = np.random.default_rng(seed)
    fig, ax = plt.subplots(figsize=(6.6, 4.1))
    ratios = np.array([1, 1.5, 2, 3, 4, 6, 8, 12])
    table = {}
    for M, c in ((2, AQUA), (3, BLUE), (4, ORANGE)):
        med, hi = [], []
        for ratio in ratios:
            N = int(np.ceil(ratio * M - 1e-9))
            g = []
            for _ in range(trials):
                x = rng.random(N)
                phi = np.exp(2j * np.pi * np.outer(x, np.arange(M)))
                cov = np.linalg.pinv(phi.conj().T @ phi)
                g.append(np.sqrt(N * np.real(np.trace(cov)) / M))
            med.append(np.median(g))
            hi.append(np.percentile(g, 90))
        table[M] = (med, hi)
        ax.plot(ratios, med, color=c, lw=1.8, label=f"{M} times finer")
        ax.plot(ratios, hi, color=c, lw=1.0, ls="--")
    ax.axhline(1, color=INK2, lw=0.8, ls=":")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_ylim(0.6, 300)
    ax.set_xticks([1, 2, 4, 8, 12])
    ax.set_xticklabels(["1", "2", "4", "8", "12"])
    ax.set_xlabel("frames taken, as a multiple of the fewest that could work")
    ax.set_ylabel("noise, relative to a perfect\nevenly spaced pattern")
    ax.legend(frameon=False, fontsize=9, title="sampling wanted")
    ax.text(2.6, 0.66, "dotted line: a perfect pattern", fontsize=8,
            color=INK2, va="bottom")
    tidy(ax)
    save(fig, "random-dither-noise")
    print("Noise gain with random known shifts (median, 90th percentile):")
    for M, (med, hi) in table.items():
        row = ", ".join(f"x{r:g}: {m:.2f}/{h:.2f}"
                        for r, m, h in zip(ratios, med, hi))
        print(f"  M={M}: {row}")


# --------------------------------------------------------------------------
# 5. What the pixel charges for detail finer than itself
# --------------------------------------------------------------------------
def pixel_cost():
    """A pattern g times finer than the finest one frame can sample has a
    period of 2/g pixels. A pixel that collects evenly over a width w (in
    pixels) keeps |sinc(w g / 2)| of its contrast. Averaging must make up the
    loss, so the number of readings needed rises as one over that squared."""
    fig, ax = plt.subplots(figsize=(7.2, 4.3))
    g = np.linspace(1, 12, 2000)
    for w, c, lab in ((1.0, BLUE, "pixel sensitive over its full width"),
                      (0.5, AQUA, "pixel sensitive over half its width")):
        mtf = np.abs(sinc(w * g / 2))
        ax.plot(g, 1 / np.maximum(mtf, 1e-4) ** 2, color=c, lw=1.6, label=lab)
    env = (np.pi * g / 2) ** 2
    ax.plot(g, env, color=INK2, lw=1.0, ls="--",
            label="trend for the full-width pixel")
    ax.axhline(13000, color=ORANGE, lw=1.2)
    ax.text(1.1, 2.6e5, "orange line: readings of each pixel-sized patch\n"
            "in one slow pass (design, section 4.2)", fontsize=8.5,
            color=ORANGE, bbox=dict(fc=SURFACE, ec="none", pad=1.5))
    # Published systems sample 2 to 3 times finer, so the detail they
    # recover lies below those limits: a band, not a point on the curve.
    ax.axvspan(1, 3, color=YELLOW, alpha=0.13, lw=0,
               label="detail recovered by the published systems\n"
               "of table 3.2 (sampling 2 to 3 times finer)")
    ax.set_yscale("log")
    ax.set_ylim(1, 1e6)
    ax.set_xlabel("how many times finer than the pixel grid the detail is")
    ax.set_ylabel("extra readings needed to bring the\nnoise back to where it was")
    tidy(ax)
    ax.legend(frameon=True, framealpha=1.0, facecolor=SURFACE,
              edgecolor=GRID, fontsize=8, loc="lower right")
    save(fig, "pixel-cost")
    print("Contrast kept by a full-width pixel, and extra readings needed:")
    # Along a pixel axis the contrast is |sinc(g/2)|. For a pattern running
    # along the diagonal of a square pixel each axis sees g/(2 sqrt 2), and
    # the two factors multiply.
    for gg in (1, 1.5, 2, 3, 5, 6.6, 7, 9):
        m = abs(sinc(gg / 2))
        need = 1 / m ** 2 if m > 1e-9 else float("inf")
        md = sinc(gg / (2 * np.sqrt(2))) ** 2
        print(f"  {gg:4.1f} times finer (period {2 / gg:5.2f} px = "
              f"{2 * PITCH_UM * 1000 / gg:6.0f} nm): along an axis contrast "
              f"{m:5.3f}, readings x{need:8.1f}; along the diagonal contrast "
              f"{md:6.4f}, readings x{1 / md ** 2:10.1f}")


# --------------------------------------------------------------------------
# 6. Published registration and position accuracy, in pixels and nanometres
# --------------------------------------------------------------------------
ACCURACY = [
    # label, value in pixels, colour group
    ("ASTER satellite: wobble left before correction", 0.2, INK2),
    ("ASTER satellite: after correction from its own lines (upper limit)",
     0.08, BLUE),
    ("Satellite image pairs matched by correlation", 0.02, BLUE),
    ("Hubble: one star in one frame, random error", 0.02, AQUA),
    ("Drizzle test: star positions after combining", 0.018, AQUA),
    ("Digital time-delay integration: fitted motion (upper limit)",
     0.01, BLUE),
    ("Gaia: extra scatter actually found, one bright star, one detector",
     0.3 / 58.9, AQUA),
    ("Hubble: pixel-phase error left after solving (upper limit)",
     0.002, AQUA),
    ("Gaia: photon-noise floor for the same measurement",
     0.06 / 58.9, SILICON),
]


def accuracy_chart(need_nm=10.0):
    """Published figures only; sources are in the table on the page. The
    requirement line is this project's estimate: one tenth of a 100 nm
    feature."""
    fig, ax = plt.subplots(figsize=(8.6, 4.2))
    labels = [a[0] for a in ACCURACY][::-1]
    vals = [a[1] for a in ACCURACY][::-1]
    cols = [a[2] for a in ACCURACY][::-1]
    y = np.arange(len(vals))
    ax.barh(y, vals, color=cols, height=0.62)
    for yi, v in zip(y, vals):
        ax.text(v * 1.12, yi, f"{v:.2g} px = {v * PITCH_UM * 1000:.3g} nm",
                va="center", fontsize=8.5,
                bbox=dict(fc=SURFACE, ec="none", pad=1.0))
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8.5)
    ax.set_xscale("log")
    ax.set_xlim(5e-4, 3)
    need_px = need_nm / (PITCH_UM * 1000)
    ax.axvline(need_px, color=ORANGE, lw=1.3, zorder=0)
    ax.text(need_px * 1.08, len(vals) - 0.45,
            f"needed here: about {need_nm:.0f} nm", color=ORANGE, fontsize=8.5)
    ax.set_xlabel("position error (pixels of that instrument); nanometres are "
                  "for this project's 1.12 µm pixel")
    tidy(ax)
    ax.grid(False, axis="y")
    save(fig, "accuracy-chart")
    print(f"Requirement {need_nm} nm = {need_px:.4f} px")
    for lab, v, _ in ACCURACY:
        print(f"  {v:8.4f} px = {v * PITCH_UM * 1000:7.2f} nm  {lab}")


# --------------------------------------------------------------------------
# 7. How well a shift can be measured: the best case
# --------------------------------------------------------------------------
def shift_bound(signal_e=2250.0, corr_px=3.0):
    """Cramer-Rao bound for a pure shift between two frames with known scene:
    sigma = noise / (rms gradient * sqrt(pixels)). Noise is photon noise on a
    mean signal of `signal_e` electrons. The scene is a texture with rms
    contrast c whose brightness changes over `corr_px` pixels, so the rms
    gradient is taken as c * signal / corr_px. All three are assumptions.
    The default signal is half the 4500 electron full well the design assumes.
    The reference is taken as noise-free (a combined picture). Matching one
    noisy frame against another is worse by the square root of two."""
    noise = np.sqrt(signal_e)
    n = np.logspace(2, 7.2, 200)
    fig, ax = plt.subplots(figsize=(7.4, 4.3))
    out = {}
    for c, col in ((0.01, ORANGE), (0.05, BLUE), (0.20, AQUA)):
        grad = c * signal_e / corr_px
        sig = noise / (grad * np.sqrt(n))
        ax.plot(n, sig * PITCH_UM * 1000, color=col, lw=1.8,
                label=f"contrast {c:.0%}")
        out[c] = lambda npx, grad=grad: noise / (grad * np.sqrt(npx))
    marks = ((COLS, "one row"), (100 * COLS, "strip of\n100 rows"),
             (ROWS * COLS, "whole frame"))
    for npx, lab in marks:
        ax.axvline(npx, color=INK2, lw=0.8, ls=":")
        ax.text(npx * 0.86, 2.3e3, lab, fontsize=8, color=INK2, ha="right",
                va="top")
    ax.axhline(10, color=INK, lw=1.0, ls="--")
    ax.text(1.1e6, 14, "dashed line:\nabout 10 nm needed", fontsize=8.5)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_ylim(0.01, 3e3)
    ax.set_xlabel("pixels used to measure the shift")
    ax.set_ylabel("best possible error of the shift (nm)")
    ax.legend(frameon=False, fontsize=9, title="scene texture")
    tidy(ax)
    save(fig, "shift-bound")
    print(f"Best-case shift error (signal {signal_e:.0f} e-, texture scale "
          f"{corr_px:g} px):")
    for c, fn in out.items():
        row = ", ".join(f"{lab.replace(chr(10), ' ')}: {fn(npx):.5f} px = "
                        f"{fn(npx) * PITCH_UM * 1000:.2f} nm"
                        for npx, lab in marks)
        rows = (noise / (c * signal_e / corr_px) * PITCH_UM * 1000 / 10) ** 2 / COLS
        print(f"  contrast {c:.0%}: {row}; rows for 10 nm: {rows:.1f} "
              f"({1 / (max(rows, 1) * 18.9e-6):.0f} estimates per second)")


# --------------------------------------------------------------------------
# 8. Choosing the best frames against weighting all of them
# --------------------------------------------------------------------------
def lucky_weighting(frames=4000, spread=0.35, seed=11):
    """Each frame j blurs the surface with a Gaussian of width s_j (in
    pixels), drawn from a log-normal spread around 1 pixel: a stand-in for a
    gap or focus that varies during the scan. Noise is equal and independent
    in every frame. Signal-to-noise at each spatial frequency is compared for
    a plain average, for keeping only the sharpest frames, and for weighting
    every frame by its own transfer function (Zackay and Ofek 2017)."""
    rng = np.random.default_rng(seed)
    s = np.exp(rng.normal(0.0, spread, frames))
    f = np.linspace(0.01, 0.6, 120)
    P = np.exp(-2 * np.pi ** 2 * np.outer(s ** 2, f ** 2))
    proper = np.sqrt((P ** 2).sum(0))
    mean = P.sum(0) / np.sqrt(frames)
    order = np.argsort(s)
    fig, ax = plt.subplots(figsize=(7.0, 4.1))
    ax.plot(f, mean / proper, color=INK2, lw=1.8, label="plain average of all")
    res = {"all": mean / proper}
    for q, c in ((0.5, AQUA), (0.1, BLUE), (0.01, ORANGE)):
        k = max(1, int(q * frames))
        sel = P[order[:k]].sum(0) / np.sqrt(k)
        res[q] = sel / proper
        ax.plot(f, sel / proper, color=c, lw=1.8,
                label=f"sharpest {q:.0%} only")
    ax.axhline(1.0, color=INK, lw=1.0, ls="--")
    ax.text(0.012, 1.02, "every frame, weighted by its own sharpness",
            fontsize=8.5)
    ax.set_ylim(0, 1.12)
    ax.set_xlabel("fineness of pattern (cycles per pixel)")
    ax.set_ylabel("signal-to-noise, relative to\nthe weighted combination")
    ax.legend(frameon=False, fontsize=9, loc="lower left")
    tidy(ax)
    save(fig, "lucky-weighting")
    print("Signal-to-noise relative to the weighted combination:")
    for key, v in res.items():
        vals = ", ".join(f"f={ff:.2f}: {np.interp(ff, f, v):.2f}"
                         for ff in (0.05, 0.25, 0.5))
        print(f"  {key}: {vals}")


# --------------------------------------------------------------------------
# 9. Why a straight scan cannot calibrate the pixels, and a turned one can
# --------------------------------------------------------------------------
def selfcal_tracks():
    """Illustrative grid of 14 by 9 pixels. The numbers under the drawings
    are for the real sensor: columns crossed = rows * tan(tilt)."""
    fig, axes = plt.subplots(1, 3, figsize=(11.2, 4.1))
    specs = (("Straight scan", 0.0, 0.0),
             ("Sensor turned slightly", 14.0, 0.0),
             ("Second pass at right angles", 0.0, 1.0))
    for ax, (title, tilt, cross) in zip(axes, specs):
        blank(ax, (-0.5, 14.5), (-2.4, 9.6))
        ax.set_title(title, fontsize=11, color=INK)
        for i in range(14):
            for j in range(9):
                ax.add_patch(Rectangle((i, j), 1, 1, fc=SURFACE, ec=GRID,
                                       lw=0.6))
        hit = set()
        for x0, col in ((4.5, BLUE), (9.5, ORANGE)):
            dx = np.tan(np.radians(tilt)) * 9
            ax.plot([x0 - dx / 2, x0 + dx / 2], [0, 9], color=col, lw=1.8)
            for yy in np.linspace(0.05, 8.95, 60):
                xx = x0 - dx / 2 + dx * yy / 9
                hit.add((int(xx), int(yy), col))
        if cross:
            for y0, col in ((2.5, AQUA), (6.5, VIOLET)):
                ax.plot([0, 14], [y0, y0], color=col, lw=1.8, ls="--")
                for xx in np.linspace(0.05, 13.95, 60):
                    hit.add((int(xx), int(y0), col))
        for i, j, col in sorted(hit):
            ax.add_patch(Rectangle((i, j), 1, 1, fc=col, ec="none", alpha=0.18))
    notes = ("each surface point meets one column only:\n"
             "a weak column and a dark stripe on the\nsurface look the same",
             "each point crosses many columns\n"
             f"(real sensor: {ROWS * np.tan(np.radians(1)):.0f} columns "
             "at 1° of turn)",
             "each point also runs along a row,\nwhich ties all the columns "
             "together")
    for ax, note in zip(axes, notes):
        ax.text(7, -1.3, note, ha="center", va="center", fontsize=8.5,
                color=INK2)
    save(fig, "selfcal-tracks")
    print("Columns crossed by one surface point during a pass:")
    for t in (0.1, 0.5, 1.0, 2.0, 5.0):
        print(f"  tilt {t:3.1f} deg: {ROWS * np.tan(np.radians(t)):6.1f}")


def candidate_elimination(cells=12, sigma=1.5, trials=20, seed=5):
    """Ruling out candidate surfaces without measuring any position.

    Toy calculation. The surface is a ring of ``cells`` cells, each one of
    two materials (reading 0 or 1). Every frame is the surface slid round by
    a whole number of cells, plus Gaussian noise of standard deviation
    ``sigma`` (in units of the contrast between the two materials). All
    2**cells two-material patterns are candidates. A candidate is scored by
    how probable the frames are under it, added up over every position the
    frame could have had, and it survives while it is within a factor of
    1000 of the best candidate. Three levels of knowledge about position
    are compared on the same data: none at all, "the sensor moves at a
    steady unknown speed from an unknown start", and exact positions.
    """
    rng = np.random.default_rng(seed)
    n = cells
    ncand = 2 ** n
    cand = ((np.arange(ncand)[:, None] >> np.arange(n)) & 1).astype(float)
    weights = 1 << np.arange(n)
    # shifted[c, s] is the index of candidate c slid round by s cells.
    shifted = np.stack([(np.roll(cand, s, axis=1) @ weights).astype(int)
                        for s in range(n)], axis=1)
    # Design rule: every line and every space at least two cells wide.
    runs_ok = np.array([
        all(not (c[i] != c[i - 1] and c[i] != c[(i + 1) % n])
            for i in range(n)) and 0 < c.sum() < n for c in cand])
    allowed = np.flatnonzero(runs_ok)
    marks = np.array([1, 2, 5, 10, 20, 50, 100, 200, 400, 800, 1600])
    keep = np.log(1000.0)
    names = ("none", "steady", "exact", "none + rule")
    counts = {k: np.zeros((trials, marks.size)) for k in names}
    truth_out = []  # (frames, case) where the true pattern fell below the cut
    s0v = np.array([(a, v) for a in range(n) for v in range(n)])
    for t in range(trials):
        truth = rng.choice(allowed)
        start, speed = rng.integers(n), rng.integers(1, n)
        ll_none = np.zeros(ncand)
        ll_exact = np.zeros(ncand)
        ll_path = np.zeros((ncand, len(s0v)))
        for k in range(marks[-1]):
            pos = (start + k * speed) % n
            y = cand[shifted[truth, pos]] + sigma * rng.standard_normal(n)
            d = -((y[None, :] - cand) ** 2).sum(axis=1) / (2 * sigma ** 2)
            per_shift = d[shifted]                      # (candidate, shift)
            ll_none += np.logaddexp.reduce(per_shift, axis=1)
            ll_exact += per_shift[:, pos]
            ll_path += per_shift[:, (s0v[:, 0] + k * s0v[:, 1]) % n]
            if k + 1 in marks:
                m = int(np.flatnonzero(marks == k + 1)[0])
                lp = np.logaddexp.reduce(ll_path, axis=1)
                for name, ll in (("none", ll_none), ("steady", lp),
                                 ("exact", ll_exact)):
                    counts[name][t, m] = (ll >= ll.max() - keep).sum()
                    if ll[truth] < ll.max() - keep:
                        truth_out.append((int(k + 1), name))
                la = ll_none[allowed]
                counts["none + rule"][t, m] = (la >= la.max() - keep).sum()
    med = {k: np.median(v, axis=0) for k, v in counts.items()}

    fig, (a0, a1) = plt.subplots(1, 2, figsize=(10.5, 4.2),
                                 gridspec_kw={"width_ratios": [1, 2.1]})
    bars = [ncand, allowed.size]
    a0.bar([0, 1], bars, color=[SILICON, AQUA], width=0.6)
    for i, b in enumerate(bars):
        a0.text(i, b * 1.15, f"{b}", ha="center", fontsize=10)
    a0.set_yscale("log")
    a0.set_ylim(1, 20000)
    a0.set_xticks([0, 1])
    a0.set_xticklabels(["any two-material\npattern",
                        "lines and spaces\nat least 2 cells"], fontsize=9)
    a0.set_ylabel("candidate surfaces (count)")
    a0.set_title("Before any data", loc="left", fontsize=11)
    tidy(a0)
    styles = (("none", ORANGE, "-", "positions not known at all"),
              ("none + rule", ORANGE, "--",
               "not known, plus the 2-cell design rule"),
              ("steady", BLUE, "-",
               "steady unknown speed, unknown start"),
              ("exact", INK2, ":", "positions known exactly"))
    for name, col, ls, lab in styles:
        a1.plot(marks, med[name], color=col, ls=ls, lw=2, marker="o", ms=4,
                label=lab)
    a1.axhline(n, color=GRID, lw=1.2)
    a1.text(marks[-1], n * 1.25, f"{n} copies of the true pattern, slid along",
            ha="right", fontsize=8.5, color=INK2)
    a1.set_xscale("log")
    a1.set_yscale("log")
    a1.set_ylim(0.7, 20000)
    a1.set_xlabel("frames used (count)")
    a1.set_ylabel("candidates still possible (count)")
    a1.set_title(f"After the frames (noise {sigma:g} x the contrast)",
                 loc="left", fontsize=11)
    a1.legend(frameon=False, fontsize=8.5, loc="upper right")
    tidy(a1)
    save(fig, "candidate-elimination")
    print(f"Candidate elimination ({n} cells, noise {sigma} x contrast, "
          f"median of {trials} trials):")
    print(f"  candidates: all {ncand}, obeying the 2-cell rule {allowed.size}")
    print("  frames  " + "  ".join(f"{k:>12s}" for k in names))
    for m, k in enumerate(marks):
        print(f"  {k:6d}  " + "  ".join(f"{med[q][m]:12.0f}" for q in names))
    print(f"  true pattern below the cut (frames, case): {truth_out}")


# --------------------------------------------------------------------------
# 11. Original units and the same figures scaled to this instrument
# --------------------------------------------------------------------------
AU_M = 1.495978707e11          # one astronomical unit, metres
PC_M = 3.0856775814913673e16   # one parsec, metres
MAS_RAD = np.pi / 180 / 3600 / 1000   # one thousandth of a second of arc

# name, pixel footprint, a second length (finest sample or error), what that
# second length is, distance to the scene; all in metres. For telescopes the
# footprint is the pixel angle times an example distance of 1000 parsecs.
STAR_M = 1000 * PC_M
SCALE_CASES = [
    ("SPOT 5 (Earth)", 5.0, 2.5, "output grid spacing", None),
    ("HiRISE (Mars)", 0.25, 0.0625, "pointing drift allowed in 10 ms", 250e3),
    # SkySat: the 0.6 m standard product is a 1.25 times enlargement, so the
    # camera pixel is 0.75 m; the measured gain in resolution is 0.10 m.
    ("SkySat (Earth)", 0.75, 0.10, "measured gain in resolution", None),
    ("PROBA-V (Earth)", 300.0, 100.0, "grid the result is scored on", 820e3),
    ("Hubble, star at 1000 parsecs", 100 * MAS_RAD * STAR_M,
     0.2 * MAS_RAD * STAR_M, "repeating position error left", STAR_M),
    ("Gaia, star at 1000 parsecs", 58.9 * MAS_RAD * STAR_M,
     0.3 * MAS_RAD * STAR_M, "position scatter per crossing", STAR_M),
]


def scale_map():
    """The scaling rule of the page: one pixel of the original instrument,
    measured on its scene, is set equal to one 1.12 micrometre pixel of this
    instrument. Every length on the original scene is divided by the same
    factor. Input figures are those cited in the page's scale tables."""
    pitch = PITCH_UM * 1e-6
    fig, ax = plt.subplots(figsize=(10.2, 4.6))
    print("Scaling: one original pixel on the scene = one 1.12 um pixel")
    for i, (name, px, other, what, dist) in enumerate(SCALE_CASES):
        y = len(SCALE_CASES) - 1 - i
        n = px / pitch
        ax.plot([pitch, px], [y, y], color=GRID, lw=1.2, zorder=0)
        ax.plot([other / n, other], [y - 0.28, y - 0.28], color=GRID, lw=1.2,
                zorder=0)
        ax.plot(px, y, "s", color=BLUE, ms=8)
        ax.plot(other, y - 0.28, "^", color=BLUE, ms=7)
        ax.plot(pitch, y, "s", color=ORANGE, ms=8)
        ax.plot(other / n, y - 0.28, "^", color=ORANGE, ms=7)
        ax.text(1e-13, y + 0.02, name, ha="right", va="center", fontsize=9)
        ax.text(1e-13, y - 0.28, what, ha="right", va="center", fontsize=8,
                color=INK2)
        mant, expo = f"{n:.1e}".split("e")
        ax.text(np.sqrt(pitch * px), y + 0.16,
                f"divide by {mant} $\\times 10^{{{int(expo)}}}$", fontsize=8,
                color=INK2, ha="center")
        nm = other / n * 1e9
        ax.text(other / n * 0.55, y - 0.28,
                f"{nm:.0f} nm" if nm >= 10 else f"{nm:.1f} nm",
                fontsize=8, color=ORANGE, ha="right", va="center")
        d = "" if dist is None else f", distance {dist:.4g} m -> {dist / n * 1e3:.4g} mm"
        print(f"  {name}: pixel {px:.4g} m, factor {n:.4g}, {what} "
              f"{other:.4g} m -> {other / n * 1e9:.4g} nm{d}")
    ax.set_xscale("log")
    ax.set_xlim(1e-12, 1e15)
    ax.set_ylim(-0.8, len(SCALE_CASES) - 0.4)
    ax.set_yticks([])
    ax.set_xlabel("length (metres)")
    ax.axvline(pitch, color=ORANGE, lw=0.8, ls=":")
    ax.text(pitch * 1.4, len(SCALE_CASES) - 0.55, "this instrument's pixel, "
            "1120 nm", fontsize=8.5, color=ORANGE)
    handles = [
        plt.Line2D([], [], marker="s", ls="", color=BLUE, ms=8,
                   label="one pixel on the original scene"),
        plt.Line2D([], [], marker="^", ls="", color=BLUE, ms=7,
                   label="a result in original units (tables S3, S4)"),
        plt.Line2D([], [], marker="s", ls="", color=ORANGE, ms=8,
                   label="the pixel after scaling"),
        plt.Line2D([], [], marker="^", ls="", color=ORANGE, ms=7,
                   label="the same result after scaling"),
    ]
    ax.legend(handles=handles, frameon=True, framealpha=1.0,
              facecolor=SURFACE, edgecolor=GRID, fontsize=8.5,
              loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.grid(True, axis="x", color=GRID, lw=0.6)
    save(fig, "scale-map")
    print(f"  1 mas at 1000 parsecs = {MAS_RAD * STAR_M / AU_M:.4f} AU = "
          f"{MAS_RAD * STAR_M / 1e3:.4g} km")
    print(f"  Gaia spin 60 arcsec/s = {60000 / 58.9:.1f} pixels/s = "
          f"{60000 / 58.9 * PITCH_UM / 1000:.3f} mm/s scaled; 4500 lines = "
          f"{4500 * 58.9 / 1000:.1f} arcsec = {4500 * PITCH_UM / 1000:.2f} mm")
    print(f"  Lucky imaging at 40 mas per pixel: 0.63 arcsec = "
          f"{630 / 40 * PITCH_UM:.1f} um, 0.26 arcsec = "
          f"{260 / 40 * PITCH_UM:.1f} um")


def main():
    tdi_map()
    tdi_mismatch()
    drizzle_kernel()
    random_dither_noise()
    pixel_cost()
    accuracy_chart()
    shift_bound()
    lucky_weighting()
    selfcal_tracks()
    candidate_elimination()
    scale_map()


if __name__ == "__main__":
    main()
