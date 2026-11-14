"""Generate the diagrams for docs/optical-elements.md.

Run from the repository root:

    python docs/diagrams/make_optics_diagrams.py

Writes SVG (used by the document) and PNG copies next to this file, all with
the prefix ``optics-``, and prints the numbers quoted in the document.

Everything here is an analytic or one-dimensional estimate, not a result from
the simulator. The tube model in particular is a slit (one-dimensional),
paraxial, and treats the walls as perfectly absorbing.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle
from scipy.special import k1

OUT = Path(__file__).resolve().parent

# Same palette as make_diagrams.py so the two sets of figures match.
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
    }
)

WAVELENGTH_UM = 0.5


def save(fig, name):
    fig.savefig(OUT / f"optics-{name}.svg", bbox_inches="tight")
    fig.savefig(OUT / f"optics-{name}.png", bbox_inches="tight", dpi=160)
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


# --------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------
def gap_transfer(period, gap):
    """Diffuse light, open pixel: u K1(u), as in ccdsr.resolution."""
    u = 2 * np.pi * np.asarray(gap, dtype=float) / np.asarray(period, dtype=float)
    return np.where(u < 1e-8, 1.0, u * k1(np.maximum(u, 1e-300)))


def open_kernel_1d(x, gap):
    """Line response of an open pixel to diffuse light (integral of the 2-D spot)."""
    return gap**3 / (x**2 + gap**2) ** 1.5


def tube_footprint(width, depth, gap, xs, wavelength=WAVELENGTH_UM, n_det=160):
    """Footprint of one absorbing tube on the surface, slit model with diffraction.

    A point of the surface at lateral offset ``x`` and height ``gap`` above the
    tube mouth emits a wave. It passes the mouth (a slit of ``width``), travels
    ``depth`` down the tube and is summed over a detector of the same width.
    Light that would hit the walls is simply lost.
    """
    n_xi = int(40 * width**2 / (wavelength * min(gap, depth))
               + 40 * width * np.abs(xs).max() / (wavelength * gap)) + 400
    n_xi = min(n_xi, 6000)
    xi = np.linspace(-width / 2, width / 2, n_xi)
    s = np.linspace(-width / 2, width / 2, n_det)
    down = np.exp(1j * np.pi * (s[:, None] - xi[None, :]) ** 2 / (wavelength * depth))
    out = np.empty(xs.size)
    for i, x in enumerate(xs):
        at_mouth = np.exp(1j * np.pi * (xi - x) ** 2 / (wavelength * gap))
        out[i] = np.mean(np.abs(down @ at_mouth) ** 2)
    return out


def tube_footprint_geometric(width, depth, gap, xs):
    """Ray-optics footprint: a trapezoid, flat over ``width``."""
    top = width / 2
    base = width / 2 + width * gap / depth
    return np.clip((base - np.abs(xs)) / (base - top), 0, 1)


def half_light_width(xs, values):
    """Width of the central region that collects half of the response.

    Steadier than the width at half height when diffraction puts ripples on
    the footprint. For the open pixel it is 1.15 times the gap.
    """
    c = np.cumsum(values)
    c = c / c[-1]
    return np.interp(0.75, c, xs) - np.interp(0.25, c, xs)


def transfer_of(xs, values, periods):
    """Magnitude of the Fourier transform of a footprint at the given periods."""
    v = values / np.trapezoid(values, xs)
    f = 1.0 / np.asarray(periods)
    return np.abs(np.trapezoid(v[None, :] * np.exp(-2j * np.pi * f[:, None] * xs[None, :]),
                               xs, axis=1))


def tube_throughput(aspect):
    """Light reaching a pixel at the bottom of a square tube, relative to an
    open pixel facing the same diffusely glowing surface (view factor between
    two coaxial squares of side w a distance L apart)."""
    x = 1.0 / np.asarray(aspect, dtype=float)  # w / L
    a = np.sqrt(1 + x**2)
    return (2 / (np.pi * x**2)) * (
        np.log(a * a / np.sqrt(1 + 2 * x**2)) + 2 * x * a * np.arctan(x / a)
        - 2 * x * np.arctan(x)
    )


# --------------------------------------------------------------------------
# 1. Where each kind of element sits
# --------------------------------------------------------------------------
def element_positions():
    fig, ax = plt.subplots(figsize=(10.5, 5.6))
    ax.axis("off")

    # Sensor die at the top, facing down, as in the design's cross-section.
    ax.add_patch(Rectangle((1.0, 4.6), 8.0, 0.9, fc=SILICON, ec=INK2, lw=1))
    ax.text(5.0, 5.05, "sensor die (pixels face down)", ha="center", va="center",
            color=INK2)
    for i in range(8):
        ax.add_patch(Rectangle((1.15 + i, 4.62), 0.7, 0.2, fc="#ffffff", ec=INK2, lw=0.7))

    # Zone B: on the sensor face
    ax.add_patch(Rectangle((1.0, 3.9), 8.0, 0.7, fc=BLUE, ec="none", alpha=0.18))
    for i in range(17):
        ax.add_patch(Rectangle((1.0 + i * 0.5 - 0.04, 3.9), 0.08, 0.7, fc=MASK, ec="none"))
    # Zone C: in the gap
    ax.add_patch(Rectangle((1.0, 2.55), 8.0, 0.16, fc=AQUA, ec="none", alpha=0.75))
    # Surface
    xs = np.linspace(0.2, 9.8, 900)
    h = np.zeros_like(xs)
    for x0, w, hh in [(1.8, 0.4, 0.12), (3.1, 0.2, 0.16), (4.7, 0.5, 0.09),
                      (6.6, 0.25, 0.14), (7.1, 0.25, 0.14), (8.3, 0.6, 0.07)]:
        h += hh * ((xs > x0) & (xs < x0 + w))
    ax.fill_between(xs, 0.5, 1.2 + h, color=SAMPLE, lw=0)
    ax.plot(xs, 1.2 + h, color=INK2, lw=1.1)
    ax.text(5.0, 0.82, "surface under test", ha="center", va="center", color=INK2)

    # Zone A: the light
    ax.add_patch(Polygon([[-0.9, 3.25], [-0.9, 2.65], [0.9, 2.0], [0.9, 2.3]],
                         closed=True, fc=YELLOW, ec="none", alpha=0.45))
    arrow(ax, (-0.9, 2.95), (0.85, 2.17), color=YELLOW, lw=2.2, scale=16)
    ax.add_patch(Rectangle((-1.5, 2.6), 0.6, 0.75, fc=LIGHT, ec=INK2, lw=1))
    ax.text(-1.2, 2.98, "light", ha="center", va="center", fontsize=9)
    ax.add_patch(Rectangle((-0.45, 2.38), 0.07, 0.72, fc=ORANGE, ec="none",
                           angle=-21))

    # Gap dimension
    arrow(ax, (9.35, 1.22), (9.35, 3.9), style="<|-|>", lw=1, scale=8)
    ax.text(9.5, 2.55, "gap", va="center")

    # Labels
    def label(x, y, title, body, color):
        ax.text(x, y, title, color=color, fontweight="bold", va="top", fontsize=10.5)
        ax.text(x, y - 0.33, body, color=INK, va="top", fontsize=9.3, linespacing=1.45)

    label(10.6, 5.5, "B  On the sensor face",
          "tubes and collimator arrays\nsub-pixel openings, coded masks\n"
          "colour filter, microlenses\ndiffuser or scattering layer", BLUE)
    label(10.6, 3.45, "C  In the gap",
          "fibre-optic or capillary plate\nmask or grating above the surface\n"
          "reference flat for interference\nindex-matching liquid", AQUA)
    label(10.6, 1.6, "A  In the light",
          "direction and angular spread\ncolour and bandwidth, coherence\n"
          "fringes, speckle, Talbot patterns\npulses and pulse codes, polarisation",
          "#b77b00")
    ax.plot([9.0, 10.5], [4.25, 5.2], color=BLUE, lw=0.8)
    ax.plot([9.0, 10.5], [2.63, 3.15], color=AQUA, lw=0.8)

    ax.set_xlim(-1.7, 14.6)
    ax.set_ylim(0.1, 5.8)
    save(fig, "element-positions")


# --------------------------------------------------------------------------
# 2. One tube around the sensor against one tube per pixel
# --------------------------------------------------------------------------
def tube_geometry():
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.4))

    # ---- Left: one tube around the whole sensor
    ax = axes[0]
    ax.axis("off")
    ax.set_title("One tube around the whole sensor", loc="left", fontsize=11,
                 fontweight="bold")
    W, L, z = 4.0, 5.0, 0.7
    ax.add_patch(Rectangle((-W / 2 - 0.3, 0), 0.3, L, fc=MASK, ec="none"))
    ax.add_patch(Rectangle((W / 2, 0), 0.3, L, fc=MASK, ec="none"))
    ax.add_patch(Rectangle((-W / 2, L), W, 0.45, fc=SILICON, ec=INK2, lw=1))
    ax.text(0, L + 0.22, "sensor", ha="center", va="center", color=INK2)
    ax.add_patch(Rectangle((-3.6, -z - 0.5), 7.2, 0.5, fc=SAMPLE, ec=INK2, lw=1))
    ax.text(0, -z - 0.25, "surface", ha="center", va="center", color=INK2)
    for xp, col in [(-1.5, BLUE), (1.5, ORANGE)]:
        # A pixel at xp sees the surface through the whole mouth.
        left = xp + (-W / 2 - xp) * (L + z) / L
        right = xp + (W / 2 - xp) * (L + z) / L
        ax.add_patch(Polygon([[xp, L], [left, -z], [right, -z]], closed=True,
                             fc=col, ec=col, alpha=0.16, lw=0))
        ax.plot([xp, left], [L, -z], color=col, lw=1)
        ax.plot([xp, right], [L, -z], color=col, lw=1)
        ax.plot([left, right], [-z + 0.04 + (0.07 if col == ORANGE else 0)] * 2,
                color=col, lw=3.2, solid_capstyle="butt")
        ax.plot(xp, L, "o", color=col, ms=6)
    arrow(ax, (-W / 2 - 0.75, 0), (-W / 2 - 0.75, L), style="<|-|>", lw=1, scale=8)
    ax.text(-W / 2 - 0.9, L / 2, "depth L", ha="right", va="center")
    arrow(ax, (-W / 2, L + 0.8), (W / 2, L + 0.8), style="<|-|>", lw=1, scale=8)
    ax.text(0, L + 0.95, "width W", ha="center", va="bottom")
    ax.text(0, -z - 0.75,
            "Two pixels far apart see almost the same patch,\n"
            "about as wide as the tube. Angles are limited,\npositions are not.",
            ha="center", va="top", fontsize=9.5)
    ax.set_xlim(-4.2, 4.2)
    ax.set_ylim(-3.0, 6.6)
    ax.set_aspect("equal")

    # ---- Right: one tube per pixel
    ax = axes[1]
    ax.axis("off")
    ax.set_title("One tube per pixel (collimator array)", loc="left", fontsize=11,
                 fontweight="bold")
    w, L, z, wall = 0.9, 4.0, 1.0, 0.16
    pitch = w + wall
    n = 6
    x0 = -n * pitch / 2
    ax.add_patch(Rectangle((x0 - wall / 2, L), n * pitch + wall, 0.45, fc=SILICON,
                           ec=INK2, lw=1))
    ax.text(0, L + 0.22, "sensor", ha="center", va="center", color=INK2)
    for i in range(n + 1):
        ax.add_patch(Rectangle((x0 + i * pitch - wall / 2, 0), wall, L, fc=MASK,
                               ec="none"))
    ax.add_patch(Rectangle((-3.9, -z - 0.5), 7.8, 0.5, fc=SAMPLE, ec=INK2, lw=1))
    ax.text(0, -z - 0.25, "surface", ha="center", va="center", color=INK2)
    for k, col in [(1, BLUE), (4, ORANGE)]:
        c = x0 + (k + 0.5) * pitch
        half_top, half_base = w / 2, w / 2 + w * z / L
        ax.add_patch(Polygon([[c - w / 2, L], [c + w / 2, L], [c + w / 2, 0],
                              [c + half_base, -z], [c - half_base, -z],
                              [c - w / 2, 0]], closed=True, fc=col, ec="none",
                             alpha=0.2))
        ax.plot([c - w / 2, c + half_base], [L, -z], color=col, lw=0.9)
        ax.plot([c + w / 2, c - half_base], [L, -z], color=col, lw=0.9)
        ax.plot([c - half_base, c + half_base], [-z + 0.05] * 2, color=col, lw=3.2,
                solid_capstyle="butt")
    c = x0 + 4.5 * pitch
    arrow(ax, (c - w / 2, L + 0.8), (c + w / 2, L + 0.8), style="<|-|>", lw=1, scale=7)
    ax.text(c, L + 0.95, "width w", ha="center", va="bottom")
    xr = x0 + n * pitch + 0.55
    arrow(ax, (xr, 0), (xr, L), style="<|-|>", lw=1, scale=8)
    ax.text(xr + 0.15, L / 2, "depth L", va="center")
    arrow(ax, (xr, -z), (xr, 0), style="<|-|>", lw=1, scale=6)
    ax.text(xr + 0.15, -z / 2, "gap z", va="center")
    ax.text(0, -z - 0.75,
            "Each pixel sees its own patch, about w·(1 + z/L) wide.\n"
            "A deep tube makes the patch as small as the tube itself,\n"
            "until diffraction at the mouth takes over.",
            ha="center", va="top", fontsize=9.5)
    ax.set_xlim(-4.6, 4.9)
    ax.set_ylim(-3.3, 6.3)
    ax.set_aspect("equal")
    save(fig, "tube-geometry")


# --------------------------------------------------------------------------
# 3. Tube numbers: footprint, best width, light lost
# --------------------------------------------------------------------------
def tube_numbers():
    fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.5))
    lam = WAVELENGTH_UM

    # (a) Footprint shapes at a 100 um gap
    ax = axes[0]
    gap = 100.0
    xs = np.linspace(-150, 150, 1501)
    ax.plot(xs, open_kernel_1d(xs, gap), color=INK2, lw=1.8, label="open pixel, no tube")
    for width, depth, col in [(10.0, 1000.0, BLUE), (30.0, 1000.0, ORANGE)]:
        fp = tube_footprint(width, depth, gap, xs)
        ax.plot(xs, fp / fp.max(), color=col, lw=1.8,
                label=f"tube {width:.0f} µm wide, {depth / 1000:.0f} mm deep")
    ax.set_xlabel("position on the surface (µm)")
    ax.set_ylabel("relative response")
    ax.set_title("Patch seen by one pixel, gap 100 µm", loc="left", fontsize=10.5)
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    ax.set_ylim(0, 1.32)
    tidy(ax)

    # (b) Width of the patch against tube width
    ax = axes[1]
    widths = np.geomspace(1.0, 60.0, 34)
    best = {}
    for gap, col in [(10.0, AQUA), (30.0, ORANGE), (100.0, BLUE)]:
        out = []
        for w in widths:
            half = 5 * w + 12 * gap * lam / w
            x = np.linspace(-half, half, 1601)
            out.append(half_light_width(x, tube_footprint(w, 10 * gap, gap, x)))
        out = np.array(out)
        i = int(np.argmin(out))
        best[gap] = (widths[i], out[i])
        ax.loglog(widths, out, color=col, lw=1.8, label=f"gap {gap:.0f} µm")
        ax.axhline(2 / np.sqrt(3) * gap, color=col, lw=1, ls=(0, (4, 3)))
        ax.plot(widths[i], out[i], "o", color=col, ms=5)
    ax.plot(widths, widths / 2, color=INK2, lw=0.8, ls=":")
    ax.text(40, 14.5, "half the tube width", rotation=38, color=INK2, fontsize=8, ha="center")
    ax.text(1.05, 150, "dashed: open pixel at the same gap", color=INK2, fontsize=8.5)
    ax.set_xlabel("tube width w (µm)")
    ax.set_ylabel("width of patch giving half the signal (µm)")
    ax.set_title("Best tube width (tube 10 times deeper than the gap)", loc="left",
                 fontsize=10.5)
    ax.legend(frameon=False, fontsize=8.5, loc="lower left")
    ax.set_ylim(1, 300)
    tidy(ax)

    # (c) Light lost
    ax = axes[2]
    aspect = np.geomspace(1, 300, 200)
    ax.loglog(aspect, tube_throughput(aspect), color=BLUE, lw=1.8,
              label="light reaching the pixel")
    ax.loglog(aspect, np.sqrt(tube_throughput(aspect)), color=ORANGE, lw=1.8,
              label="signal-to-noise per sample\n(photon noise limited)")
    for a in (5, 10, 30, 100):
        ax.plot(a, tube_throughput(a), "o", color=BLUE, ms=4)
        ax.annotate(f"{100 * tube_throughput(a):.2g}%", (a, tube_throughput(a)),
                    textcoords="offset points", xytext=(6, 4), fontsize=8.5, color=BLUE)
    ax.set_xlabel("tube depth divided by width, L / w")
    ax.set_ylabel("relative to an open pixel")
    ax.set_title("Light kept by a tube (diffuse surface)", loc="left", fontsize=10.5)
    ax.legend(frameon=False, fontsize=8.5, loc="lower left")
    tidy(ax)

    fig.tight_layout()
    save(fig, "tube-numbers")
    return best


# --------------------------------------------------------------------------
# 4. Transfer functions at one gap
# --------------------------------------------------------------------------
def transfer_functions(gap=30.0):
    lam = WAVELENGTH_UM
    fig, ax = plt.subplots(figsize=(10, 5.2))
    periods = np.geomspace(0.7, 400, 700)

    ax.loglog(periods, gap_transfer(periods, gap), color=INK2, lw=2,
              label="open pixel, diffuse light (design baseline)")

    # Tube of the best width for this gap
    w = 1.45 * np.sqrt(lam * gap)
    half = 60 * w
    xs = np.linspace(-half, half, 6001)
    fp = tube_footprint(w, 10 * gap, gap, xs)
    ax.loglog(periods, transfer_of(xs, fp, periods), color=BLUE, lw=2,
              label=f"tube per pixel group, {w:.1f} µm wide, diffuse light")

    # Collimated coherent light, weak object: phase contrast transfer function
    f = 1 / periods
    bandwidth = 0.02  # um, a plain LED
    envelope = np.exp(-0.5 * (np.pi * gap * bandwidth * f**2) ** 2)
    ctf = np.abs(np.sin(np.pi * lam * gap * f**2)) * envelope
    ax.loglog(periods, np.maximum(ctf, 1e-6), color=AQUA, lw=1.1, alpha=0.9,
              label="collimated single-colour light, height contrast (one gap)")
    ax.loglog(periods, envelope, color=AQUA, lw=2, ls=(0, (5, 2)),
              label="  its envelope, reached by combining gaps or colours")

    # Fringe illumination fixed to the sensor: a window around the fringe period
    fringe = 3.0
    window = 0.5 * gap_transfer(1 / np.maximum(np.abs(f - 1 / fringe), 1e-9), gap)
    ax.loglog(periods, np.maximum(window, 1e-6), color=ORANGE, lw=2,
              label=f"fringe lighting, {fringe:.0f} µm fringes fixed to the sensor")

    ax.axhline(1e-3, color=INK, lw=0.8, ls=":")
    ax.text(410, 1.15e-3, "illustrative noise floor", ha="right", fontsize=8.5)
    ax.axvline(lam, color=INK2, lw=0.8, ls=":")
    ax.text(lam * 1.04, 3e-5, "wavelength", rotation=90, fontsize=8.5, color=INK2,
            va="bottom")
    ax.set_ylim(1e-5, 2)
    ax.set_xlim(0.4, 400)
    ax.set_xlabel("feature period on the surface (µm)")
    ax.set_ylabel("contrast passed to the pixel")
    ax.set_title(f"What crosses a {gap:.0f} µm gap, by method", loc="left", fontsize=11)
    ax.legend(frameon=False, fontsize=8.8, loc="lower right", bbox_to_anchor=(1.0, 0.07))
    tidy(ax)
    save(fig, "transfer-functions")

    # Numbers for the text: period at which each curve meets the floor
    def crossing(values):
        ok = np.where(values >= 1e-3)[0]
        return periods[ok[0]]

    return {
        "open": crossing(gap_transfer(periods, gap)),
        "tube": crossing(transfer_of(xs, fp, periods)),
        "tube_width": w,
        "coherent": crossing(envelope),
    }


# --------------------------------------------------------------------------
# 5. Resolution against gap, by family of method
# --------------------------------------------------------------------------
def resolution_vs_gap():
    lam = WAVELENGTH_UM
    fig, ax = plt.subplots(figsize=(10, 5.6))
    gap = np.geomspace(0.05, 2000, 400)

    ax.loglog(gap, 0.75 * gap, color=INK2, lw=2.2)
    ax.text(11, 40, "open pixel, diffuse light\n0.75 × gap", color=INK2,
            fontsize=9.5, rotation=31, ha="center")

    lo = np.minimum(np.sqrt(lam * gap), 0.75 * gap)
    hi = np.minimum(2 * np.sqrt(lam * gap), 0.75 * gap)
    mask = gap > 2 * lam
    ax.fill_between(gap[mask], lo[mask], hi[mask], color=BLUE, alpha=0.3, lw=0)
    ax.text(1800, 3.4, "angle restriction: tubes, collimators, pinholes,\n"
            "shadow masks. About √(wavelength × gap)", color=BLUE, fontsize=9.5,
            ha="right", va="center")

    ax.fill_between(gap, lam / 2, lam, color=AQUA, alpha=0.3, lw=0)
    ax.text(1800, 0.345, "interference methods: coherent light with phase recovery,\n"
            "fringe or speckle lighting, coded masks. About one wavelength,\n"
            "set by the angles collected, not by the gap",
            color="#0d7a54", fontsize=9.2, va="center", ha="right")

    ax.fill_between(gap[gap < lam / 2], 0.75 * gap[gap < lam / 2], lam / 2,
                    color=ORANGE, alpha=0.18, lw=0)
    ax.text(0.36, 0.085, "near field: finer\ndetail needs a gap far\nbelow a wavelength",
            color=ORANGE, fontsize=9, va="center")

    ax.axhline(1.12, color=INK, lw=0.8, ls=":")
    ax.text(0.055, 1.25, "pixel pitch 1.12 µm", fontsize=8.5)

    for g, name in [(3, "bare die\nheld close"), (500, "cover glass\nleft on")]:
        ax.axvline(g, color=INK2, lw=0.8, ls=(0, (4, 3)))
        ax.text(g * 1.08, 0.034, name, fontsize=8.5, color=INK2, va="bottom")

    ax.set_xlim(0.05, 2000)
    ax.set_ylim(0.03, 1000)
    ax.set_xlabel("gap between sensor and surface (µm)")
    ax.set_ylabel("smallest recoverable feature period (µm)")
    ax.set_title("How each family of method scales with the gap (green light, 0.5 µm)",
                 loc="left", fontsize=11)
    tidy(ax)
    save(fig, "resolution-vs-gap")


# --------------------------------------------------------------------------
# 6. Ways to light an opaque surface under a sensor
# --------------------------------------------------------------------------
def illumination_geometries():
    fig, axes = plt.subplots(1, 4, figsize=(14.5, 4.0))

    def base(ax, title, gap, note):
        ax.axis("off")
        ax.set_title(title, loc="left", fontsize=10.5, fontweight="bold")
        ax.add_patch(Rectangle((-2, gap), 4, 0.5, fc=SILICON, ec=INK2, lw=1))
        ax.text(0, gap + 0.25, "sensor", ha="center", va="center", color=INK2,
                fontsize=9)
        ax.add_patch(Rectangle((-3.4, -0.5), 6.8, 0.5, fc=SAMPLE, ec=INK2, lw=1))
        ax.text(0, -1.0, note, ha="center", va="top", fontsize=8.8, linespacing=1.4)
        ax.set_xlim(-3.6, 3.6)
        ax.set_ylim(-3.2, 5.2)
        ax.set_aspect("equal")

    def ray(ax, pts, col=YELLOW):
        pts = np.asarray(pts, dtype=float)
        ax.plot(pts[:-1, 0], pts[:-1, 1], color=col, lw=2)
        arrow(ax, pts[-2], pts[-1], color=col, lw=2, scale=12)

    ax = axes[0]
    base(ax, "A  From the side, through the gap", 0.6,
         "Works with diffuse light.\nGap must be at least a few\npercent of the sensor width.")
    ray(ax, [(-3.5, 0.75), (-0.6, 0.04), (-0.6, 0.55)])
    ray(ax, [(3.5, 0.75), (0.9, 0.04), (0.9, 0.55)])

    ax = axes[1]
    base(ax, "B  Slanted beam, mirror-like surface", 1.6,
         "Collimated beam enters past the\nsensor edge and reflects up.\nGap about a millimetre.")
    ray(ax, [(-3.5, 2.1), (-0.9, 0.0), (1.0, 1.55)])
    ray(ax, [(-3.5, 1.5), (-1.55, 0.0), (0.4, 1.55)])

    ax = axes[2]
    base(ax, "C  Through a beam splitter", 3.0,
         "Light arrives straight down.\nGap of several millimetres:\ncoherent methods only.")
    ax.add_patch(Rectangle((-1.2, 0.5), 2.4, 2.2, fc="#dfeefc", ec=INK2, lw=0.9))
    ax.plot([-1.2, 1.2], [2.7, 0.5], color=INK2, lw=0.9)
    ray(ax, [(-3.5, 1.6), (0.0, 1.6), (0.0, 0.05)])
    ray(ax, [(0.25, 0.05), (0.25, 2.95)], col=ORANGE)

    ax = axes[3]
    base(ax, "D  Through the sample", 0.6,
         "Only for transparent samples.\nThe arrangement used by nearly\nall published lensless microscopes.")
    for x in (-1.0, 0.0, 1.0):
        ray(ax, [(x, -3.0), (x, 0.55)])
    ax.text(0, -0.25, "sample", ha="center", va="center", color=INK2, fontsize=9)

    for a in axes[:3]:
        a.text(0, -0.25, "opaque surface", ha="center", va="center", color=INK2,
               fontsize=9)
    fig.tight_layout()
    save(fig, "illumination-geometries")


# --------------------------------------------------------------------------
# 7. Fringe lighting: a one-dimensional demonstration
# --------------------------------------------------------------------------
def fringe_demo():
    gap, bar_period, fringe_period = 30.0, 3.0, 3.0
    dx = 0.05
    x = np.arange(-400, 400, dx)
    surface = 0.5 + 0.25 * np.sign(np.sin(2 * np.pi * x / bar_period)) * (np.abs(x) < 60)
    xk = np.arange(-300, 300 + dx, dx)
    blur = open_kernel_1d(xk, gap)
    blur /= blur.sum()

    def scan(light):
        # The pixel and the light pattern stay together; the surface slides under them.
        kernel = blur * light(xk)
        return np.convolve(surface, kernel[::-1], mode="same")

    plain = scan(lambda u: np.ones_like(u))
    fringes = scan(lambda u: 1 + np.cos(2 * np.pi * u / fringe_period))

    fig, axes = plt.subplots(3, 1, figsize=(10, 6.4), sharex=True)
    sel = np.abs(x) < 90
    axes[0].plot(x[sel], surface[sel], color=INK2, lw=0.9)
    axes[0].set_ylabel("reflectance")
    axes[0].set_title(
        f"Surface: bars of {bar_period:.0f} µm period, seen across a {gap:.0f} µm gap",
        loc="left", fontsize=10.5)
    axes[1].plot(x[sel], plain[sel], color=INK2, lw=1.4)
    axes[1].set_ylabel("pixel signal")
    axes[1].set_title("Uniform diffuse light: the bars are gone", loc="left", fontsize=10.5)
    axes[2].plot(x[sel], fringes[sel], color=ORANGE, lw=0.9)
    axes[2].set_ylabel("pixel signal")
    axes[2].set_title(
        f"Light fringes of {fringe_period:.0f} µm period travelling with the sensor: "
        "the bars come through", loc="left", fontsize=10.5)
    axes[2].set_xlabel("scan position (µm)")
    for a in axes:
        tidy(a)
    axes[1].set_ylim(0.3, 0.7)
    axes[2].set_ylim(0.3, 0.7)
    fig.tight_layout()
    save(fig, "fringe-demo")

    centre = np.abs(x) < 20
    return {
        "plain_ripple": float(np.ptp(plain[centre])),
        "fringe_ripple": float(np.ptp(fringes[centre])),
        "bar_swing": 0.5,
    }


# --------------------------------------------------------------------------
# 8. Signal produced by one nanometre of height
# --------------------------------------------------------------------------
def height_signal():
    lam_nm = 500.0
    rows = [
        ("Interference in the gap or against a reference flat\n(fringe visibility 0.5)",
         0.5 * 4 * np.pi / lam_nm, AQUA),
        ("Collimated coherent light, phase contrast\n(best feature size for the gap)",
         2 * 4 * np.pi / lam_nm, AQUA),
        ("Thin transparent film on a mirror-like base\n(about 0.5 % per nm, depends on the film)",
         0.005, AQUA),
        ("Slanted fringes, 1 µm period, 45° slant", 0.5 * 2 * np.pi / 1000.0, ORANGE),
        ("Shading under slanted light, 5 µm wide feature", 2 * np.pi / 5000.0, ORANGE),
        ("Blur width, 3 µm gap", 1 / 3000.0, INK2),
        ("Blur width, 100 µm gap", 1 / 100000.0, INK2),
    ]
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ys = np.arange(len(rows))[::-1]
    for y, (name, value, col) in zip(ys, rows):
        ax.barh(y, value * 100, color=col, height=0.55)
        ax.text(value * 100 * 1.12, y, f"{value * 100:.2g} %", va="center", fontsize=9)
    ax.set_yticks(ys)
    ax.set_yticklabels([r[0] for r in rows], fontsize=9)
    ax.set_xscale("log")
    ax.set_xlim(5e-4, 30)
    ax.axvline(2.0, color=INK, lw=0.9, ls=":")
    ax.text(2.1, len(rows) + 0.25, "noise of one sample\n(signal-to-noise 50)", fontsize=8.3,
            va="top")
    ax.axvline(2.0 / np.sqrt(13000), color=INK, lw=0.9, ls=":")
    ax.text(2.0 / np.sqrt(13000) * 1.05, len(rows) + 0.25,
            "noise after averaging\n13 000 samples", fontsize=8.3, va="top")
    ax.set_xlabel("change in pixel signal caused by 1 nm of height (%)")
    ax.set_title("How strongly each mechanism turns height into signal", loc="left",
                 fontsize=11)
    ax.set_ylim(-0.6, len(rows) + 0.4)
    tidy(ax)
    ax.grid(False, axis="y")
    save(fig, "height-signal")


def main():
    element_positions()
    tube_geometry()
    best = tube_numbers()
    numbers = transfer_functions()
    resolution_vs_gap()
    illumination_geometries()
    demo = fringe_demo()
    height_signal()

    lam = WAVELENGTH_UM
    print("Best tube width and patch width (slit model, tube depth 10 x gap):")
    for gap, (w, patch) in best.items():
        print(f"  gap {gap:5.0f} um: width {w:5.1f} um = {w / np.sqrt(lam * gap):.2f} sqrt(lam z),"
              f" patch {patch:5.1f} um = {patch / np.sqrt(lam * gap):.2f} sqrt(lam z),"
              f" open pixel {2 / np.sqrt(3) * gap:.0f} um")
    print("Tube throughput:", {a: float(tube_throughput(a)) for a in (2, 5, 10, 30, 100)})
    print("Period at 1/1000 contrast, 30 um gap:", numbers)
    print("Fringe demonstration:", demo)


if __name__ == "__main__":
    main()
