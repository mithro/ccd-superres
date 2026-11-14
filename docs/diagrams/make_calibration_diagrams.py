"""Generate the diagrams for docs/calibration-and-test.md.

Run from the repository root:

    python docs/diagrams/make_calibration_diagrams.py

Writes SVG (used by the document) and PNG copies next to this file, all with
the prefix ``calib-``, and prints the numbers quoted in the document.

Everything here is an analytic estimate or a small toy simulation written for
the figure. None of it is a result from the project's simulator levels.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle

OUT = Path(__file__).resolve().parent

# Same palette as make_diagrams.py so all figures match.
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#dddcd6"
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
YELLOW = "#eda100"
SILICON = "#c9c8c1"
MASK = "#3b3a37"
LIGHT = "#fff3c4"
VIOLET = "#7a52c7"

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

CROP_Y, CROP_X = 140, 120  # region of the toy scene shown in the FRC figure
PITCH_NM = 1120.0  # IMX219 pixel pitch
SENSOR_MM = 3.68  # IMX219 long side
WAVELENGTH_NM = 405.0


def save(fig, name):
    fig.savefig(OUT / f"calib-{name}.svg", bbox_inches="tight")
    fig.savefig(OUT / f"calib-{name}.png", bbox_inches="tight", dpi=160)
    plt.close(fig)


def tidy(ax):
    ax.grid(True, color=GRID, lw=0.6, which="major")
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def arrow(ax, p0, p1, color=INK, lw=1.4, style="-|>", scale=12, **kw):
    ax.add_patch(
        FancyArrowPatch(
            p0, p1, arrowstyle=style, mutation_scale=scale, color=color, lw=lw,
            shrinkA=0, shrinkB=0, **kw
        )
    )


# --------------------------------------------------------------------------
# 1. Which approach needs which calibration, and where it comes from
# --------------------------------------------------------------------------
def fig_map():
    approaches = [
        "Diffuse light,\nlinear blur",
        "Pulsed or\ncoded exposure",
        "Tubes or\ncollimator",
        "Collimated\ncoherent light",
        "Fringe or\nspeckle light",
        "Slanted beams,\nptychography",
        "Mask or diffuser\non the sensor",
        "Model fitting\n(scatterometry)",
    ]
    # 0 not needed, 1 solved from the scan data, 2 measured once then refined
    # from the data, 3 needs a dedicated measurement or an outside standard
    rows = [
        ("Pixel gain, offset, bad pixels", [1, 1, 1, 1, 1, 1, 1, 1]),
        ("Noise model and linearity", [3, 3, 3, 3, 3, 3, 3, 3]),
        ("Colour filter response per colour", [0, 0, 0, 2, 2, 2, 2, 3]),
        ("Pixel response shape (footprint)", [2, 2, 2, 2, 2, 2, 2, 0]),
        ("Pixel response to angle", [0, 0, 2, 2, 2, 3, 2, 3]),
        ("Frame positions, speed, yaw", [1, 1, 1, 1, 1, 1, 1, 1]),
        ("Length scale", [3, 3, 3, 3, 3, 3, 3, 3]),
        ("Gap and sensor tilt", [2, 2, 2, 1, 2, 1, 2, 2]),
        ("Row and frame timing", [2, 2, 2, 2, 2, 2, 2, 0]),
        ("Pulse or code timing", [0, 3, 0, 0, 0, 2, 0, 0]),
        ("Wavelength and bandwidth", [0, 0, 0, 2, 2, 2, 2, 3]),
        ("Beam direction and wavefront", [0, 0, 0, 1, 2, 1, 1, 3]),
        ("Coherence (mixture of patterns)", [0, 0, 0, 1, 1, 1, 1, 0]),
        ("Light pattern or fringe phase", [0, 0, 0, 0, 1, 1, 0, 0]),
        ("Added element (tube, mask) geometry", [0, 0, 3, 0, 0, 0, 2, 0]),
        ("Polarisation", [0, 0, 0, 0, 3, 3, 0, 3]),
        ("Reflectance and height scale", [3, 3, 3, 3, 3, 3, 3, 3]),
    ]
    data = np.array([r[1] for r in rows])
    cmap = ListedColormap(["#f1f0ec", AQUA, YELLOW, ORANGE])
    fig, ax = plt.subplots(figsize=(11.2, 7.4))
    ax.imshow(data, cmap=cmap, vmin=0, vmax=3, aspect="auto")
    ax.set_xticks(range(len(approaches)))
    ax.set_xticklabels(approaches, fontsize=8.5)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows], fontsize=9.5)
    ax.set_xticks(np.arange(-0.5, len(approaches)), minor=True)
    ax.set_yticks(np.arange(-0.5, len(rows)), minor=True)
    ax.grid(which="minor", color=SURFACE, lw=2.5)
    ax.tick_params(which="both", length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    labels = {0: "", 1: "data", 2: "once,\nthen data", 3: "measure"}
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            ax.text(j, i, labels[data[i, j]], ha="center", va="center",
                    fontsize=7.5, color=INK, linespacing=0.95)
    handles = [
        Rectangle((0, 0), 1, 1, color="#f1f0ec"),
        Rectangle((0, 0), 1, 1, color=AQUA),
        Rectangle((0, 0), 1, 1, color=YELLOW),
        Rectangle((0, 0), 1, 1, color=ORANGE),
    ]
    ax.legend(
        handles,
        [
            "Not needed by this approach",
            "Solved from the scan data alone",
            "Measured once as a starting value, then refined from the data",
            "Needs a dedicated measurement or an outside standard",
        ],
        loc="upper center", bbox_to_anchor=(0.4, -0.02), ncol=2, frameon=False,
        fontsize=9,
    )
    save(fig, "map")


# --------------------------------------------------------------------------
# 2. Stage 0: two-beam fringe measurement
# --------------------------------------------------------------------------
def pixel_contrast(period_nm, edge_nm, width_nm=PITCH_NM):
    f = 1.0 / np.asarray(period_nm, dtype=float)
    return np.abs(np.sinc(width_nm * f)) * np.exp(-2 * np.pi**2 * edge_nm**2 * f**2)


def pixel_envelope(period_nm, edge_nm, width_nm=PITCH_NM):
    f = 1.0 / np.asarray(period_nm, dtype=float)
    return np.minimum(1.0, 1.0 / (np.pi * width_nm * f)) * np.exp(
        -2 * np.pi**2 * edge_nm**2 * f**2
    )


def fig_fringe():
    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(12, 4.6),
                                   gridspec_kw={"width_ratios": [1, 1.35]})
    # geometry: mirror standing on the sensor, one widened beam
    ax0.set_xlim(-0.3, 6.4)
    ax0.set_ylim(-1.3, 4.6)
    ax0.set_aspect("equal")
    ax0.axis("off")
    ax0.add_patch(Rectangle((0, -0.35), 5.6, 0.35, color=SILICON, ec=INK2, lw=0.8))
    ax0.text(2.8, -1.08, "sensor, lenses removed", ha="center", color=INK2)
    ax0.add_patch(Rectangle((-0.12, 0), 0.12, 3.9, color=MASK))
    ax0.text(-0.2, 4.15, "mirror", ha="left", color=INK2)
    th = np.radians(55)
    d = np.array([-np.sin(th), -np.cos(th)])
    for x in (1.0, 2.2, 3.4):  # direct rays
        p1 = np.array([x, 0.0])
        arrow(ax0, p1 - 3.4 * d, p1, color=VIOLET, lw=1.3)
    for y in (1.0, 1.9):  # rays that reflect off the mirror first
        hit = np.array([0.0, y])
        start = hit - 2.6 * d
        ax0.plot([start[0], hit[0]], [start[1], hit[1]], color=VIOLET, lw=1.3)
        land = np.array([y * np.tan(th), 0.0])
        arrow(ax0, hit, land, color=VIOLET, lw=1.3, ls="--")
    ax0.plot([4.6, 4.6], [0, 1.5], color=INK2, lw=0.7, ls=":")
    ax0.annotate("", xy=(4.6 + 1.0 * np.sin(th), 1.0 * np.cos(th)), xytext=(4.6, 1.0),
                 arrowprops=dict(arrowstyle="-", color=INK2, lw=0.7,
                                 connectionstyle="arc3,rad=-0.3"))
    ax0.text(4.78, 1.25, "θ", color=INK2, fontsize=11)
    xs = np.linspace(0.05, 2.9, 30)
    for i, x in enumerate(xs):
        ax0.add_patch(Rectangle((x, 0.0), 0.045, 0.1,
                                color=VIOLET if i % 2 else LIGHT, lw=0))
    ax0.text(1.5, -0.72, "fringes, period λ / (2 sin θ)", ha="center", fontsize=8.5,
             color=INK)
    ax0.text(3.5, 4.25, "one widened laser beam", color=VIOLET, ha="center")
    ax0.set_title("Arrangement: a mirror turns one beam into two", fontsize=10.5)

    period = np.geomspace(150, 6000, 3000)
    ax1.plot(period, pixel_contrast(period, 0), color=GRID, lw=1.0,
             label="Ideal square pixel, exact")
    for edge, col in ((0, INK), (30, BLUE), (50, AQUA), (100, ORANGE)):
        ax1.plot(period, pixel_envelope(period, edge), color=col, lw=1.8,
                 label=f"Envelope, edges soft over {edge} nm" if edge else
                 "Envelope, perfectly sharp edges")
    ax1.axvspan(150, WAVELENGTH_NM / 2, color=MASK, alpha=0.12, lw=0)
    ax1.text(175, 1.6e-4, "not reachable\nin air at 405 nm", fontsize=8, color=INK2,
             ha="center", rotation=90, va="bottom")
    ax1.axvline(PITCH_NM, color=INK2, lw=0.8, ls=":")
    ax1.text(PITCH_NM * 1.05, 1.5e-4, "pixel pitch", fontsize=8, color=INK2)
    ax1.set_xscale("log")
    ax1.set_yscale("log")
    ax1.set_ylim(1e-4, 1.5)
    ax1.set_xlim(150, 6000)
    ax1.set_xlabel("Fringe period on the sensor (nm)")
    ax1.set_ylabel("Fraction of fringe contrast a pixel records")
    ax1.set_xticks([200, 300, 500, 1000, 2000, 5000])
    ax1.set_xticklabels(["200", "300", "500", "1000", "2000", "5000"])
    ax1.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax1.legend(frameon=False, fontsize=8.5, loc="lower right",
               bbox_to_anchor=(1.0, 0.08))
    ax1.set_title("What the measurement is expected to show", fontsize=10.5)
    tidy(ax1)
    save(fig, "fringe-response")

    print("Fringe response of a 1120 nm square pixel (envelope):")
    for p in (203, 213, 290, 400):
        print(f"  period {p} nm:", ", ".join(
            f"edge {e} nm -> {pixel_envelope(p, e):.4f}" for e in (0, 30, 50, 100)))
    for th_deg in (10, 30, 60, 72, 85):
        print(f"  theta {th_deg} deg -> period "
              f"{WAVELENGTH_NM / (2 * np.sin(np.radians(th_deg))):.0f} nm")


# --------------------------------------------------------------------------
# 3. Tolerances
# --------------------------------------------------------------------------
def fig_tolerances():
    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(12, 4.5))
    sigma = np.geomspace(1, 1000, 400)
    for period, col in ((2000, INK), (400, BLUE), (290, AQUA), (200, ORANGE)):
        ax0.plot(sigma, np.exp(-2 * np.pi**2 * sigma**2 / period**2), color=col,
                 lw=1.8, label=f"{period} nm period")
    ax0.axhline(0.9, color=INK2, lw=0.8, ls=":")
    ax0.text(1.1, 0.915, "10% loss", fontsize=8, color=INK2)
    ax0.set_xscale("log")
    ax0.set_xlabel("Unknown random error in position (nm, root mean square)")
    ax0.set_ylabel("Contrast kept")
    ax0.set_title("Position errors the reconstruction does not know about",
                  fontsize=10.5)
    ax0.legend(frameon=False, fontsize=9)
    tidy(ax0)

    rel = np.geomspace(1e-7, 3e-2, 400)
    fringe_nm = WAVELENGTH_NM / (2 * np.sin(np.radians(72)))
    for half_mm, col in ((1.84, ORANGE), (0.5, AQUA), (0.1, BLUE)):
        n = half_mm * 1e6 / fringe_nm
        ax1.plot(rel, n * rel, color=col, lw=1.8,
                 label=f"{half_mm} mm from the line of equal paths")
    ax1.axhline(0.25, color=INK2, lw=0.8, ls=":")
    ax1.text(1.2e-7, 0.3, "quarter of a fringe", fontsize=8, color=INK2)
    marks = [
        (0.0001 / 405, "single-frequency\nlaser, 0.1 pm"),
        (0.05 / 405, "1 K of diode\nwarming"),
        (0.5 / 405, "plain diode\nwidth, 0.5 nm"),
        (5 / 405, "unit to unit,\n±5 nm"),
    ]
    for k, (x, text) in enumerate(marks):
        ax1.axvline(x, color=VIOLET, lw=0.9, ls="--")
        ax1.text(x * (1.12 if k == 0 else 0.88), 3e-4 * 6 ** (k % 2), text,
                 fontsize=7.5, color=VIOLET, va="bottom",
                 ha="left" if k == 0 else "right")
    ax1.set_xscale("log")
    ax1.set_yscale("log")
    ax1.set_ylim(2e-4, 300)
    ax1.set_xlabel("Relative error or spread in wavelength (or in sin θ)")
    ax1.set_ylabel("Fringe slip at that distance (fringes)")
    ax1.set_title("Beam pair at ±72°: fringes of 213 nm period", fontsize=10.5)
    ax1.legend(fontsize=8.5, loc="upper left", framealpha=0.95, edgecolor=GRID,
               facecolor=SURFACE)
    tidy(ax1)
    save(fig, "tolerances")

    print("Position error for 10% contrast loss:")
    for period in (2000, 400, 290, 200):
        print(f"  {period} nm period: {period * np.sqrt(-np.log(0.9) / (2 * np.pi**2)):.1f} nm")
    n_half = 1.84e6 / fringe_nm
    print(f"Fringe period {fringe_nm:.1f} nm, fringes over half field {n_half:.0f}")
    print(f"  quarter-fringe relative tolerance {0.25 / n_half:.2e} "
          f"= {0.25 / n_half * 405 * 1000:.1f} pm")
    for width_nm in (2.0, 0.5, 0.0001):
        lc_mm = 405e-9**2 / (width_nm * 1e-9) * 1e3
        half = lc_mm / (2 * 2 * np.sin(np.radians(72)))
        print(f"  width {width_nm} nm: coherence length about {lc_mm:.3g} mm, "
              f"fringes within about ±{half:.3g} mm of the equal-path line")
    print(f"  path difference across the 3.68 mm sensor: "
          f"{3.68 * 2 * np.sin(np.radians(72)):.1f} mm")


# --------------------------------------------------------------------------
# 4. Reference samples against the stage targets
# --------------------------------------------------------------------------
def fig_targets():
    samples = [
        ("USAF 1951 chrome-on-glass slide, to group 9", 1096, 100000, INK2),
        ("Compact disc, track pitch", 1600, 1600, BLUE),
        ("DVD, track pitch", 740, 740, BLUE),
        ("Blu-ray disc, track pitch", 320, 320, BLUE),
        ("Holographic gratings, 1200 to 3600 lines per mm", 278, 833, AQUA),
        ("Probe-microscope pitch standard (TDG01), 278 ± 1 nm", 278, 278, AQUA),
        ("NIST RM 8820 scale artifact, 200 nm upwards", 200, 100000, AQUA),
        ("SKY130 chip: metal 5 (top), 1.6 µm lines", 3200, 3200, ORANGE),
        ("SKY130 chip: metal 3 and 4, 300 nm lines", 600, 600, ORANGE),
        ("SKY130 chip: polysilicon, 150 nm lines", 360, 360, ORANGE),
        ("SKY130 chip: local interconnect, 170 nm lines", 340, 340, ORANGE),
        ("SKY130 chip: metal 1 and 2, 140 nm lines", 280, 280, ORANGE),
        ("Custom electron-beam target: star and bars", 100, 100000, VIOLET),
    ]
    fig, ax = plt.subplots(figsize=(11.5, 5.6))
    top = len(samples)
    for lo, hi, alpha in ((2000, 100000, 0.22), (300, 400, 0.22), (225, 290, 0.1),
                          (200, 225, 0.22)):
        ax.axvspan(lo, hi, color=YELLOW, alpha=alpha, lw=0)
    ax.text(14000, top - 0.2, "Stage 1: coarse picture", ha="center", va="bottom",
            fontsize=8.5)
    ax.text(410, top - 0.2, "Stage 2: expected", ha="left", va="bottom", fontsize=8.5)
    ax.text(255, top + 0.6, "Stage 2: limit", ha="center", va="bottom", fontsize=8.5,
            color=INK2)
    ax.text(195, top - 0.2, "Stages 3 and 4:\ntarget", ha="right", va="bottom",
            fontsize=8.5)
    for i, (name, lo, hi, col) in enumerate(samples):
        y = len(samples) - 1 - i
        if lo == hi:
            ax.plot([lo], [y], marker="D", color=col, ms=7)
        else:
            ax.plot([lo, hi], [y, y], color=col, lw=6, solid_capstyle="butt")
        ax.text(0.985, y, name, transform=ax.get_yaxis_transform(), ha="right",
                va="center", fontsize=8.8, color=INK,
                bbox=dict(fc=SURFACE, ec="none", pad=1.0, alpha=0.85))
    ax.set_xscale("log")
    ax.set_xlim(90, 3e6)
    ax.set_ylim(-0.7, len(samples) + 1.6)
    ax.set_yticks([])
    ax.set_xticks([100, 200, 500, 1000, 2000, 5000, 10000, 100000])
    ax.set_xticklabels(["100 nm", "200 nm", "500 nm", "1 µm", "2 µm", "5 µm", "10 µm",
                        "100 µm"])
    ax.set_xlabel("Period of the pattern (one line plus one space)")
    ax.grid(True, axis="x", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    save(fig, "targets")


# --------------------------------------------------------------------------
# 5. Fourier ring correlation, and how a prior can fool the split-data form
# --------------------------------------------------------------------------
def ring_correlation(a, b, nbins=64):
    fa = np.fft.fftshift(np.fft.fft2(a - a.mean()))
    fb = np.fft.fftshift(np.fft.fft2(b - b.mean()))
    n = a.shape[0]
    y, x = np.indices(a.shape) - n // 2
    r = np.hypot(x, y)
    edges = np.linspace(0, n // 2, nbins + 1)
    idx = np.digitize(r.ravel(), edges) - 1
    ok = (idx >= 0) & (idx < nbins)
    num = np.bincount(idx[ok], (fa * fb.conj()).real.ravel()[ok], nbins)
    da = np.bincount(idx[ok], (np.abs(fa) ** 2).ravel()[ok], nbins)
    db = np.bincount(idx[ok], (np.abs(fb) ** 2).ravel()[ok], nbins)
    freq = 0.5 * (edges[:-1] + edges[1:]) / n  # cycles per grid cell
    return freq, num / np.sqrt(da * db + 1e-30)


def make_layout(rng, n=512):
    """Wiring-like pattern: isolated lines, dense line groups, and a third level."""
    img = np.zeros((n, n))
    for _ in range(60):  # isolated lines, 4 or 12 cells wide
        w = rng.choice([4, 12])
        length = rng.integers(40, 160)
        x, y = rng.integers(0, n, 2)
        if rng.random() < 0.5:
            img[y:y + w, x:x + length] = 1
        else:
            img[y:y + length, x:x + w] = 1
    for _ in range(40):  # dense groups: 4-cell lines on an 8-cell period
        x, y = rng.integers(0, n - 64, 2)
        size = rng.integers(40, 64)
        img[y:y + size, x:x + size] = 0
        lines = (np.arange(size) % 8) < 4
        if rng.random() < 0.5:
            img[y:y + size, x:x + size] = lines[None, :]
        else:
            img[y:y + size, x:x + size] = lines[:, None]
    for _ in range(12):  # a third material the two-level prior does not allow
        x, y = rng.integers(0, n - 40, 2)
        img[y:y + 30, x:x + 30] = 0.5
    return img


def fig_frc():
    rng = np.random.default_rng(7)
    n = 512
    truth = make_layout(rng, n)
    fy = np.fft.fftfreq(n)[:, None]
    fx = np.fft.fftfreq(n)[None, :]
    fr = np.hypot(fx, fy)
    cutoff = 0.06  # cycles per grid cell: the finest period measured is ~17 cells
    transfer = np.exp(-0.5 * (fr / (cutoff / 2)) ** 2)

    def measure():
        blurred = np.fft.ifft2(np.fft.fft2(truth) * transfer).real
        return blurred + rng.normal(0, 0.05, truth.shape)

    def linear(data):  # Wiener-type inverse: recovers what the data supports
        w = transfer / (transfer**2 + 0.02)
        return np.fft.ifft2(np.fft.fft2(data) * w).real

    def with_prior(data):  # strong "two materials" prior: force to 0 or 1
        return (linear(data) > 0.5).astype(float)

    d1, d2 = measure(), measure()
    l1, l2 = linear(d1), linear(d2)
    p1, p2 = with_prior(d1), with_prior(d2)

    curves = {
        "linear, half against half": ring_correlation(l1, l2),
        "linear, against truth": ring_correlation(l1, truth),
        "prior, half against half": ring_correlation(p1, p2),
        "prior, against truth": ring_correlation(p1, truth),
    }

    def crossing(freq, c, level=1 / 7):
        below = np.where(c < level)[0]
        return freq[below[0]] if len(below) else np.nan

    fig = plt.figure(figsize=(12, 7.6))
    gs = fig.add_gridspec(2, 3, height_ratios=[1, 1.15], hspace=0.28, wspace=0.12)
    crop = (slice(CROP_Y, CROP_Y + 160), slice(CROP_X, CROP_X + 160))
    for k, (img, title) in enumerate((
        (truth, "Truth: fine lines are 4 cells wide, 8-cell period"),
        (l1, "Linear reconstruction of half the data"),
        (p1, "Reconstruction forced to two levels"),
    )):
        ax = fig.add_subplot(gs[0, k])
        ax.imshow(img[crop], cmap="gray", vmin=-0.1, vmax=1.1, interpolation="nearest")
        ax.set_title(title, fontsize=10)
        ax.set_xticks([])
        ax.set_yticks([])
    ax = fig.add_subplot(gs[1, :])
    styles = {
        "linear, half against half": (BLUE, "-"),
        "linear, against truth": (BLUE, ":"),
        "prior, half against half": (ORANGE, "-"),
        "prior, against truth": (ORANGE, ":"),
    }
    names = {
        "linear, half against half": "Linear: one half of the data against the other",
        "linear, against truth": "Linear: against the truth",
        "prior, half against half": "Two-level prior: one half against the other",
        "prior, against truth": "Two-level prior: against the truth",
    }
    print("Fourier ring correlation toy model, 1/7 crossings (period in cells):")
    for key, (freq, c) in curves.items():
        col, ls = styles[key]
        ax.plot(freq, c, color=col, ls=ls, lw=1.9, label=names[key])
        fc = crossing(freq, c)
        print(f"  {key}: frequency {fc:.3f}, period {1 / fc:.1f} cells")
    ax.axhline(1 / 7, color=INK2, lw=0.8, ls="--")
    ax.text(0.29, 1 / 7 + 0.02, "threshold 1/7", fontsize=8.5, color=INK2, ha="right")
    ax.axvline(1 / 8, color=INK2, lw=0.8, ls=":")
    ax.text(1 / 8 + 0.003, 0.93, "period of the\nfine lines (8 cells)", fontsize=8.5,
            color=INK2, va="top")
    ax.set_xlim(0, 0.3)
    ax.set_ylim(-0.15, 1.02)
    ax.set_xlabel("Spatial frequency (cycles per grid cell)")
    ax.set_ylabel("Fourier ring correlation")
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    tidy(ax)
    save(fig, "frc-demo")


# --------------------------------------------------------------------------
# 6. Photon transfer rehearsal
# --------------------------------------------------------------------------
def fig_photon_transfer():
    rng = np.random.default_rng(3)
    full_well, read_e, bits, prnu = 4500.0, 3.0, 10, 0.01
    k_true = full_well / (2**bits - 1 - 64)  # electrons per count, 64 count pedestal
    shape = (200, 200)
    gain_map = 1 + prnu * rng.standard_normal(shape)
    levels = np.geomspace(5, 4300, 28)
    mean, var_pair, var_single = [], [], []
    for e in levels:
        frames = []
        for _ in range(2):
            electrons = rng.poisson(e * gain_map) + rng.normal(0, read_e, shape)
            frames.append(np.clip(np.round(electrons / k_true + 64), 0, 2**bits - 1))
        a, b = frames
        mean.append(0.5 * (a.mean() + b.mean()) - 64)
        var_pair.append(np.var(a - b) / 2)
        var_single.append(np.var(a))
    mean, var_pair, var_single = map(np.array, (mean, var_pair, var_single))
    fit = mean < 0.8 * mean.max()
    slope, intercept = np.polyfit(mean[fit], var_pair[fit], 1)
    k_est = 1 / slope
    read_est = np.sqrt(max(intercept - 1 / 12, 0)) * k_est
    print(f"Photon transfer rehearsal: true {k_true:.3f} e/count, {read_e} e read noise")
    print(f"  recovered {k_est:.3f} e/count, {read_est:.2f} e read noise")

    fig, (ax0, ax) = plt.subplots(1, 2, figsize=(12, 4.4),
                                  gridspec_kw={"width_ratios": [1, 1.5]})
    ax0.set_xlim(0, 10)
    ax0.set_ylim(0, 8)
    ax0.axis("off")
    ax0.add_patch(plt.Circle((5, 7.0), 0.35, color=YELLOW))
    ax0.text(5.6, 7.0, "small steady lamp\n(not a laser)", va="center", fontsize=9)
    for x in (2.6, 3.8, 5.0, 6.2, 7.4):
        arrow(ax0, (5, 6.6), (x, 1.75), color=YELLOW, lw=1.0, scale=9)
    ax0.add_patch(Rectangle((2.2, 1.2), 5.6, 0.45, color=SILICON, ec=INK2, lw=0.8))
    ax0.text(5, 0.7, "bare sensor, in the dark", ha="center", color=INK2, fontsize=9)
    ax0.annotate("", xy=(1.5, 6.9), xytext=(1.5, 1.7),
                 arrowprops=dict(arrowstyle="<->", color=INK, lw=0.9))
    ax0.text(1.3, 4.3, "far enough for\neven light", ha="right", va="center",
             fontsize=8.5)
    ax0.text(5, 0.05, "Two frames at each of about 30 light levels,\nplus frames "
             "with the lamp off", ha="center", fontsize=8.5)
    ax0.set_title("Arrangement", fontsize=10.5)
    ax.set_title("Simulated measurement and the values recovered", fontsize=10.5)
    ax.plot(mean, var_single, "o", color=ORANGE, ms=4.5,
            label="Variance of one frame (includes fixed gain differences)")
    ax.plot(mean, var_pair, "o", color=BLUE, ms=4.5,
            label="Half the variance of the difference of two frames")
    xs = np.geomspace(mean.min(), mean.max(), 100)
    ax.plot(xs, slope * xs + intercept, color=INK, lw=1.1,
            label=f"Fit: {k_est:.2f} electrons per count, read noise {read_est:.1f} e")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Mean signal above the dark level (counts)")
    ax.set_ylabel("Variance (counts squared)")
    ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    tidy(ax)
    save(fig, "photon-transfer")


# --------------------------------------------------------------------------
# 7. The anchors: what the data cannot tell apart
# --------------------------------------------------------------------------
def fig_anchors():
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.9))
    for ax in axes:
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 7)
        ax.axis("off")

    def chip(ax, x0, y0, w, n, col=ORANGE):
        ax.add_patch(Rectangle((x0, y0), w, 0.5, color=SILICON, ec=INK2, lw=0.8))
        step = w / (2 * n)
        for i in range(n):
            ax.add_patch(Rectangle((x0 + (2 * i + 0.5) * step, y0 + 0.5), step, 0.22,
                                   color=col, lw=0))

    def sensor(ax, x0, y0, w, n):
        for i in range(n):
            ax.add_patch(Rectangle((x0 + i * w / n, y0), w / n * 0.92, 0.45, color=BLUE,
                                   alpha=0.85, lw=0))

    # length
    ax = axes[0]
    ax.set_title("Length: big and fast, or small and slow?", fontsize=10.5)
    sensor(ax, 0.6, 5.4, 3.6, 6)
    chip(ax, 0.4, 4.2, 4.0, 4)
    arrow(ax, (1.2, 6.3), (3.6, 6.3), color=INK)
    ax.text(2.4, 6.45, "speed 2", ha="center", fontsize=8.5)
    ax.text(2.4, 3.75, "pattern period 2", ha="center", fontsize=8.5, color=INK2)
    sensor(ax, 6.2, 5.4, 1.8, 6)
    chip(ax, 6.1, 4.2, 2.0, 4)
    arrow(ax, (6.5, 6.3), (7.7, 6.3), color=INK)
    ax.text(7.1, 6.45, "speed 1", ha="center", fontsize=8.5)
    ax.text(7.1, 3.75, "pattern period 1", ha="center", fontsize=8.5, color=INK2)
    ax.text(5.1, 2.6, "Both give identical frames.\nAnchor: one known length\n"
            "(pixel spacing, wavelength,\nor a grating of known period).", ha="center",
            va="top", fontsize=9)
    # brightness
    ax = axes[1]
    ax.set_title("Brightness: strong light, or shiny surface?", fontsize=10.5)
    for x0, n_in, refl, lab in ((1.0, 6, 0.33, "strong light,\ndull surface"),
                                (6.0, 3, 0.67, "weak light,\nshiny surface")):
        ax.add_patch(Rectangle((x0, 3.9), 3.0, 0.5, color=SILICON, ec=INK2, lw=0.8))
        for i in range(n_in):
            x = x0 + 0.3 + i * 1.6 / max(n_in - 1, 1) * (1 if n_in > 1 else 0)
            arrow(ax, (x - 0.5, 6.4), (x + 0.3, 4.45), color=VIOLET, lw=1.1, scale=8)
        for i in range(2):
            x = x0 + 1.9 + 0.45 * i
            arrow(ax, (x, 4.45), (x + 0.8, 6.4), color=VIOLET, lw=1.1, scale=8)
        ax.text(x0 + 1.5, 3.45, lab, ha="center", va="top", fontsize=8.5, color=INK2)
    ax.text(5.1, 2.0, "Both return the same light.\nAnchor: one area of known\n"
            "reflectance (bare silicon).", ha="center", va="top", fontsize=9)
    # height
    ax = axes[2]
    ax.set_title("Height: read in units of the wavelength", fontsize=10.5)
    ax.add_patch(Rectangle((1.0, 3.9), 8.0, 0.5, color=SILICON, ec=INK2, lw=0.8))
    ax.add_patch(Rectangle((4.2, 4.4), 2.4, 0.7, color=ORANGE, lw=0))
    xs = np.linspace(1.2, 4.0, 200)
    ax.plot(xs, 6.0 + 0.3 * np.sin(2 * np.pi * (xs - 1.2) / 0.7), color=VIOLET, lw=1.2)
    xs2 = np.linspace(4.3, 6.5, 200)
    ax.plot(xs2, 6.0 + 0.3 * np.sin(2 * np.pi * (xs2 - 1.2) / 0.7 + 1.6), color=VIOLET,
            lw=1.2)
    ax.annotate("", xy=(6.9, 5.1), xytext=(6.9, 4.4),
                arrowprops=dict(arrowstyle="<->", color=INK, lw=0.9))
    ax.text(7.05, 4.75, "step h", fontsize=8.5, va="center")
    ax.text(5.4, 6.55, "wave shifted by 4π h cos θ / λ", ha="center", fontsize=8.5,
            color=VIOLET)
    ax.text(5.0, 2.6, "The shift gives h only if the\nwavelength λ and light angle θ\n"
            "are known. Check: a step of\nknown height.", ha="center", va="top",
            fontsize=9)
    save(fig, "anchors")


# --------------------------------------------------------------------------
# 8. Beat pattern: how coarse pixels read fine fringes
# --------------------------------------------------------------------------
def fig_beat():
    n = 48
    fringe = WAVELENGTH_NM / (2 * np.sin(np.radians(72)))
    rot = np.radians(4.0)
    fx, fy = np.cos(rot) / fringe, np.sin(rot) / fringe
    j, i = np.mgrid[0:n, 0:n]
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.0),
                             gridspec_kw={"width_ratios": [1, 1, 1.25]})
    rows = {}
    for ax, edge in zip(axes[:2], (0, 50)):
        c = (np.sinc(PITCH_NM * fx) * np.sinc(PITCH_NM * fy)
             * np.exp(-2 * np.pi**2 * edge**2 * (fx**2 + fy**2)))
        img = 1 + c * np.cos(2 * np.pi * PITCH_NM * (fx * i + fy * j))
        rows[edge] = img[n // 2]
        ax.imshow(img, cmap="gray", vmin=0.93, vmax=1.07, interpolation="nearest")
        ax.set_title(f"Pixel edges soft over {edge} nm" if edge else
                     "Perfectly sharp pixel edges", fontsize=10)
        ax.set_xlabel("Pixel column")
        ax.set_ylabel("Pixel row")
    ax = axes[2]
    for edge, col in ((0, INK), (50, AQUA)):
        ax.plot(100 * (rows[edge] - 1), color=col, lw=1.4, marker="o", ms=2.5,
                label=f"edges soft over {edge} nm" if edge else "sharp edges")
    ax.set_xlabel("Pixel column, along one row")
    ax.set_ylabel("Reading, change from the mean (%)")
    ax.set_title("The stripe strength is the pixel's response", fontsize=10)
    ax.set_ylim(-4.2, 5.6)
    ax.legend(frameon=False, fontsize=8.5, loc="upper right", ncol=2)
    tidy(ax)
    fig.tight_layout()
    save(fig, "beat")
    beat = 1 / abs(PITCH_NM * fx - round(PITCH_NM * fx))
    print(f"Beat pattern: {PITCH_NM / fringe:.3f} fringes per pixel, "
          f"beat period {beat:.2f} pixels along a row")


# --------------------------------------------------------------------------
# 9. Coherence: where the fringes of a beam pair are visible
# --------------------------------------------------------------------------
def visibility(x_mm, width_nm, theta_deg=72.0):
    """Fringe contrast at distance x from the equal-path line, Gaussian spectrum."""
    path_nm = 2 * np.abs(x_mm) * 1e6 * np.sin(np.radians(theta_deg))
    lc_nm = WAVELENGTH_NM**2 / width_nm
    return np.exp(-(np.pi * path_nm / lc_nm) ** 2 / (4 * np.log(2)))


def fig_coherence():
    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(12.5, 4.3),
                                   gridspec_kw={"width_ratios": [1, 1.3]})
    ax0.set_xlim(-4.2, 4.2)
    ax0.set_ylim(-1.5, 4.2)
    ax0.set_aspect("equal")
    ax0.axis("off")
    ax0.add_patch(Rectangle((-3.4, -0.35), 6.8, 0.35, color=SILICON, ec=INK2, lw=0.8))
    ax0.text(0, -0.75, "sensor or chip, 3.68 mm across", ha="center", color=INK2)
    th = np.radians(55)
    for sgn in (-1, 1):
        d = np.array([sgn * np.sin(th), -np.cos(th)])
        for x in (-2.0, 0.0, 2.0):
            p1 = np.array([x, 0.0])
            arrow(ax0, p1 - 3.6 * d, p1, color=VIOLET, lw=1.2)
    ax0.plot([0, 0], [0, 3.6], color=INK, lw=0.9, ls="--")
    ax0.text(0.1, 3.75, "line of equal paths", fontsize=8.5, ha="center")
    ax0.annotate("", xy=(2.0, -1.05), xytext=(0, -1.05),
                 arrowprops=dict(arrowstyle="<->", color=INK, lw=0.9))
    ax0.text(1.0, -1.42, "x: paths differ by 2 x sin θ", ha="center", fontsize=8.5)
    ax0.set_title("Two beams from one laser, from opposite sides", fontsize=10.5)

    x = np.linspace(-1.84, 1.84, 2000)
    for width, col, lab in ((2.0, ORANGE, "2 nm (multimode diode)"),
                            (0.5, YELLOW, "0.5 nm (single-mode diode)"),
                            (0.05, AQUA, "0.05 nm"),
                            (0.0001, BLUE, "0.0001 nm (single-frequency laser)")):
        ax1.plot(x, visibility(x, width), color=col, lw=1.9, label=lab)
    ax1.axhline(0.5, color=INK2, lw=0.8, ls=":")
    ax1.set_xlabel("Position across the sensor, from the line of equal paths (mm)")
    ax1.set_ylabel("Fringe contrast")
    ax1.set_title("Fringe contrast for four spectral widths of the laser", fontsize=10.5)
    ax1.legend(frameon=False, fontsize=8.5, loc="upper center", ncol=2,
               bbox_to_anchor=(0.5, -0.17), title="Spectral width of the laser")
    tidy(ax1)
    save(fig, "coherence")
    print("Half-contrast half-width of the fringe strip at ±72 degrees:")
    for width in (2.0, 0.5, 0.05, 0.0001):
        lc = WAVELENGTH_NM**2 / width * 1e-6
        half = lc * 2 * np.log(2) / np.pi / (2 * np.sin(np.radians(72)))
        print(f"  width {width} nm: coherence length {lc:.3g} mm, strip ±{half:.3g} mm")


# --------------------------------------------------------------------------
# 10. Timing check with a strobed light
# --------------------------------------------------------------------------
def fig_timing():
    rng = np.random.default_rng(5)
    line_true = 18.9e-6 * 1.004  # hidden: 0.4% longer than the nominal 18.9 µs
    strobe_hz, duty, exposure_lines = 1000.0, 0.1, 4
    rows = np.arange(600)

    def light_fraction(t0, t1):
        period = 1 / strobe_hz
        on = duty * period
        def integral(t):
            whole = np.floor(t / period)
            return whole * on + np.minimum(t - whole * period, on)
        return (integral(t1) - integral(t0)) / (t1 - t0)

    start = rows * line_true
    profile = light_fraction(start, start + exposure_lines * line_true)
    img = profile[:, None] * np.ones((1, 200)) * 600 + rng.normal(0, 6, (600, 200))
    row_mean = img.mean(axis=1)
    spec = np.abs(np.fft.rfft(row_mean - row_mean.mean(), 1 << 18))
    freqs = np.fft.rfftfreq(1 << 18)
    f_peak = freqs[np.argmax(spec)]
    spacing = 1 / f_peak
    line_est = 1 / (strobe_hz * spacing)
    print(f"Timing rehearsal: hidden line time {line_true * 1e6:.3f} us, "
          f"band spacing {spacing:.2f} rows, recovered {line_est * 1e6:.3f} us")

    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(11.5, 4.2),
                                   gridspec_kw={"width_ratios": [1, 1.6]})
    ax0.imshow(img[:260], cmap="gray", aspect="auto", interpolation="nearest")
    ax0.set_xlabel("Pixel column")
    ax0.set_ylabel("Pixel row (read one after another)")
    ax0.set_title("Simulated frame under a light\nflashing 1000 times a second",
                  fontsize=10)
    ax1.plot(rows[:260], row_mean[:260], color=BLUE, lw=1.3)
    peaks = [k for k in range(1, 259) if row_mean[k] > row_mean[k - 1]
             and row_mean[k] >= row_mean[k + 1] and row_mean[k] > 0.8 * row_mean.max()]
    if len(peaks) >= 2:
        a, b = peaks[0], peaks[0] + spacing
        y = row_mean.max() * 1.08
        ax1.annotate("", xy=(b, y), xytext=(a, y),
                     arrowprops=dict(arrowstyle="<->", color=INK, lw=0.9))
        ax1.text((a + b) / 2, y * 1.03, f"{spacing:.1f} rows = 1 ms", ha="center",
                 fontsize=9)
    ax1.set_ylim(0, row_mean.max() * 1.25)
    ax1.set_xlabel("Pixel row")
    ax1.set_ylabel("Mean reading of the row (counts)")
    ax1.set_title(f"Band spacing gives the row time: {line_est * 1e6:.2f} µs recovered, "
                  f"{line_true * 1e6:.2f} µs true", fontsize=10)
    tidy(ax1)
    save(fig, "timing")


# --------------------------------------------------------------------------
# 11. The benchmark scenes
# --------------------------------------------------------------------------
def scene_bars(n=240):
    img = np.zeros((n, n))
    x = 8
    for period in (24, 16, 12, 8, 6, 4):
        w = period // 2
        for k in range(4):
            img[10:105, x + k * period: x + k * period + w] = 1
        x += 4 * period + 6
    y = 125
    for period in (16, 12, 8, 6, 4):
        w = period // 2
        for k in range(3):
            img[y + k * period: y + k * period + w, 20:220] = 1
        y += 3 * period + 5
    return img


def scene_star(n=240, spokes=18):
    y, x = np.indices((n, n)) - n / 2
    return ((np.sin(spokes * np.arctan2(y, x)) > 0) & (np.hypot(x, y) < n * 0.46)) * 1.0


def scene_isolated(n=240):
    img = np.zeros((n, n))
    img[:, :70] = 1
    img[20:220, 110:114] = 1
    for k, sep in enumerate((4, 6, 8, 12, 16)):
        yy = 30 + 44 * k
        img[yy:yy + 3, 170:173] = 1
        img[yy:yy + 3, 170 + sep:173 + sep] = 1
    return img


def scene_grating(n=240):
    return (((np.arange(n) % 8) < 4) * 1.0)[None, :] * np.ones((n, 1))


def scene_steps(n=240):
    img = np.zeros((n, n))
    for k, h in enumerate((0.2, 0.4, 0.6, 0.8, 1.0)):
        img[30:210, 20 + 44 * k: 44 + 44 * k] = h
    return img


def scene_silicon(rng, n=240, defect=True):
    img = np.zeros((n, n))
    for y in range(12, 110, 8):
        img[y:y + 4, 10:150] = 1
    for x in range(160, 232, 8):
        img[10:120, x:x + 4] = 1
    for y in range(130, 230, 12):
        for x in range(12, 110, 12):
            img[y:y + 4, x:x + 4] = 1
    img[130:134, 125:230] = 1
    img[130:228, 226:230] = 1
    img[160:164, 125:200] = 1
    img[160:228, 196:200] = 1
    img[190:194, 125:170] = 1
    if defect:
        img[36:40, 70:78] = 0  # a broken line
        img[52:60, 100:104] = 1  # a bridge between two lines
    return img


def scene_rule_breaking(rng, n=240):
    img = scene_silicon(rng, n)
    img[135:225, 20:60] = np.where(img[135:225, 20:60] > 0, 1, 0.5)  # third material
    for k in range(70):  # a diagonal line
        img[140 + k: 144 + k, 128 + k: 132 + k] = 1
    img[78:82, 10:150] = 0
    img[75:79, 10:150] = 1  # a line off the grid
    yy, xx = np.indices((n, n))
    img[(np.hypot(xx - 200, yy - 60) < 14) & (np.hypot(xx - 200, yy - 60) > 10)] = 1
    return img


def scene_texture(rng, n=240):
    f = np.fft.fftfreq(n)
    r = np.hypot(f[:, None], f[None, :])
    spec = np.fft.fft2(rng.standard_normal((n, n))) / (r + 0.02) ** 1.2
    img = np.fft.ifft2(spec).real
    return (img - img.min()) / (img.max() - img.min())


def fig_scenes():
    rng = np.random.default_rng(11)
    scenes = [
        ("B1 Bar groups", scene_bars()),
        ("B2 Star", scene_star()),
        ("B3 Edge, line, point pairs", scene_isolated()),
        ("B4 Single grating", scene_grating()),
        ("B5 Height steps", scene_steps()),
        ("B6 Patterned silicon\nwith two defects", scene_silicon(rng)),
        ("B7 Layout clip from a\npublic chip (stand-in)", scene_silicon(rng, defect=False).T),
        ("B8 Rule-breaking scene", scene_rule_breaking(rng)),
        ("B9 Empty: bare silicon", np.zeros((240, 240)) + 0.02 * rng.standard_normal((240, 240))),
        ("B10 Random texture", scene_texture(rng)),
    ]
    fig, axes = plt.subplots(2, 5, figsize=(12.5, 5.6))
    for ax, (title, img) in zip(axes.ravel(), scenes):
        ax.imshow(img, cmap="gray", vmin=-0.1, vmax=1.1, interpolation="nearest")
        ax.set_title(title, fontsize=9.5)
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ax.spines.values():
            s.set_color(INK2)
    save(fig, "scenes")


# --------------------------------------------------------------------------
# 12. The measures: bar contrast, edge response, ring correlation
# --------------------------------------------------------------------------
def fig_measures():
    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(12.5, 4.0),
                                   gridspec_kw={"width_ratios": [1.5, 1]})
    # bar contrast
    x = np.arange(900)
    truth = np.zeros(900)
    pos, groups = 30, []
    for period in (48, 32, 24, 16, 12):
        for k in range(4):
            truth[pos + k * period: pos + k * period + period // 2] = 1
        groups.append((pos, pos + 4 * period - period // 2, period))
        pos += 4 * period + 40
    f = np.fft.fftfreq(900)
    blurred = np.fft.ifft(np.fft.fft(truth) * np.exp(-0.5 * (f / 0.035) ** 2)).real
    ax0.plot(x, truth, color=GRID, lw=1.2, label="Truth")
    ax0.plot(x, blurred, color=BLUE, lw=1.6, label="Reconstruction")
    for a, b, period in groups:
        seg = blurred[a + period // 4: b - period // 4]
        c = (seg.max() - seg.min()) / (seg.max() + seg.min())
        ax0.text((a + b) / 2, 1.06 + 0.2 * (groups.index((a, b, period)) % 2),
                 f"period {period} cells\ncontrast {c:.2f}", ha="center", fontsize=8)
    ax0.set_ylim(-0.32, 1.5)
    ax0.set_xlabel("Position (grid cells)")
    ax0.set_ylabel("Brightness")
    ax0.set_title("Bar contrast: (max − min) / (max + min) in each group", fontsize=10)
    ax0.legend(frameon=False, fontsize=8.5, loc="lower left", ncol=2)
    tidy(ax0)
    # edge response
    xe = np.arange(-40, 41)
    step = (xe >= 0) * 1.0
    fe = np.fft.fftfreq(len(xe))
    honest = np.fft.ifft(np.fft.fft(np.roll(step, 0)) * np.exp(-0.5 * (fe / 0.05) ** 2)).real
    xe2 = np.linspace(-40, 40, 801)
    from scipy.special import erf, sici
    honest = 0.5 * (1 + erf(xe2 / (np.sqrt(2) * 3.2)))
    sharp = 0.5 + sici(2 * np.pi * 0.09 * xe2)[0] / np.pi  # hard cut-off: rings
    ax1.plot(xe2, (xe2 >= 0) * 1.0, color=GRID, lw=1.2, label="Truth")
    ax1.plot(xe2, honest, color=BLUE, lw=1.6, label="Smooth roll-off")
    ax1.plot(xe2, sharp, color=ORANGE, lw=1.6, label="Over-sharpened: rings")
    lo, hi = xe2[np.argmax(honest > 0.1)], xe2[np.argmax(honest > 0.9)]
    ax1.annotate("", xy=(hi, 0.5), xytext=(lo, 0.5),
                 arrowprops=dict(arrowstyle="<->", color=INK, lw=0.9))
    ax1.text(hi + 1.5, 0.47, f"10 to 90% width\n{hi - lo:.1f} cells", fontsize=8,
             va="top")
    ax1.text(-38, 1.12, f"overshoot {100 * (sharp.max() - 1):.0f}%", fontsize=8,
             color=ORANGE)
    ax1.set_ylim(-0.15, 1.25)
    ax1.set_xlabel("Position across an edge (grid cells)")
    ax1.set_ylabel("Brightness")
    ax1.set_title("Edge response: width and overshoot", fontsize=10)
    ax1.legend(frameon=False, fontsize=8.5, loc="lower right")
    tidy(ax1)
    save(fig, "measures")


def fig_frc_how():
    rng = np.random.default_rng(2)
    n = 256
    truth = make_layout(rng, n)
    f = np.fft.fftfreq(n)
    fr = np.hypot(f[:, None], f[None, :])
    tf = np.exp(-0.5 * (fr / 0.05) ** 2)
    a = np.fft.ifft2(np.fft.fft2(truth) * tf).real + rng.normal(0, 0.08, (n, n))
    b = np.fft.ifft2(np.fft.fft2(truth) * tf).real + rng.normal(0, 0.08, (n, n))
    freq, c = ring_correlation(a, b, nbins=48)
    fig, axes = plt.subplots(1, 4, figsize=(13.5, 3.6),
                             gridspec_kw={"width_ratios": [1, 1, 1, 1.5],
                                          "wspace": 0.32})
    for ax, img, title in ((axes[0], a, "Picture from half A of the data"),
                           (axes[1], b, "Picture from half B of the data")):
        ax.imshow(img[:128, :128], cmap="gray", interpolation="nearest")
        ax.set_title(title, fontsize=9.5)
        ax.set_xticks([])
        ax.set_yticks([])
    spec = np.log10(np.abs(np.fft.fftshift(np.fft.fft2(a - a.mean()))) + 1)
    ax = axes[2]
    ax.imshow(spec, cmap="gray", extent=(-0.5, 0.5, -0.5, 0.5))
    for radius, col in ((0.05, AQUA), (0.12, YELLOW), (0.25, ORANGE)):
        ax.add_patch(plt.Circle((0, 0), radius, fill=False, color=col, lw=1.6))
    ax.set_title("Each picture split by detail size:\nrings of equal fineness",
                 fontsize=9.5)
    ax.set_xticks([])
    ax.set_yticks([])
    ax = axes[3]
    ax.plot(freq, c, color=BLUE, lw=1.8)
    for radius, col in ((0.05, AQUA), (0.12, YELLOW), (0.25, ORANGE)):
        ax.axvline(radius, color=col, lw=1.4)
    ax.axhline(1 / 7, color=INK2, lw=0.8, ls="--")
    below = np.where(c < 1 / 7)[0][0]
    ax.plot([freq[below]], [c[below]], "o", color=INK, ms=5)
    ax.annotate(f"falls below 1/7 at a period\nof {1 / freq[below]:.0f} cells: the resolution",
                xy=(freq[below], c[below]), xytext=(0.17, 0.55), fontsize=8.5,
                arrowprops=dict(arrowstyle="->", color=INK, lw=0.8))
    ax.set_xlim(0, 0.4)
    ax.set_ylim(-0.1, 1.05)
    ax.set_xlabel("Fineness of detail (cycles per grid cell)")
    ax.set_ylabel("Agreement of A and B in each ring")
    ax.set_title("Ring by ring correlation", fontsize=9.5)
    tidy(ax)
    save(fig, "frc-how")


# --------------------------------------------------------------------------
# 13. Held-out data
# --------------------------------------------------------------------------
def fig_heldout():
    rng = np.random.default_rng(4)
    fig, axes = plt.subplots(1, 4, figsize=(12.5, 3.5))
    titles = ["Random 5% of pixels\nin every frame", "Whole frames",
              "One whole lighting direction", "One whole pass of the scan"]
    cmap = ListedColormap([BLUE, VIOLET, AQUA, ORANGE])
    for k, (ax, title) in enumerate(zip(axes, titles)):
        # 12 frames in a 3 x 4 arrangement, each 10 x 10 pixels, 1-cell gutters
        canvas = np.full((3 * 11 + 1, 4 * 11 + 1), np.nan)
        for fidx in range(12):
            r, c = divmod(fidx, 4)
            block = np.full((10, 10), float(fidx % 3))  # colour = lighting direction
            if k == 0:
                block[rng.random((10, 10)) < 0.08] = 3
            elif k == 1 and fidx in (2, 7, 9):
                block[:] = 3
            elif k == 2 and fidx % 3 == 1:
                block[:] = 3
            elif k == 3 and r == 2:
                block[:] = 3
            canvas[1 + r * 11: 11 + r * 11, 1 + c * 11: 11 + c * 11] = block
        ax.imshow(canvas, cmap=cmap, vmin=0, vmax=3, interpolation="nearest")
        ax.set_title(title, fontsize=9.5)
        ax.axis("off")
    handles = [Rectangle((0, 0), 1, 1, color=c) for c in (BLUE, VIOLET, AQUA, ORANGE)]
    fig.legend(handles, ["Used in the fit: lighting direction 1", "direction 2",
                         "direction 3", "Held out, predicted afterwards"],
               loc="lower center", ncol=4, frameon=False, fontsize=9)
    save(fig, "heldout")


# --------------------------------------------------------------------------
# 14. Identifiability: a toy case
# --------------------------------------------------------------------------
def fig_identifiability():
    rng = np.random.default_rng(9)
    names = ["Light\nlevel", "Surface\nreflectance", "Pixel\nspacing", "Scan\nspeed",
             "Pattern\nsize", "Start\nposition"]
    coef = rng.standard_normal(12)

    def pattern(u):
        k = np.arange(1, 13)
        return 1 + 0.3 * np.sum(coef[:, None] * np.sin(2 * np.pi * np.outer(k, u) / 7
                                                         + k[:, None]), axis=0) / 3

    pix, frames = np.arange(40.0), np.arange(30.0)

    def model(logp):
        light, refl, pitch, speed, size, start = np.exp(logp[:5]).tolist() + [logp[5]]
        u = (pitch * pix[:, None] + speed * frames[None, :] + start) / size
        return (light * refl * pattern(u.ravel())).ravel()

    p0 = np.zeros(6)
    p0[3] = np.log(0.37)
    jac = np.empty((len(pix) * len(frames), 6))
    for k in range(6):
        d = np.zeros(6)
        d[k] = 1e-5
        jac[:, k] = (model(p0 + d) - model(p0 - d)) / 2e-5
    fisher = jac.T @ jac
    w, v = np.linalg.eigh(fisher)
    fisher_anchored = fisher[np.ix_([0, 3, 4, 5], [0, 3, 4, 5])]  # reflectance, pitch known
    w2 = np.linalg.eigvalsh(fisher_anchored)
    print("Identifiability toy: eigenvalues free", np.array2string(w, precision=3),
          "anchored", np.array2string(w2, precision=3))

    fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.9),
                             gridspec_kw={"width_ratios": [1, 1.25, 1.25]})
    ax = axes[0]
    ax.bar(np.arange(6) - 0.2, np.maximum(w[::-1], 1e-12), 0.4, color=ORANGE,
           label="No anchors")
    ax.bar(np.arange(4) + 0.2, w2[::-1], 0.4, color=AQUA,
           label="Reflectance and\npixel spacing known")
    ax.set_yscale("log")
    ax.set_ylim(1e-10, 1e7)
    ax.set_xticks(range(6))
    ax.set_xticklabels([str(k + 1) for k in range(6)])
    ax.set_xlabel("Combination of unknowns, best determined first")
    ax.set_ylabel("Information in the data")
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("Two combinations carry\nno information", fontsize=10)
    tidy(ax)
    for ax, vec, title in ((axes[1], v[:, 0], "Unseen combination 1"),
                           (axes[2], v[:, 1], "Unseen combination 2")):
        vec = vec / np.abs(vec).max()
        ax.bar(range(6), vec, color=[BLUE if x > 0 else ORANGE for x in vec])
        ax.axhline(0, color=INK2, lw=0.8)
        ax.set_xticks(range(6))
        ax.set_xticklabels(names, fontsize=7.5)
        ax.set_ylim(-1.2, 1.2)
        ax.set_ylabel("Relative change")
        ax.set_title(title, fontsize=10)
        tidy(ax)
    save(fig, "identifiability")
    for k in (0, 1):
        print("  null vector", k, np.array2string(v[:, k] / np.abs(v[:, k]).max(),
                                                 precision=2))




if __name__ == "__main__":
    fig_map()
    fig_fringe()
    fig_tolerances()
    fig_targets()
    fig_frc()
    fig_photon_transfer()
    fig_anchors()
    fig_beat()
    fig_coherence()
    fig_timing()
    fig_scenes()
    fig_measures()
    fig_frc_how()
    fig_heldout()
    fig_identifiability()
