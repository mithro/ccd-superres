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
    fig.savefig(OUT / f"recon-{name}.svg", bbox_inches="tight")
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


if __name__ == "__main__":
    analogy()
    fourier_coverage()
    passband_demo()
    sparsity_conditioning()
    ladder()
    evanescent_table()
    ladder_table()
    numbers()
