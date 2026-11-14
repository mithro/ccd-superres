"""Generate the diagrams for docs/reconstruction-methods.md.

Run from the repository root:

    python docs/diagrams/make_reconstruction_diagrams.py

Writes SVG (used by the document) and PNG copies next to this file, all with
the prefix ``recon-``, and prints the numbers quoted in the document.

Everything here is a formula or a small one-dimensional calculation, not a
result from the simulator. Each function says what it leaves out.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle

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
MASK = "#3b3a37"
SAMPLE = "#e9e4d4"
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
        "svg.hashsalt": "recon",
    }
)


def save(fig, name):
    fig.savefig(OUT / f"recon-{name}.svg", bbox_inches="tight",
                metadata={"Date": None})
    fig.savefig(OUT / f"recon-{name}.png", bbox_inches="tight", dpi=160)
    plt.close(fig)


def arrow(ax, p0, p1, color=INK, lw=1.4, style="-|>", scale=12, **kw):
    ax.add_patch(
        FancyArrowPatch(
            p0, p1, arrowstyle=style, mutation_scale=scale, color=color, lw=lw,
            shrinkA=0, shrinkB=0, **kw
        )
    )


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


# --------------------------------------------------------------------------
# 1. Radar and the scanning sensor side by side
# --------------------------------------------------------------------------
def analogy():
    fig, (a, b) = plt.subplots(1, 2, figsize=(11.5, 4.6))

    # --- synthetic aperture radar ---
    blank(a, (0, 10), (0, 7))
    a.set_title("Synthetic aperture radar", loc="left", fontsize=11, color=INK)
    a.add_patch(Rectangle((0.3, 0.5), 9.4, 0.35, color=SAMPLE, ec=INK2, lw=0.8))
    a.text(9.7, 0.15, "ground", ha="right", fontsize=9, color=INK2)
    target = (5.0, 0.85)
    a.plot(*target, "o", color=ORANGE, ms=7, zorder=5)
    a.text(5.0, 0.15, "one ground point", ha="center", fontsize=9, color=ORANGE)
    ys = 5.6
    xs = np.linspace(1.6, 8.4, 9)
    for x in xs:
        a.plot([x, target[0]], [ys, target[1]], color=BLUE, lw=0.7, alpha=0.55)
        a.add_patch(Rectangle((x - 0.22, ys - 0.07), 0.44, 0.14, color=MASK))
    a.add_patch(Rectangle((xs[4] - 0.3, ys - 0.1), 0.6, 0.2, color=BLUE))
    arrow(a, (1.2, 6.25), (8.8, 6.25), color=INK2)
    a.text(5.0, 6.45, "flight path: one small antenna, one pulse per position",
           ha="center", fontsize=9, color=INK2)
    a.annotate("", (8.4, 5.2), (1.6, 5.2),
               arrowprops=dict(arrowstyle="<->", color=AQUA, lw=1.2))
    a.text(5.0, 4.85, "synthetic aperture", ha="center", fontsize=9, color=AQUA)
    a.text(7.9, 3.0, "each pulse records\namplitude and phase\nof the echo",
           fontsize=9, color=BLUE, ha="left")
    a.text(0.4, 2.6, "range R", fontsize=9, color=INK2)
    a.annotate("", (0.95, 0.9), (0.95, 5.5),
               arrowprops=dict(arrowstyle="<->", color=INK2, lw=1.0))

    # --- scanning lensless sensor ---
    blank(b, (0, 10), (0, 7))
    b.set_title("Scanning lensless sensor, coherent light", loc="left",
                fontsize=11, color=INK)
    b.add_patch(Rectangle((0.3, 0.5), 9.4, 0.35, color=SAMPLE, ec=INK2, lw=0.8))
    b.text(9.7, 0.15, "chip surface", ha="right", fontsize=9, color=INK2)
    target = (5.0, 0.85)
    b.plot(*target, "o", color=ORANGE, ms=7, zorder=5)
    b.text(5.0, 0.15, "one surface point", ha="center", fontsize=9, color=ORANGE)
    ys = 3.4
    b.add_patch(Rectangle((1.6, ys), 6.8, 0.3, color=SILICON, ec=INK2, lw=0.8))
    for x in np.linspace(1.75, 8.25, 27):
        b.add_patch(Rectangle((x - 0.09, ys), 0.18, 0.1, color=MASK))
    for x in np.linspace(1.9, 8.1, 9):
        b.plot([x, target[0]], [ys, target[1]], color=BLUE, lw=0.7, alpha=0.55)
    b.text(5.0, 3.95, "sensor: thousands of pixels at once", ha="center",
           fontsize=9, color=INK2)
    b.annotate("", (8.4, 4.45), (1.6, 4.45),
               arrowprops=dict(arrowstyle="<->", color=AQUA, lw=1.2))
    b.text(5.0, 4.6, "real aperture, already as wide as the sensor",
           ha="center", fontsize=9, color=AQUA)
    arrow(b, (3.4, 5.45), (6.6, 5.45), color=INK2)
    b.text(5.0, 5.65, "scan: moves the pixel grid by fractions of a pixel",
           ha="center", fontsize=9, color=INK2)
    # illumination entering from the side
    for dy in (0.0, 0.35, 0.7):
        arrow(b, (0.2, 2.9 - dy), (2.3 + 2.2 * dy, 0.9), color=YELLOW, lw=1.2)
    b.text(0.25, 3.05, "light", fontsize=9, color=YELLOW)
    b.text(8.6, 2.3, "each pixel records\nbrightness only", fontsize=9,
           color=BLUE, ha="left")
    b.text(0.55, 1.35, "gap", fontsize=9, color=INK2, rotation=90)
    b.annotate("", (1.25, 0.9), (1.25, 3.38),
               arrowprops=dict(arrowstyle="<->", color=INK2, lw=1.0))
    save(fig, "analogy")


# --------------------------------------------------------------------------
# 2. Which feature sizes each kind of measurement can carry
# --------------------------------------------------------------------------
def fourier_coverage(wavelength_um=0.405, tilt_deg=70.0):
    """Regions of surface detail (spatial frequency) that reach the sensor.

    Scalar, far-field picture: a detail of period P sends light sideways at
    sin(angle) = wavelength / P. Assumes the sensor accepts every angle, which
    a real pixel does not. Evanescent detail is treated as lost.
    """
    k = 1.0 / wavelength_um  # cycles per micrometre carried by a wave at 90 deg
    s = np.sin(np.radians(tilt_deg))
    fig, ax = plt.subplots(figsize=(7.4, 7.0))
    lim = 6.2
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect("equal")
    tidy(ax)

    # tilted-light passbands
    for phi in np.arange(0, 360, 45):
        c = (s * k * np.cos(np.radians(phi)), s * k * np.sin(np.radians(phi)))
        ax.add_patch(Circle(c, k, fc=AQUA, ec=AQUA, alpha=0.10, lw=0.8))
    ax.add_patch(Circle((0, 0), (1 + s) * k, fc="none", ec=AQUA, lw=1.6))
    # straight-down light
    ax.add_patch(Circle((0, 0), k, fc=BLUE, ec=BLUE, alpha=0.30, lw=1.2))
    # diffuse light across a 30 um gap
    diffuse = 1.0 / (0.75 * 30.0)
    ax.add_patch(Circle((0, 0), max(diffuse, 0.06), fc=ORANGE, ec=ORANGE))

    # targets
    for period, label, col in (
        (0.200, "100 nm lines and spaces\n(period 200 nm)", INK),
        (0.340, "170 nm lines and spaces\n(period 340 nm)", INK2),
    ):
        r = 1.0 / period
        ax.add_patch(Circle((0, 0), r, fc="none", ec=col, lw=1.3, ls=(0, (5, 3))))
        ang = np.radians(125 if period < 0.3 else 147)
        ax.text(r * np.cos(ang), r * np.sin(ang) + 0.15, label, fontsize=8.5,
                color=col, ha="center", va="bottom",
                bbox=dict(fc=SURFACE, ec="none", pad=1.5))

    ax.annotate("diffuse light, 30 µm gap\n(period 23 µm and larger)", (0, 0),
                (2.6, -5.4), fontsize=8.5, color=ORANGE, ha="center",
                arrowprops=dict(arrowstyle="-", color=ORANGE, lw=0.9))
    ax.text(0, -1.25, "coherent light\nstraight down", fontsize=8.5, color=BLUE,
            ha="center", va="center")
    ax.text(0, 3.45, "coherent light from 8 directions\nat %d° (synthetic aperture)"
            % tilt_deg, fontsize=8.5, color=AQUA, ha="center", va="center")
    ax.set_xlabel("detail across the scan, cycles per µm")
    ax.set_ylabel("detail along the scan, cycles per µm")
    ax.set_title("Surface detail that can reach the sensor, %d nm light"
                 % round(wavelength_um * 1000), loc="left", fontsize=11)
    save(fig, "fourier-coverage")

    print("Fourier coverage at %.0f nm:" % (wavelength_um * 1000))
    print("  straight-down cut-off period   %.0f nm" % (1000 / k))
    print("  synthetic cut-off period (%d deg) %.0f nm" %
          (tilt_deg, 1000 / ((1 + s) * k)))
    print("  absolute limit, period         %.0f nm" % (1000 / (2 * k)))


# --------------------------------------------------------------------------
# 3. One-dimensional demonstration of the cut-offs
# --------------------------------------------------------------------------
def passband_demo():
    """Bar groups seen through ideal cut-offs.

    The bars are low-pass filtered at each cut-off, which is what a perfect
    reconstruction with known phase and no noise would return. It shows the
    ceiling of each method, not what a real reconstruction achieves.
    """
    dx = 0.005  # micrometres
    x = np.arange(0, 16.0, dx)
    truth = np.zeros_like(x)
    groups = [(1.0, 0.400), (5.6, 0.250), (9.0, 0.150), (12.0, 0.100)]
    for x0, hp in groups:
        for i in range(5):
            a = x0 + 2 * i * hp
            truth[(x >= a) & (x < a + hp)] = 1.0
    f = np.fft.fftfreq(x.size, dx)
    spec = np.fft.fft(truth)

    def lowpass(cut):
        return np.real(np.fft.ifft(spec * (np.abs(f) <= cut)))

    rows = [
        ("The surface: groups of five bars", truth, INK),
        ("405 nm light straight down: periods above 405 nm",
         lowpass(1 / 0.405), BLUE),
        ("405 nm, synthetic aperture: periods above 203 nm",
         lowpass(2 / 0.405), AQUA),
        ("266 nm, synthetic aperture: periods above 133 nm",
         lowpass(2 / 0.266), VIOLET),
    ]
    fig, axes = plt.subplots(len(rows), 1, figsize=(10.5, 6.6), sharex=True)
    for ax, (title, y, col) in zip(axes, rows):
        ax.plot(x, y, color=col, lw=1.1)
        ax.set_ylim(-0.25, 1.3)
        ax.set_yticks([0, 1])
        ax.set_title(title, loc="left", fontsize=9.5, color=col, pad=3)
        tidy(ax)
    for x0, hp in groups:
        axes[0].text(x0 + 4.5 * hp, 1.12, "%d nm bars" % round(hp * 1000),
                     ha="center", fontsize=8.5, color=INK2)
    axes[-1].set_xlabel("position on the surface, µm")
    fig.tight_layout()
    save(fig, "passband-demo")

    print("Passband demo, contrast of each bar group (max-min in the middle):")
    for title, y, _ in rows[1:]:
        out = []
        for x0, hp in groups:
            m = (x > x0 + 2 * hp) & (x < x0 + 7 * hp)
            out.append("%d nm: %.2f" % (round(hp * 1000), y[m].max() - y[m].min()))
        print("  " + title[:28].ljust(28), ", ".join(out))


# --------------------------------------------------------------------------
# 4. What prior knowledge buys
# --------------------------------------------------------------------------
def sparsity_conditioning():
    """Noise amplification when k adjacent point features are closer than the
    cut-off allows.

    Best case: the positions are known exactly and only the k brightnesses
    are solved for, from all frequencies up to the cut-off. A real
    reconstruction must also find the positions, which is harder.
    """
    fc = 1.0
    freqs = np.linspace(-fc, fc, 801)
    factors = np.linspace(1.0, 6.0, 51)
    fig, ax = plt.subplots(figsize=(7.6, 4.8))
    table = {}
    for k, col in ((2, BLUE), (3, AQUA), (4, YELLOW), (6, ORANGE)):
        amp = []
        for srf in factors:
            spacing = 1.0 / (2 * fc * srf)
            pos = (np.arange(k) - (k - 1) / 2) * spacing
            A = np.exp(-2j * np.pi * np.outer(freqs, pos)) / np.sqrt(freqs.size)
            amp.append(1.0 / np.linalg.svd(A, compute_uv=False)[-1])
        amp = np.array(amp)
        ax.semilogy(factors, amp, color=col, lw=1.8)
        ax.text(6.08, amp[-1], "%d features" % k, color=col, fontsize=9,
                va="center")
        table[k] = {s: amp[np.argmin(np.abs(factors - s))] for s in (2, 3, 4)}
    ax.set_xlim(1, 7.2)
    ax.set_ylim(0.8, 1e5)
    ax.set_xlabel("how many times finer than the cut-off the features are packed")
    ax.set_ylabel("noise amplification")
    ax.set_title("Cost of resolving a tight cluster of point features beyond "
                 "the cut-off", loc="left", fontsize=11)
    tidy(ax)
    save(fig, "sparsity-conditioning")

    print("Noise amplification (known positions), factor 2 / 3 / 4:")
    for k, row in table.items():
        print("  %d features: %.1f / %.1f / %.1f   extra samples: %.0e / %.0e / %.0e"
              % (k, row[2], row[3], row[4], row[2] ** 2, row[3] ** 2, row[4] ** 2))


# --------------------------------------------------------------------------
# 5. The ladder of limits
# --------------------------------------------------------------------------
def ladder():
    """Smallest line width (half period) per approach. Formula rows use the
    scalar limits quoted in the document; "reported" rows are published
    figures as their authors state them."""
    rows = [
        ("Diffuse light, open pixels, 30 µm gap", 0.75 * 30000 / 2, ORANGE, "formula"),
        ("Diffuse light, open pixels, 3 µm gap", 0.75 * 3000 / 2, ORANGE, "formula"),
        ("Tube per pixel group, 30 µm gap", 2700 / 2, YELLOW, "estimate"),
        ("Coherent, straight down, 405 nm", 405 / 2, BLUE, "formula"),
        ("Lensless hologram, 1.12 µm pixels", 225, BLUE, "reported"),
        ("Coherent, synthetic aperture, 405 nm", 405 / 4, AQUA, "formula"),
        ("Lensless synthetic aperture, 700 nm", 250, AQUA, "reported"),
        ("Coherent, synthetic aperture, 266 nm", 266 / 4, AQUA, "formula"),
        ("Sparse features, 532 nm, with lenses", 100, VIOLET, "reported"),
        ("Extreme ultraviolet ptychography, 13.5 nm", 12.6, INK2, "reported"),
        ("X-ray ptychographic tomography of a chip", 14.6, INK2, "reported"),
    ]
    fig, ax = plt.subplots(figsize=(9.6, 5.2))
    y = np.arange(len(rows))[::-1]
    for yi, (label, nm, col, kind) in zip(y, rows):
        hatch = None if kind != "reported" else "///"
        ax.barh(yi, nm, left=1, color=col if kind != "reported" else SURFACE,
                edgecolor=col, hatch=hatch, height=0.62, lw=1.2)
        txt = ("%.0f nm" % nm) if nm < 1000 else ("%.1f µm" % (nm / 1000))
        ax.text(nm * 1.18, yi, "%s (%s)" % (txt, kind), va="center", fontsize=8.5,
                color=INK2)
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows], fontsize=9)
    ax.set_xscale("log")
    ax.set_xlim(5, 2e5)
    ax.axvline(100, color=INK, lw=1.4, ls=(0, (5, 3)))
    ax.text(112, len(rows) - 0.35, "target: 100 nm", ha="left", fontsize=9,
            color=INK)
    ax.set_ylim(-0.7, len(rows) + 0.1)
    ax.set_xlabel("smallest line width, nm (lines and spaces of equal width)")
    ax.set_title("Where each approach stops", loc="left", fontsize=11)
    tidy(ax)
    ax.grid(False, axis="y")
    save(fig, "ladder")


# --------------------------------------------------------------------------
# 6. Numbers quoted in the text
# --------------------------------------------------------------------------
def evanescent_table(wavelength_nm=405.0):
    """Heights at which a sub-wavelength pattern's light has faded.

    Scalar plane-wave decay exp(-2 pi z sqrt(1/P^2 - 1/wavelength^2)).
    """
    print("Evanescent decay heights (nm) for %.0f nm light:" % wavelength_nm)
    print("  period | 10 %% left | 1 %% left | 0.1 %% left | left at 1 um")
    for period in (150.0, 200.0, 300.0, 400.0):
        kappa = 2 * np.pi * np.sqrt(1 / period**2 - 1 / wavelength_nm**2)
        heights = [np.log(x) / kappa for x in (10, 100, 1000)]
        print("  %6.0f | %9.0f | %8.0f | %10.0f | %.1e"
              % (period, *heights, np.exp(-kappa * 1000)))


def ladder_table():
    """Finest period and line width for each lighting, formula of section 2.1."""
    print("Ladder: wavelength, index, largest light angle -> period, line (nm)")
    for lam, n, deg in ((405, 1.0, 90), (405, 1.0, 70), (375, 1.0, 90),
                        (266, 1.0, 90), (405, 1.5, 90)):
        period = lam / n / (1 + np.sin(np.radians(deg)))
        print("  %d nm, n=%.1f, %d deg: period %.1f, line %.1f"
              % (lam, n, deg, period, period / 2))
    print("Light frequency at 405 nm: %.1e Hz" % (2.998e8 / 405e-9))
    print("Time for light to cross a 0.67 mm gap: %.1f ps" % (0.67e-3 / 2.998e8 * 1e12))
    print("Dither: 10-bit step %.1f e, photon noise at half well %.0f e"
          % (4500 / 1024, np.sqrt(2250)))
    print("Cells of a 50 nm grid per 1.12 um pixel: %.0f" % (1.12**2 / 0.05**2))
    print("Sensor: %.2f mm x %.2f mm" % (3280 * 1.12e-3, 2464 * 1.12e-3))


def numbers():
    print("Evanescent loss of a 200 nm period, 405 nm light:")
    f, k = 1 / 0.200, 1 / 0.405
    kappa = 2 * np.pi * np.sqrt(f * f - k * k)
    for z in (0.05, 0.1, 0.3, 1.0):
        print("  gap %.2f um: field x %.1e" % (z, np.exp(-kappa * z)))
    print("Pixel response to a 200 nm period fringe, 1.12 um pixel:")
    a = 1.12
    print("  sharp-edged pixel: %.3f" % abs(np.sinc(a * f)))
    for sig in (0.05, 0.1, 0.3):
        print("  edge softness %.2f um: x %.1e, passes %.1e %%"
              % (sig, np.exp(-2 * np.pi**2 * sig**2 * f**2),
                 100 * abs(np.sinc(a * f)) * np.exp(-2 * np.pi**2 * sig**2 * f**2)))
    print("Two-beam fringe period, 405 nm at 70 deg: %.0f nm"
          % (405 / (2 * np.sin(np.radians(70)))))
    print("Gap needed to let a 70 deg beam under a 3.68 mm sensor: %.2f mm"
          % (3.68 / (2 * np.tan(np.radians(70)))))


# --------------------------------------------------------------------------
# 7. One-dimensional demonstrations of the ideas in the text
# --------------------------------------------------------------------------
def _lowpass(y, dx, cutoff_period):
    """Ideal low-pass: keep ripples of period longer than cutoff_period."""
    f = np.fft.rfftfreq(y.size, dx)
    return np.fft.irfft(np.fft.rfft(y) * (f <= 1.0 / cutoff_period), y.size)


def limits_curves(wavelength_um=0.405, pixel_um=1.12):
    """Two of the hard limits of section 2.1 as curves.

    Left: scalar plane-wave decay of sub-wavelength detail with height.
    Right: response of a box pixel with Gaussian-softened edges to a fringe.
    """
    fig, (a, b) = plt.subplots(1, 2, figsize=(11.5, 4.4))
    z = np.linspace(0, 1000, 400)
    for period, col in ((150, ORANGE), (200, BLUE), (300, AQUA), (400, VIOLET)):
        kappa = 2 * np.pi * np.sqrt(1 / period**2 - 1 / (1e3 * wavelength_um) ** 2)
        a.semilogy(z, 100 * np.exp(-kappa * z), color=col, lw=2,
                   label="%d nm period (%d nm lines)" % (period, period // 2))
    a.set_ylim(1e-4, 150)
    a.set_xlim(0, 1000)
    a.set_xlabel("height above the surface (nm)")
    a.set_ylabel("share of the wave still present (%)")
    a.set_title("Detail finer than the wavelength fades with height",
                loc="left", fontsize=11, color=INK)
    a.legend(frameon=False, fontsize=9, loc="upper right")
    a.text(990, 0.03, "the design's gap is\n30 000 nm or more,\nfar off the right\nof this plot",
           ha="right", va="bottom", fontsize=9, color=INK2)
    tidy(a)

    p = np.linspace(150, 3000, 600)
    for sig, col in ((0.0, BLUE), (0.05, AQUA), (0.10, YELLOW), (0.30, ORANGE)):
        f = 1e3 / p
        resp = np.abs(np.sinc(pixel_um * f)) * np.exp(-2 * np.pi**2 * sig**2 * f**2)
        # envelope of the sinc so the curve is readable: 1/(pi a f) capped at 1
        env = np.minimum(1.0, 1.0 / (np.pi * pixel_um * f)) * np.exp(
            -2 * np.pi**2 * sig**2 * f**2)
        b.loglog(p, 100 * env, color=col, lw=2,
                 label="edge softness %.2f µm" % sig)
    b.axvline(200, color=INK2, lw=1, ls="--")
    b.text(210, 60, "200 nm period\n(100 nm lines)", fontsize=9, color=INK2, va="top")
    b.axvline(1120, color=INK2, lw=1, ls=":")
    b.text(1160, 0.05, "pixel\nwidth", fontsize=9, color=INK2)
    b.set_ylim(1e-4, 150)
    b.set_xlim(150, 3000)
    b.set_xticks([200, 500, 1000, 2000])
    b.set_xticklabels(["200", "500", "1000", "2000"])
    b.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    b.set_xlabel("period of the fringe on the sensor (nm)")
    b.set_ylabel("share of the fringe the pixel records (%)")
    b.set_title("A 1.12 µm pixel averages fine fringes away",
                loc="left", fontsize=11, color=INK)
    b.legend(frameon=False, fontsize=9, loc="lower right")
    tidy(b)
    save(fig, "limits-curves")


def mixing_demo(detail_nm=230.0, pattern_nm=215.0, pixel_um=1.12):
    """Two-beam mixing as a moire: brightness = light pattern x surface.

    Simplified intensity picture (as in structured illumination), not a wave
    simulation. Shows why a fine ripple becomes a coarse one the pixel sees.
    """
    dx = 0.002
    x = np.arange(0, 14, dx)
    surf = 1 + 0.5 * np.cos(2 * np.pi * x / (detail_nm / 1e3))
    light = 1 + np.cos(2 * np.pi * x / (pattern_nm / 1e3))
    box = np.ones(int(round(pixel_um / dx)))
    box /= box.size
    seen_plain = np.convolve(surf, box, mode="same")
    seen_mixed = np.convolve(surf * light, box, mode="same")
    beat = 1 / (1e3 / pattern_nm - 1e3 / detail_nm)
    fig, axes = plt.subplots(4, 1, figsize=(11.5, 7.2), sharex=True)
    rows = (
        ("Surface detail: ripple with a %d nm period" % detail_nm, surf, INK2),
        ("Light pattern from a beam pair: fringes with a %d nm period" % pattern_nm,
         light, YELLOW),
        ("What one pixel records under plain light: the ripple averages to nothing",
         seen_plain, ORANGE),
        ("What one pixel records under the beam pair: a coarse ripple, period %.1f µm"
         % beat, seen_mixed, BLUE),
    )
    for ax, (title, y, col) in zip(axes, rows):
        ax.plot(x, y, color=col, lw=0.8 if y is surf or y is light else 2)
        ax.set_title(title, loc="left", fontsize=10, color=INK)
        ax.set_ylim(-0.1, 3.1 if y is not light and y is not surf else 2.2)
        ax.set_ylabel("brightness")
        tidy(ax)
    for ax in axes[2:]:
        ax.set_ylim(0.4, 1.6)
        ax.add_patch(Rectangle((1.0, 0.47), pixel_um, 0.12, color=MASK))
        ax.text(1.0 + pixel_um + 0.1, 0.53, "width of one pixel", fontsize=9,
                color=INK2, va="center")
    axes[-1].set_xlim(1, 13)
    axes[-1].set_xlabel("position along the surface (µm)")
    fig.tight_layout()
    print("Mixing demo: %d nm detail under a %d nm pattern beats at %.2f um"
          % (detail_nm, pattern_nm, beat))
    print("  ripple seen by a pixel, plain light: %.4f; beam pair: %.4f"
          % (np.ptp(seen_plain[1000:-1000]) / 2, np.ptp(seen_mixed[1000:-1000]) / 2))
    save(fig, "mixing-demo")


def _propagate(u, dx, z, wavelength):
    f = np.fft.fftfreq(u.size, dx)
    arg = 1 / wavelength**2 - f**2
    h = np.where(arg > 0, np.exp(2j * np.pi * z * np.sqrt(np.maximum(arg, 0))), 0)
    return np.fft.ifft(np.fft.fft(u) * h)


def twin_image_demo(wavelength=0.405, z1=40.0, z2=55.0, z3=75.0):
    """Hologram refocusing with and without phase recovery, in one dimension.

    Scalar wave propagation. The surface is a row of dark bars. Row 3 refocuses
    one recording directly; row 4 alternates between three recordings at
    different gaps (Gerchberg-Saxton style) before refocusing.
    """
    dx = 0.05
    n = 8192
    x = (np.arange(n) - n / 2) * dx
    obj = np.ones(n)
    for c, w in ((-40, 6.0), (-22, 3.0), (-10, 2.0), (0, 1.0), (8, 1.0),
                 (20, 2.0), (24, 2.0), (40, 4.0)):
        obj[np.abs(x - c) < w / 2] = 0.3
    u0 = obj.astype(complex)
    amps = [np.abs(_propagate(u0, dx, z, wavelength)) for z in (z1, z2, z3)]
    direct = np.abs(_propagate(amps[0].astype(complex), dx, -z1, wavelength))
    zs = (z1, z2, z3)
    u = amps[0].astype(complex)
    for _ in range(300):
        for k in (1, 2, 0):
            prev = zs[(k - 1) % 3]
            u = _propagate(u, dx, zs[k] - prev, wavelength)
            u = amps[k] * np.exp(1j * np.angle(u))
    multi = np.abs(_propagate(u, dx, -z1, wavelength))
    sel = np.abs(x) < 60
    err = lambda y: np.sqrt(np.mean((y[sel] - obj[sel]) ** 2))
    print("Twin-image demo, rms error of refocused picture: direct %.3f, three gaps %.3f"
          % (err(direct), err(multi)))
    fig, axes = plt.subplots(4, 1, figsize=(11.5, 7.6), sharex=True)
    rows = (
        ("Surface: dark bars 1 to 6 µm wide on a bright background", obj, INK2),
        ("What the sensor records %d µm above it (brightness only)" % z1,
         amps[0] ** 2, ORANGE),
        ("Refocused from that one recording: ripples from the ghost image remain",
         direct, YELLOW),
        ("Refocused after recovering the phase from recordings at %d, %d and %d µm"
         % zs, multi, BLUE),
    )
    for ax, (title, y, col) in zip(axes, rows):
        ax.plot(x, y, color=col, lw=1.2)
        ax.set_title(title, loc="left", fontsize=10, color=INK)
        ax.set_ylim(0, 1.9 if y is amps[0] ** 2 else 1.5)
        ax.set_ylabel("brightness" if col == ORANGE else "reflection")
        tidy(ax)
    axes[-1].set_xlim(-55, 55)
    axes[-1].set_xlabel("position along the surface (µm)")
    fig.tight_layout()
    save(fig, "twin-image-demo")


def multiscale_demo():
    """Why fitting starts coarse: mismatch against position error.

    Mismatch between a striped pattern and a shifted copy of itself, for
    fine and coarse stripes. Fine stripes give many false minima.
    """
    x = np.linspace(0, 40, 8000)
    shifts = np.linspace(-3, 3, 601)
    fig, ax = plt.subplots(figsize=(9.5, 4.2))
    for period, col, lab in ((0.4, ORANGE, "fine detail only (0.4 µm period)"),
                             (5.0, BLUE, "coarse detail only (5 µm period)")):
        ref = np.cos(2 * np.pi * x / period)
        mis = [np.mean((ref - np.cos(2 * np.pi * (x - s) / period)) ** 2) for s in shifts]
        ax.plot(shifts, mis, color=col, lw=1.6, label=lab)
    ax.axvline(0, color=INK2, lw=1, ls="--")
    ax.text(0.05, 2.3, "true position", fontsize=9, color=INK2)
    ax.annotate("false matches:\noff by whole stripes", (0.8, 0.02), (1.25, 2.35),
                fontsize=9, color=ORANGE, va="bottom",
                arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=1))
    ax.set_xlabel("error in the starting guess of position (µm)")
    ax.set_ylabel("mismatch with the data (arbitrary units)")
    ax.set_ylim(0, 3.3)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    tidy(ax)
    save(fig, "multiscale-demo")


def detect_resolve_demo():
    """One line, two close lines and two separated lines through ideal cut-offs.

    Best case: known phase, no noise. Cut-offs are the finest periods of
    section 2.1 for 405 nm light, straight down and from all directions.
    """
    dx = 1.0
    x = np.arange(-2048, 2048) * dx
    cases = (
        ("One line, 100 nm wide", [(-50, 50)]),
        ("Two 100 nm lines, 100 nm apart", [(-150, -50), (50, 150)]),
        ("Two 100 nm lines, 250 nm apart", [(-225, -125), (125, 225)]),
    )
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.9), sharey=True)
    for ax, (title, spans) in zip(axes, cases):
        obj = np.zeros(x.size)
        for lo, hi in spans:
            obj[(x >= lo) & (x < hi)] = 1
        ax.fill_between(x, 0, obj, color=SILICON, label="true lines")
        ax.plot(x, _lowpass(obj, dx, 405.0), color=ORANGE, lw=2,
                label="laser straight down")
        ax.plot(x, _lowpass(obj, dx, 202.5), color=BLUE, lw=2,
                label="laser from all directions")
        ax.set_title(title, loc="left", fontsize=10, color=INK)
        ax.set_xlim(-600, 600)
        ax.set_xlabel("position (nm)")
        tidy(ax)
    axes[0].set_ylabel("brightness (true line = 1)")
    axes[0].legend(frameon=False, fontsize=9, loc="upper left")
    axes[0].set_ylim(-0.3, 1.9)
    fig.tight_layout()
    save(fig, "detect-resolve-demo")


def dither_demo(samples=2000, seed=1):
    """Averaging quantised readings with and without noise before the digitiser."""
    rng = np.random.default_rng(seed)
    true = np.linspace(0, 3, 121)
    fig, ax = plt.subplots(figsize=(9.5, 4.4))
    ax.plot(true, true, color=INK2, lw=1, ls="--", label="true level")
    for sig, col, lab in ((0.0, ORANGE, "no noise: the average is stuck on the steps"),
                          (0.5, BLUE, "noise of half a step: the average follows the true level")):
        avg = [np.mean(np.round(t + sig * rng.standard_normal(samples))) for t in true]
        ax.plot(true, avg, color=col, lw=2, label=lab)
    ax.set_xlabel("true signal level (digitiser steps)")
    ax.set_ylabel("average of %d readings (digitiser steps)" % samples)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    tidy(ax)
    save(fig, "dither-demo")


def few_materials_demo(cutoff_nm=203.0, seed=3):
    """What a 'two materials only' prior adds to a band-limited picture.

    Alternates between keeping the measured band and pushing every point
    towards the nearer of two values. Best case: no noise, exact cut-off.
    """
    dx = 5.0
    n = 1024
    x = (np.arange(n) - n / 2) * dx
    obj = np.zeros(n)
    for lo, hi in ((-1800, -1500), (-1100, -950), (-650, -500), (-350, -200),
                   (300, 420), (540, 660), (1200, 1900)):
        obj[(x >= lo) & (x < hi)] = 1
    f = np.fft.rfftfreq(n, dx)
    band = f <= 1.0 / cutoff_nm
    data = np.fft.rfft(obj) * band
    plain = np.fft.irfft(data, n)
    est = plain.copy()
    for it in range(400):
        strength = min(1.0, it / 300)
        pushed = est + strength * (np.where(est > 0.5, 1.0, 0.0) - est)
        spec = np.fft.rfft(pushed)
        spec[band] = data[band]
        est = np.fft.irfft(spec, n)
    rms = lambda y: np.sqrt(np.mean((y - obj) ** 2))
    print("Few-materials demo, rms error: band alone %.3f, with two-value prior %.3f"
          % (rms(plain), rms(est)))
    fig, axes = plt.subplots(3, 1, figsize=(11.5, 5.8), sharex=True)
    rows = (("Surface: metal lines 120 to 700 nm wide (two materials)", obj, INK2),
            ("Best picture from the measured band alone (periods above %d nm)" % cutoff_nm,
             plain, ORANGE),
            ("The same data, with the picture required to take two values only",
             est, BLUE))
    for ax, (title, y, col) in zip(axes, rows):
        ax.fill_between(x, 0, obj, color=SILICON, lw=0)
        ax.plot(x, y, color=col, lw=1.6)
        ax.set_title(title, loc="left", fontsize=10, color=INK)
        ax.set_ylim(-0.3, 1.4)
        ax.set_ylabel("reflection")
        tidy(ax)
    axes[-1].set_xlim(-2200, 2200)
    axes[-1].set_xlabel("position (nm)")
    fig.tight_layout()
    save(fig, "few-materials-demo")


# --------------------------------------------------------------------------
# 8. Schematics: how each field's method maps onto the instrument
# --------------------------------------------------------------------------
def _label(ax, x, y, s, color=INK2, **kw):
    kw.setdefault("fontsize", 9)
    kw.setdefault("ha", "center")
    ax.text(x, y, s, color=color, **kw)


def _surface(ax, x0, x1, y, label="chip surface"):
    ax.add_patch(Rectangle((x0, y - 0.3), x1 - x0, 0.3, color=SAMPLE, ec=INK2, lw=0.8))
    _label(ax, x1, y - 0.62, label, ha="right")


def beamforming_map():
    """Delay-and-sum beside shift-and-add. Illustrative, not to scale."""
    fig, (a, b) = plt.subplots(1, 2, figsize=(11.5, 5.0))
    blank(a, (0, 10), (0, 8))
    a.set_title("Beamforming: delay and sum", loc="left", fontsize=11, color=INK)
    xs = np.linspace(1.5, 8.5, 6)
    for k in range(3):  # slanted wave crests arriving from upper left
        off = 0.55 * k
        a.plot([0.6, 9.4], [5.2 + off, 6.4 + off], color=BLUE, lw=1, alpha=0.6)
    arrow(a, (1.6, 7.75), (1.75, 6.65), color=BLUE)
    _label(a, 2.0, 7.65, "wave crests arriving from one direction", color=BLUE, ha="left")
    for i, x in enumerate(xs):
        a.add_patch(Rectangle((x - 0.25, 4.6), 0.5, 0.25, color=MASK))
        d = 0.35 + 0.33 * (len(xs) - 1 - i)
        a.plot([x, x], [4.6, 4.2], color=INK2, lw=1)
        a.add_patch(Rectangle((x - 0.18, 4.2 - d), 0.36, d, color=YELLOW, ec=INK2, lw=0.6))
        a.plot([x, 5.0], [4.2 - d, 1.55], color=INK2, lw=0.8)
    _label(a, 9.95, 5.05, "receivers", ha="right")
    _label(a, 9.95, 2.9, "delays, one\nper receiver", ha="right", color=YELLOW)
    a.add_patch(Circle((5.0, 1.3), 0.32, fc=SURFACE, ec=INK, lw=1.2))
    _label(a, 5.0, 1.19, "+", color=INK, fontsize=14)
    _label(a, 5.0, 0.35, "sum is strong only for the chosen direction")

    blank(b, (0, 10), (0, 8))
    b.set_title("This instrument: shift and add", loc="left", fontsize=11, color=INK)
    _surface(b, 0.5, 9.5, 6.6)
    b.plot(5.0, 6.6, "o", color=ORANGE, ms=7, zorder=5)
    _label(b, 5.0, 6.85, "one surface point", color=ORANGE)
    for k, y in enumerate((5.3, 4.5, 3.7)):
        x0 = 2.0 + 0.28 * k
        for j in range(6):
            col = BLUE if x0 + j <= 5.0 < x0 + j + 0.92 else SILICON
            b.add_patch(Rectangle((x0 + j, y), 0.92, 0.42, color=col, ec=INK2, lw=0.6))
        _label(b, 0.3, y + 0.1, "frame %d" % (k + 1), ha="left")
        b.plot([5.0, 5.0], [y + 0.42, 6.3 if k == 0 else y + 0.8], color=ORANGE, lw=0.8, ls=":")
        if k:
            arrow(b, (x0 + 6.5, y + 0.21), (x0 + 6.5 - 0.28 * k, y + 0.21), color=YELLOW)
    _label(b, 9.9, 2.75, "shift each frame back\nby its known movement", color=YELLOW, ha="right")
    b.plot([5.0, 5.0], [3.7, 2.2], color=INK2, lw=0.8)
    b.add_patch(Circle((5.0, 1.9), 0.32, fc=SURFACE, ec=INK, lw=1.2))
    _label(b, 5.0, 1.79, "+", color=INK, fontsize=14)
    for j in range(24):
        b.add_patch(Rectangle((2.0 + 0.25 * j, 0.75), 0.23, 0.3,
                              color=BLUE if j == 12 else SILICON, ec=INK2, lw=0.4))
    b.plot([5.0, 5.1], [1.58, 1.05], color=INK2, lw=0.8)
    _label(b, 5.0, 0.2, "samples land on a grid finer than the pixels")
    save(fig, "beamforming-map")


def baselines_map():
    """What one antenna pair measures, beside one pair of light directions."""
    fig, (a, b) = plt.subplots(1, 2, figsize=(11.5, 5.0))
    blank(a, (0, 10), (-0.5, 8))
    a.set_title("Radio astronomy: one pair of antennas", loc="left", fontsize=11, color=INK)
    for x in (2.5, 7.5):
        a.add_patch(Polygon([(x - 0.7, 3.2), (x + 0.7, 3.2), (x, 2.5)], color=MASK))
        a.plot([x, x], [2.5, 1.9], color=MASK, lw=2)
        for dx in (-0.35, 0.0, 0.35):
            arrow(a, (x + dx - 0.9, 7.3), (x + dx - 0.1, 3.5), color=BLUE, lw=1)
    _label(a, 5.0, 7.5, "radio waves from the sky", color=BLUE)
    a.annotate("", (7.5, 3.8), (2.5, 3.8), arrowprops=dict(arrowstyle="<->", color=AQUA, lw=1.2))
    _label(a, 5.0, 4.0, "spacing of the pair", color=AQUA)
    a.plot([2.5, 2.5, 4.55], [1.9, 1.5, 1.5], color=INK2, lw=1)
    a.plot([7.5, 7.5, 5.45], [1.9, 1.5, 1.5], color=INK2, lw=1)
    a.add_patch(Circle((5.0, 1.5), 0.45, fc=SURFACE, ec=INK, lw=1.2))
    _label(a, 5.0, 1.39, "×", color=INK, fontsize=14)
    _label(a, 5.0, -0.3, "comparing the two signals measures one ripple of the sky:\n"
           "ripple period = wavelength / spacing")

    blank(b, (0, 10), (-0.5, 8))
    b.set_title("This instrument: one direction in, one direction out", loc="left",
                fontsize=11, color=INK)
    _surface(b, 0.5, 9.5, 1.6, "")
    _label(b, 0.6, 1.8, "chip surface", ha="left")
    b.add_patch(Rectangle((1.5, 6.3), 7.0, 0.35, color=SILICON, ec=INK2, lw=0.8))
    for x in np.linspace(1.65, 8.35, 28):
        b.add_patch(Rectangle((x - 0.09, 6.3), 0.18, 0.1, color=MASK))
    _label(b, 5.0, 6.85, "sensor")
    p = (5.0, 1.6)
    b.plot(*p, "o", color=ORANGE, ms=7, zorder=5)
    arrow(b, (0.4, 3.6), (4.85, 1.7), color=YELLOW, lw=1.6)
    _label(b, 1.2, 3.75, "laser light in,\nslanted", color=YELLOW)
    arrow(b, p, (7.9, 6.25), color=BLUE, lw=1.6)
    _label(b, 8.6, 3.4, "scattered light out,\ntowards one pixel", color=BLUE)
    b.plot([5.0, 5.0], [1.6, 5.6], color=INK2, lw=0.8, ls=":")
    _label(b, 4.4, 2.75, "angle\nin", fontsize=8)
    _label(b, 5.55, 3.4, "angle\nout", fontsize=8)
    _label(b, 5.0, -0.3, "each pair of directions measures one ripple of the surface:\n"
           "ripple period = wavelength / (sin of angle in + sin of angle out)")
    save(fig, "baselines-map")


def overlap_map():
    """Overlap between successive recordings: sonar beside the sensor."""
    fig, (a, b) = plt.subplots(1, 2, figsize=(11.5, 3.6))
    for ax, title, shift, n, unit, note in (
        (a, "Sonar: array positions at two pings", 2.5, 11, "array element",
         "the overlapping elements heard the same echo twice;\n"
         "comparing them gives the movement between pings"),
        (b, "This instrument: sensor positions at two frames", 0.22, 12, "pixel",
         "nearly every pixel overlaps;\ncomparing frames gives the movement to a fraction of a pixel"),
    ):
        blank(ax, (0, 10), (0, 5.2))
        ax.set_title(title, loc="left", fontsize=11, color=INK)
        w = 0.5
        for k, (y, col) in enumerate(((3.4, BLUE), (2.4, ORANGE))):
            x0 = 1.5 + k * shift
            for j in range(n):
                ax.add_patch(Rectangle((x0 + j * w, y), w * 0.92, 0.5, color=col,
                                       alpha=0.85, ec=INK2, lw=0.5))
            _label(ax, 0.1, y + 0.15, ("first", "second")[k], ha="left", color=col)
        lo, hi = 1.5 + shift, 1.5 + n * w
        ax.add_patch(Rectangle((lo, 2.25), hi - lo, 1.8, fill=False, ec=AQUA, lw=1.5, ls="--"))
        _label(ax, (lo + hi) / 2, 4.25, "overlap", color=AQUA)
        arrow(ax, (1.5, 1.75), (1.5 + max(shift, 0.6), 1.75), color=INK2)
        _label(ax, 1.5 + max(shift, 0.6) + 0.15, 1.65,
               "movement between recordings" + ("" if shift > 1 else " (a fraction of a pixel)"),
               ha="left")
        _label(ax, 5.0, 0.3, note)
    save(fig, "overlap-map")


def sampling_map():
    """Where samples fall across the scan for three detector layouts.

    Offsets are computed from the drawn geometry: every row that passes over
    a surface point samples it at that row's sideways offset.
    """
    fig, axes = plt.subplots(2, 3, figsize=(11.5, 5.6),
                             gridspec_kw=dict(height_ratios=[3.2, 0.55]))
    cases = (
        ("One line of pixels", [0.0]),
        ("Two lines offset by half a pixel\n(SPOT 5 satellite)", [0.0, 0.5]),
        ("Two-dimensional array, slightly turned\n(this instrument)",
         [0.125 * r for r in range(8)]),
    )
    for (top, bot), (title, offs) in zip(axes.T, cases):
        blank(top, (-1.2, 7.2), (-0.6, 9.2))
        top.set_title(title, loc="left", fontsize=10, color=INK)
        for r, off in enumerate(offs):
            y = 7.6 - r * (1.0 if len(offs) > 2 else 1.6)
            for c in range(6):
                top.add_patch(Rectangle((c + off, y), 0.94, 0.94, color=SILICON,
                                        ec=INK2, lw=0.6))
            top.plot([2 + off + 0.47], [y + 0.47], "o", color=BLUE, ms=4)
        arrow(top, (-0.8, 8.6), (-0.8, 6.2), color=INK2)
        top.text(-1.05, 7.4, "scan", rotation=90, fontsize=9, color=INK2, va="center")
        bot.set_xlim(-0.05, 1.05)
        bot.set_ylim(0, 1)
        bot.add_patch(Rectangle((0, 0.3), 1, 0.4, color=SILICON, ec=INK2, lw=0.6))
        frac = sorted({round(o % 1.0, 4) for o in offs})
        for f in frac:
            bot.plot([f + 0.0], [0.5], "o", color=BLUE, ms=6, clip_on=False)
        bot.set_yticks([])
        bot.set_xticks([0, 0.5, 1])
        bot.set_xlabel("sample positions across the scan (pixel widths)\n%d per pixel width"
                       % len(frac), fontsize=9)
        for side in ("top", "right", "left"):
            bot.spines[side].set_visible(False)
    fig.tight_layout()
    save(fig, "sampling-map")


def ptychography_map():
    """Ptychography's roles beside the instrument's. Illustrative."""
    fig, (a, b) = plt.subplots(1, 2, figsize=(11.5, 5.0))
    blank(a, (0, 10), (0, 8))
    a.set_title("Ptychography", loc="left", fontsize=11, color=INK)
    a.add_patch(Rectangle((0.2, 3.6), 9.6, 3.6, color=SAMPLE, ec=INK2, lw=0.8))
    _label(a, 9.1, 7.35, "object, seen from above", ha="right")
    for k, x in enumerate(np.linspace(2.4, 7.6, 5)):
        a.add_patch(Circle((x, 5.4), 1.15, fc=LIGHT, ec=YELLOW, lw=1.3, alpha=0.55))
        _label(a, x, 5.3, str(k + 1), color=INK)
    _label(a, 5.0, 6.8, "laser patch (the probe) at five positions; neighbours overlap",
           color=INK2)
    for k, x in enumerate(np.linspace(2.4, 7.6, 5)):
        a.add_patch(Rectangle((x - 0.5, 1.5), 1.0, 1.0, color=SILICON, ec=INK2, lw=0.6))
        for r in (0.15, 0.3, 0.42):
            a.add_patch(Circle((x + 0.05 * (k - 2), 2.0), r, fill=False, ec=BLUE, lw=0.6))
        arrow(a, (x, 3.55), (x, 2.6), color=INK2, lw=0.8)
    _label(a, 5.0, 0.6, "one recorded pattern per position (brightness only);\n"
           "the overlap ties them together so the phase can be solved")

    blank(b, (0, 10), (0, 8))
    b.set_title("This instrument", loc="left", fontsize=11, color=INK)
    b.add_patch(Rectangle((2.0, 6.2), 6.0, 0.4, color=SILICON, ec=INK2, lw=0.8))
    for x in np.linspace(2.15, 7.85, 24):
        b.add_patch(Rectangle((x - 0.09, 6.2), 0.18, 0.1, color=MASK))
    _label(b, 5.0, 6.8, "sensor (records one pattern per frame)")
    for x in np.linspace(2.2, 7.6, 10):  # structured light fixed to the sensor
        b.add_patch(Rectangle((x, 3.0), 0.28, 3.15, color=LIGHT, lw=0))
    _label(b, 8.15, 4.7, "light pattern\nfixed to the\nsensor\n(the probe)", color=YELLOW, ha="left")
    _surface(b, 0.4, 9.6, 3.0, "")
    for x0, w in ((1.2, 0.5), (2.6, 0.25), (3.3, 0.25), (4.6, 0.8), (6.2, 0.3), (7.4, 0.5)):
        b.add_patch(Rectangle((x0, 3.0), w, 0.18, color=ORANGE, lw=0))
    _label(b, 0.45, 2.3, "chip surface (the object)", ha="left")
    arrow(b, (6.0, 2.35), (8.2, 2.35), color=INK2)
    _label(b, 8.3, 2.25, "slides under the sensor", ha="left")
    for k in range(4):
        y = 1.55 - 0.3 * k
        b.plot([2.0 + 0.35 * k, 8.0 + 0.35 * k], [y, y], color=BLUE, lw=2.5, alpha=0.8)
    _label(b, 1.85, 0.95, "area seen in\nframes 1 to 4", ha="right", color=BLUE)
    _label(b, 5.5, 0.05, "successive frames overlap almost completely")
    save(fig, "ptychography-map")


def array2d_map():
    """Three uses of the sensor's second dimension. Illustrative, not to scale."""
    fig, (a, b, c) = plt.subplots(1, 3, figsize=(12.5, 4.6))
    blank(a, (0, 10), (-0.8, 9))
    a.set_title("Tilt: many gaps in one pass\n(side view)", loc="left", fontsize=10, color=INK)
    _surface(a, 0.5, 9.5, 1.6, "")
    _label(a, 0.5, 0.95, "chip surface", ha="left")
    a.add_patch(Polygon([(1.5, 3.4), (8.5, 5.6), (8.5, 6.0), (1.5, 3.8)], color=SILICON, ec=INK2, lw=0.8))
    _label(a, 5.0, 5.75, "sensor, slightly tilted", rotation=14)
    for x, y in ((1.8, 3.45), (8.2, 5.47)):
        a.annotate("", (x, 1.65), (x, y), arrowprops=dict(arrowstyle="<->", color=AQUA, lw=1.2))
    _label(a, 2.75, 2.3, "small gap", color=AQUA)
    _label(a, 7.2, 3.2, "large gap", color=AQUA)
    a.plot(3.0, 1.6, "o", color=ORANGE, ms=7, zorder=5)
    arrow(a, (3.3, 1.2), (7.5, 1.2), color=ORANGE)
    _label(a, 5.5, -0.5, "a surface point passing underneath\nis recorded at every gap in between", color=INK2)

    blank(b, (0, 10), (0, 9))
    b.set_title("Strips: several kinds of measurement\nin one pass (top view)", loc="left",
                fontsize=10, color=INK)
    names = ("bare pixels", "scattering layer", "angle-selecting plate", "colour filter")
    cols = (SILICON, LIGHT, SAMPLE, "#cfe0f7")
    for k, (nm, col) in enumerate(zip(names, cols)):
        b.add_patch(Rectangle((2.0, 6.6 - 1.4 * k), 6.5, 1.4, color=col, ec=INK2, lw=0.8))
        _label(b, 5.25, 7.2 - 1.4 * k, nm, color=INK)
    _label(b, 5.25, 8.25, "sensor, divided into strips")
    arrow(b, (1.2, 8.3), (1.2, 2.2), color=ORANGE)
    b.plot(1.2, 8.3, "o", color=ORANGE, ms=7)
    b.text(0.55, 5.2, "path of one surface point", rotation=90, fontsize=9,
           color=ORANGE, va="center")
    _label(b, 5.0, 0.6, "each point passes under every strip in turn")

    blank(c, (0, 10), (0, 9))
    c.set_title("Halves: depth from two views\n(side view)", loc="left", fontsize=10, color=INK)
    c.add_patch(Rectangle((1.0, 7.0), 3.9, 0.4, color=BLUE, alpha=0.8, ec=INK2, lw=0.8))
    c.add_patch(Rectangle((5.1, 7.0), 3.9, 0.4, color=ORANGE, alpha=0.8, ec=INK2, lw=0.8))
    _label(c, 2.95, 7.6, "left half", color=BLUE)
    _label(c, 7.05, 7.6, "right half", color=ORANGE)
    c.plot([0.5, 9.5], [3.4, 3.4], color=INK2, lw=1, ls="--")
    _label(c, 0.5, 3.55, "assumed surface", ha="left")
    c.plot([0.5, 9.5], [1.8, 1.8], color=INK2, lw=1)
    _label(c, 0.5, 1.3, "true surface", ha="left")
    f = (5.0, 1.8)
    c.plot(*f, "o", color=INK, ms=7, zorder=5)
    for xs, col in ((2.95, BLUE), (7.05, ORANGE)):
        c.plot([f[0], xs], [f[1], 7.0], color=col, lw=1.2)
        xi = f[0] + (xs - f[0]) * (3.4 - 1.8) / (7.0 - 1.8)
        c.plot(xi, 3.4, "o", color=col, ms=6, zorder=5)
    c.annotate("", (5.63, 3.05), (4.37, 3.05), arrowprops=dict(arrowstyle="<->", color=AQUA, lw=1.2))
    _label(c, 8.4, 4.5, "the two halves place\nthe feature differently;\nthe difference gives\nits depth", color=AQUA)
    _label(c, 5.0, 0.3, "pictures from the two halves agree\nonly where the assumed gap is right")
    fig.tight_layout()
    save(fig, "array2d-map")


if __name__ == "__main__":
    analogy()
    fourier_coverage()
    passband_demo()
    sparsity_conditioning()
    ladder()
    limits_curves()
    mixing_demo()
    twin_image_demo()
    multiscale_demo()
    detect_resolve_demo()
    dither_demo()
    few_materials_demo()
    beamforming_map()
    baselines_map()
    overlap_map()
    sampling_map()
    ptychography_map()
    array2d_map()
    evanescent_table()
    ladder_table()
    numbers()
