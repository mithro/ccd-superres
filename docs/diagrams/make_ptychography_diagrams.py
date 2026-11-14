"""Generate the diagrams for docs/research/ptychography.md.

Run from the repository root:

    python docs/diagrams/make_ptychography_diagrams.py

Writes SVG (used by the document) and PNG copies next to this file, all with
the prefix ``ptycho-``, and prints the numbers quoted in the document. The
toy reconstructions take a few minutes; pass ``--fast`` to skip them.

The calculations here are formulas and small toy reconstructions, not results
from the simulator. Each function says what it leaves out. Published figures
plotted here are listed with their sources on the page itself.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle

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
        "svg.hashsalt": "ptycho",
    }
)

WAVELENGTH_NM = 405.0
PITCH_NM = 1120.0
SENSOR_MM = 3.68


def save(fig, name):
    fig.savefig(OUT / f"ptycho-{name}.svg", bbox_inches="tight",
                metadata={"Date": None})
    fig.savefig(OUT / f"ptycho-{name}.png", bbox_inches="tight", dpi=160)
    plt.close(fig)


def arrow(ax, p0, p1, color=INK, lw=1.4, style="-|>", scale=12, **kw):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=scale,
                                 color=color, lw=lw, shrinkA=0, shrinkB=0, **kw))


def tidy(ax):
    ax.grid(True, color=GRID, lw=0.6, which="major")
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


# --------------------------------------------------------------------------
# 1. The family of arrangements
# --------------------------------------------------------------------------
def fig_family():
    """Side views of five arrangements. Illustrative, not to scale."""
    fig, axes = plt.subplots(1, 5, figsize=(14.5, 3.9))
    titles = [
        "A. Far-field\nptychography",
        "B. Near-field\nptychography",
        "C. Fourier\nptychography",
        "D. Coded sensor\n(lensless, on chip)",
        "E. This project:\nreflection, slanted pair",
    ]
    for ax, title in zip(axes, titles):
        ax.set_xlim(0, 10)
        ax.set_ylim(-1.2, 10)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(title, fontsize=10)

    def sensor(ax, y, x0=1.5, x1=8.5, label="sensor"):
        ax.add_patch(Rectangle((x0, y), x1 - x0, 0.55, color=BLUE))
        ax.text(x1 + 0.15, y + 0.27, label, fontsize=8, va="center", color=BLUE)

    def sample(ax, y, x0=1.0, x1=9.0, label="object", color=SILICON):
        ax.add_patch(Rectangle((x0, y), x1 - x0, 0.4, color=color))
        ax.text(x1 + 0.1, y + 0.2, label, fontsize=8, va="center", color=INK2)

    # A: small spot, far detector, object steps sideways
    ax = axes[0]
    sample(ax, 6.0)
    ax.fill([4.2, 5.8, 5.3, 4.7], [9.6, 9.6, 6.4, 6.4], color=LIGHT)
    ax.fill([4.7, 5.3, 8.3, 1.7], [6.0, 6.0, 1.6, 1.6], color=LIGHT, alpha=0.7)
    sensor(ax, 1.0)
    arrow(ax, (2.0, 7.0), (3.6, 7.0), color=ORANGE)
    ax.text(2.8, 7.3, "step", fontsize=8, ha="center", color=ORANGE)
    ax.text(5, 0.2, "small spot, spread pattern", fontsize=8, ha="center")

    # B: wide structured light, close detector
    ax = axes[1]
    ax.fill([1.6, 8.4, 8.4, 1.6], [9.6, 9.6, 4.6, 4.6], color=LIGHT)
    for x in np.linspace(2.0, 8.0, 13):
        ax.plot([x, x + 0.25], [8.6, 8.6], color=YELLOW, lw=3)
    ax.text(5, 9.0, "patterned light", fontsize=8, ha="center")
    sample(ax, 5.6)
    sensor(ax, 3.6)
    arrow(ax, (2.0, 6.5), (3.6, 6.5), color=ORANGE)
    ax.text(5, 0.9, "whole field at once,\nhologram on the sensor",
            fontsize=8, ha="center")

    # C: lens, light direction changes
    ax = axes[2]
    for x0, c in ((1.0, YELLOW), (5.0, LIGHT), (9.0, YELLOW)):
        ax.fill([x0 - 0.5, x0 + 0.5, 5.5, 4.5], [0.4, 0.4, 3.6, 3.6],
                color=c, alpha=0.8)
    ax.text(5, -0.6, "light from many directions", fontsize=8, ha="center")
    sample(ax, 3.6, 3.0, 7.0)
    ax.add_patch(matplotlib.patches.Ellipse((5, 6.2), 4.0, 0.9, color=AQUA,
                                            alpha=0.6))
    ax.text(7.2, 6.2, "lens", fontsize=8, va="center", color=AQUA)
    sensor(ax, 8.6, 2.5, 7.5)

    # D: coded layer on the sensor, object slides
    ax = axes[3]
    ax.fill([1.6, 8.4, 8.4, 1.6], [9.6, 9.6, 3.2, 3.2], color=LIGHT)
    sample(ax, 5.0)
    arrow(ax, (2.0, 5.9), (3.6, 5.9), color=ORANGE)
    rng = np.random.default_rng(3)
    for x in np.linspace(1.6, 8.3, 40):
        ax.add_patch(Rectangle((x, 3.25), 0.12, 0.2 + 0.25 * rng.random(),
                               color=MASK))
    ax.text(8.65, 3.5, "scattering\nlayer", fontsize=8, va="center", color=MASK)
    sensor(ax, 2.6, label="")
    ax.text(5, 1.2, "the layer is the probe,\nfixed to the sensor",
            fontsize=8, ha="center")

    # E: reflection with slanted pair, sensor above
    ax = axes[4]
    sample(ax, 1.4, label="chip", color=SILICON)
    sensor(ax, 6.2, 2.6, 7.4)
    for sx in (-1, 1):
        x_far = 5 + sx * 5.2
        ax.fill([x_far, x_far, 5 + sx * 1.6, 5 - sx * 0.2],
                [3.3, 4.0, 1.8, 1.8], color=LIGHT)
        arrow(ax, (x_far, 3.6), (5 + sx * 1.2, 2.0), color=YELLOW, lw=1.6)
    for dx in (-1.6, 0, 1.6):
        arrow(ax, (5, 1.9), (5 + dx, 6.1), color=VIOLET, lw=1.1)
    ax.text(5, -0.2, "fringes on the chip,\nscattered light to the sensor",
            fontsize=8, ha="center")
    arrow(ax, (2.6, 7.4), (4.2, 7.4), color=ORANGE)
    ax.text(3.4, 7.7, "scan", fontsize=8, ha="center", color=ORANGE)
    save(fig, "family")


# --------------------------------------------------------------------------
# 2. How many lighting directions: coverage of surface detail
# --------------------------------------------------------------------------
def disc_overlap(d, r):
    """Shared share of area of two discs of radius r whose centres are d apart."""
    d = np.asarray(d, float)
    out = np.zeros_like(d)
    ok = d < 2 * r
    dd = d[ok]
    out[ok] = (2 * r**2 * np.arccos(dd / (2 * r))
               - dd / 2 * np.sqrt(4 * r**2 - dd**2)) / (np.pi * r**2)
    return out


def max_separation(r, share):
    """Largest centre distance that still leaves the given shared share."""
    d = np.linspace(0, 2 * r, 20001)
    return d[np.argmin(np.abs(disc_overlap(d, r) - share))]


def plan_directions(collect_deg, share, slant_deg=72.0):
    """Rings of lighting directions so that every disc shares `share` of its
    area with a neighbour, from straight-down light out to the slant.

    Each lighting direction lets the sensor see a disc of surface detail of
    radius sin(collection angle), centred on the sine of the slant, both in
    units of 1/wavelength. Scalar far-field picture; the pixel's response is
    taken as flat inside the collection angle and zero outside it.
    """
    r = np.sin(np.radians(collect_deg))
    top = np.sin(np.radians(slant_deg))
    dmax = max_separation(r, share)
    n_rings = int(np.ceil(top / dmax))
    radii = [top * (k + 1) / n_rings for k in range(n_rings)]
    counts = []
    for rho in radii:
        if dmax >= 2 * rho:
            counts.append(2)
        else:
            counts.append(int(np.ceil(np.pi / np.arcsin(dmax / (2 * rho)))))
    return r, dmax, radii, counts


def fig_angle_coverage():
    fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.9))
    print("Lighting directions needed (35 % and 60 % shared area):")
    for ax, collect in zip(axes[:2], (30.0, 58.0)):
        r, dmax, radii, counts = plan_directions(collect, 0.35)
        ax.add_patch(Circle((0, 0), r, fc=BLUE, ec=BLUE, alpha=0.25, lw=1))
        for rho, n, col in zip(radii, counts, (AQUA, ORANGE, VIOLET, YELLOW)):
            for k in range(n):
                a = 2 * np.pi * k / n
                ax.add_patch(Circle((rho * np.cos(a), rho * np.sin(a)), r,
                                    fc=col, ec=col, alpha=0.16, lw=0.8))
                ax.plot(rho * np.cos(a), rho * np.sin(a), ".", color=col, ms=4)
        reach = radii[-1] + r
        for lim, ls, lab in ((2.0, "-", "limit: period = wavelength / 2"),
                             (WAVELENGTH_NM / 200.0, "--",
                              "target: 200 nm period")):
            ax.add_patch(Circle((0, 0), lim, fill=False, ec=INK, ls=ls, lw=1.1))
        ax.set_xlim(-2.25, 2.25)
        ax.set_ylim(-2.25, 2.25)
        ax.set_aspect("equal")
        ax.set_xlabel("Fineness of detail across the scan (wavelength / period)")
        ax.set_ylabel("Fineness along the scan (wavelength / period)")
        ax.set_title(f"Sensor collects ±{collect:.0f}°: {1 + sum(counts)} "
                     f"directions\nfinest period {WAVELENGTH_NM / reach:.0f} nm",
                     fontsize=10)
        tidy(ax)
    axes[0].text(0, -2.12, "solid ring: wavelength / 2     dashed ring: 200 nm"
                 " period", fontsize=7.5, ha="center")
    for collect in (30.0, 45.0, 58.0):
        for share in (0.35, 0.60):
            r, dmax, radii, counts = plan_directions(collect, share)
            print(f"  collect ±{collect:.0f}°, share {share:.2f}: rings at sines "
                  f"{[round(x, 2) for x in radii]}, counts {counts}, total "
                  f"{1 + sum(counts)}, finest period "
                  f"{WAVELENGTH_NM / (radii[-1] + r):.0f} nm")
    ax = axes[2]
    n = np.arange(3, 41)
    top = np.sin(np.radians(72.0))
    for collect, col in ((30.0, BLUE), (45.0, AQUA), (58.0, ORANGE)):
        r = np.sin(np.radians(collect))
        ax.plot(n, 100 * disc_overlap(2 * top * np.sin(np.pi / n), r), "-o",
                ms=3, color=col, label=f"sensor collects ±{collect:.0f}°")
    ax.axhline(35, color=INK2, ls="--", lw=1)
    ax.text(40, 36.5, "35 %: published minimum", fontsize=8, ha="right")
    ax.axhline(60, color=INK2, ls=":", lw=1)
    ax.text(40, 61.5, "60 %: comfortable", fontsize=8, ha="right")
    ax.set_xlabel("Number of directions around the outer ring (72° slant)")
    ax.set_ylabel("Area shared by neighbouring discs (%)")
    ax.set_ylim(0, 100)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.set_title("Shared area between neighbours\non the outer ring", fontsize=10)
    tidy(ax)
    save(fig, "angle-coverage")


# --------------------------------------------------------------------------
# 3. Toy ptychography: overlap and position errors
# --------------------------------------------------------------------------
def toy_object(rng, n=128):
    """A chip-like test object: bars of a second reflectance and height."""
    amp = np.full((n, n), 0.6)
    ph = np.zeros((n, n))
    for _ in range(60):
        if rng.random() < 0.5:
            w, h = rng.integers(2, 5), rng.integers(10, 50)
        else:
            w, h = rng.integers(10, 50), rng.integers(2, 5)
        x, y = rng.integers(0, n - w), rng.integers(0, n - h)
        amp[y:y + h, x:x + w] = 1.0
        ph[y:y + h, x:x + w] = 0.8
    return amp * np.exp(1j * ph)


def toy_probe(m=32):
    y, x = np.mgrid[-m // 2:m // 2, -m // 2:m // 2]
    r = np.hypot(x, y)
    p = (r < m * 0.36).astype(float) * np.exp(1j * 0.02 * r**2)
    f = np.hypot(*np.meshgrid(np.fft.fftfreq(m), np.fft.fftfreq(m)))
    return np.fft.ifft2(np.fft.fft2(p) * np.exp(-(f / 0.25) ** 2))


def toy_positions(n, m, step, rng, jitter=0.3):
    pts = []
    for y in np.arange(0, n - m + 1e-9, step):
        for x in np.arange(0, n - m + 1e-9, step):
            pts.append((int(round(y + rng.uniform(-jitter, jitter) * step)),
                        int(round(x + rng.uniform(-jitter, jitter) * step))))
    return np.clip(np.array(pts), 0, n - m)


def toy_measure(obj, probe, pts, rng, photons=1e3):
    m = probe.shape[0]
    inten = np.array([np.abs(np.fft.fft2(probe * obj[y:y + m, x:x + m])) ** 2
                      for y, x in pts])
    s = photons / inten.mean()
    return rng.poisson(inten * s) / s


def toy_solve(inten, pts, probe0, n, iters, rng, refine=False):
    """The extended ptychographic iterative engine of Maiden and Rodenburg,
    with an optional local search over each position (one cell each way)."""
    m = probe0.shape[0]
    obj = np.ones((n, n), complex)
    probe = probe0.copy()
    pts = pts.copy()
    amp = np.sqrt(inten)
    cand = [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]
    for it in range(iters):
        for j in rng.permutation(len(pts)):
            y, x = pts[j]
            if refine and it >= 10 and it % 2 == 0:
                best, be = (y, x), None
                for dy, dx in cand:
                    yy = int(np.clip(y + dy, 0, n - m))
                    xx = int(np.clip(x + dx, 0, n - m))
                    e = np.sum((np.abs(np.fft.fft2(
                        probe * obj[yy:yy + m, xx:xx + m])) - amp[j]) ** 2)
                    if be is None or e < be:
                        be, best = e, (yy, xx)
                y, x = best
                pts[j] = best
            o = obj[y:y + m, x:x + m]
            psi = probe * o
            far = np.fft.fft2(psi)
            d = np.fft.ifft2(amp[j] * np.exp(1j * np.angle(far))) - psi
            obj[y:y + m, x:x + m] = o + np.conj(probe) / (np.abs(probe) ** 2).max() * d
            if it >= 3:
                probe = probe + np.conj(o) / (np.abs(o) ** 2).max() * d
    return obj, probe, pts


def toy_error(obj, true, m):
    """Relative error over the centre, after removing the overall brightness,
    phase and a whole-cell shift, none of which the data can fix."""
    c = slice(m, -m)
    t = true[c, c]
    best = 9.0
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            r = np.roll(obj, (dy, dx), (0, 1))[c, c]
            g = np.vdot(r, t) / np.vdot(r, r)
            best = min(best, np.linalg.norm(g * r - t) / np.linalg.norm(t))
    return best


def fig_toy():
    n, m = 128, 32
    width = 0.72 * m
    y, x = np.mgrid[-m // 2:m // 2, -m // 2:m // 2]
    start = (np.hypot(x, y) < m * 0.4).astype(complex)

    overlaps = np.array([0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1])
    seeds = (1, 2, 3)
    err = np.zeros((len(seeds), len(overlaps)))
    for si, seed in enumerate(seeds):
        rng = np.random.default_rng(seed)
        obj = toy_object(rng, n)
        probe = toy_probe(m)
        for oi, ov in enumerate(overlaps):
            pts = toy_positions(n, m, width * (1 - ov), rng)
            inten = toy_measure(obj, probe, pts, rng)
            rec, _, _ = toy_solve(inten, pts, start, n, 100, rng)
            err[si, oi] = toy_error(rec, obj, m)
    print("Toy: error against overlap (median of three objects):")
    for ov, e in zip(overlaps, np.median(err, 0)):
        print(f"  overlap {ov:.0%}: error {e:.2f}")

    sig = np.array([0.0, 0.5, 1.0, 2.0, 3.0])
    e_plain = np.zeros((len(seeds), len(sig)))
    e_ref = np.zeros_like(e_plain)
    for si, seed in enumerate(seeds):
        rng = np.random.default_rng(10 + seed)
        obj = toy_object(rng, n)
        probe = toy_probe(m)
        pts = toy_positions(n, m, width * 0.25, rng)
        inten = toy_measure(obj, probe, pts, rng)
        for k, s in enumerate(sig):
            bad = np.clip(pts + np.rint(rng.normal(0, s, pts.shape)).astype(int),
                          0, n - m)
            rec, _, _ = toy_solve(inten, bad, start, n, 80, rng)
            e_plain[si, k] = toy_error(rec, obj, m)
            rec, _, _ = toy_solve(inten, bad, start, n, 80, rng, refine=True)
            e_ref[si, k] = toy_error(rec, obj, m)
    print("Toy: error against position error (median of three objects):")
    for s, a, b in zip(sig, np.median(e_plain, 0), np.median(e_ref, 0)):
        print(f"  position error {s:.1f} cells: not corrected {a:.2f}, "
              f"corrected {b:.2f}")

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.3))
    ax = axes[0]
    for row in err:
        ax.plot(100 * overlaps, row, ".", color=BLUE, alpha=0.45)
    ax.plot(100 * overlaps, np.median(err, 0), "-", color=BLUE, lw=2,
            label="median of three test objects")
    ax.axvspan(60, 85, color=AQUA, alpha=0.12)
    ax.text(72.5, 0.45, "range the\nliterature\nrecommends", fontsize=8,
            ha="center", color="#0d7a54")
    ax.set_xlabel("Overlap between neighbouring light patches (%)")
    ax.set_ylabel("Error of the recovered object (0 = perfect)")
    ax.set_xlim(5, 85)
    ax.set_ylim(0, 0.85)
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    ax.set_title("Too little overlap and the solve fails", fontsize=10)
    tidy(ax)
    ax = axes[1]
    ax.plot(sig, np.median(e_plain, 0), "-o", color=ORANGE,
            label="positions taken as given")
    ax.plot(sig, np.median(e_ref, 0), "-o", color=AQUA,
            label="positions also solved (local search)")
    ax.set_xlabel("Error in the positions given to the solver\n"
                  "(reconstruction cells, root mean square)")
    ax.set_ylabel("Error of the recovered object (0 = perfect)")
    ax.set_ylim(0, 0.85)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.set_title("Wrong positions spoil the picture;\nsolving for them "
                 "rescues small errors", fontsize=10)
    tidy(ax)
    save(fig, "toy-overlap-position")


# --------------------------------------------------------------------------
# 4. Pulse length against scan speed
# --------------------------------------------------------------------------
def fig_pulse():
    speed = np.logspace(-3, 1, 200)  # mm/s
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    for t, col in ((1e-2, ORANGE), (1e-3, YELLOW), (1e-4, AQUA), (1e-5, BLUE),
                   (1e-6, VIOLET)):
        label = (f"{t * 1e3:g} ms pulse" if t >= 1e-3
                 else f"{t * 1e6:g} µs pulse")
        ax.loglog(speed, speed * 1e6 * t, color=col, lw=1.8, label=label)
    ax.axhspan(1e-3, 50, color=AQUA, alpha=0.10)
    ax.axhspan(50, 600, color=YELLOW, alpha=0.12)
    ax.axhspan(600, 1e5, color=ORANGE, alpha=0.10)
    ax.text(1.2e-3, 12, "no modelling needed:\nunder a quarter of a 200 nm period",
            fontsize=8, va="center")
    ax.text(1.2e-3, 180, "recoverable by modelling the movement\n"
            "(3 to 10 patterns per frame)", fontsize=8, va="center")
    ax.text(1.2e-3, 6000, "beyond what has been shown", fontsize=8, va="center")
    for v, name in ((0.0084, "baseline\n8.4 µm/s"), (0.736, "20 % of sensor\nper second")):
        ax.axvline(v, color=INK2, ls="--", lw=1)
        ax.text(v * 1.08, 2.2e-3, name, fontsize=8, color=INK2)
    ax.set_xlabel("Scan speed (mm/s)")
    ax.set_ylabel("Distance moved during one pulse (nm)")
    ax.set_ylim(1e-3, 1e5)
    ax.set_xlim(1e-3, 10)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    tidy(ax)
    save(fig, "pulse-timing")
    print("Pulse length for a given smear:")
    for v in (0.0084, 0.736):
        for smear in (50, 600):
            print(f"  speed {v} mm/s, smear {smear} nm: pulse "
                  f"{smear / (v * 1e6) * 1e3:.3g} ms")


# --------------------------------------------------------------------------
# 5. Step size: what each requirement allows
# --------------------------------------------------------------------------
def print_steps():
    print("Largest step per frame of one lighting state:")
    for name, width_um in (("whole sensor lit by one pattern", SENSOR_MM * 1e3),
                           ("fringe strip, ordinary diode (0.5 nm)", 160.0),
                           ("fringe strip, ordinary diode (2 nm)", 40.0)):
        print(f"  {name}: width {width_um:g} um, step at 60 % overlap "
              f"{0.4 * width_um:g} um, at 80 % {0.2 * width_um:g} um")
    print(f"  baseline step 0.28 um: overlap of the whole sensor "
          f"{100 * (1 - 0.28 / (SENSOR_MM * 1e3)):.3f} %")


# --------------------------------------------------------------------------
# 6. Published results against the wavelength used
# --------------------------------------------------------------------------
# (label, finest half-period in nm, wavelength in nm, group). Sources and the
# caveats on each figure are in the tables of docs/research/ptychography.md.
PUBLISHED = [
    ("Luo 2015, oil-filled gap, tilted light", 250, 700, "lt"),
    ("Luo 2016, wavelength scan + tilted light", 250, 500, "lt"),
    ("Greenbaum 2013, ultraviolet LED", 225, 372, "lt"),
    ("Jiang 2021, coded sensor, 532 nm", 345, 532, "lt"),
    ("Jiang 2021, coded sensor, 405 nm", 308, 405, "lt"),
    ("Song 2020, diffuser", 550, 415, "lt"),
    ("Jiang 2020, diffuser", 780, 532, "lt"),
    ("Wang 2026, deep-ultraviolet LED", 435, 266, "lt"),
    ("Gardner 2017, extreme ultraviolet", 12.6, 13.5, "lt"),
    ("Eschen 2022, extreme ultraviolet", 16, 13.5, "lt"),
    ("Zhang 2015, extreme ultraviolet (best axis)", 40, 30, "lr"),
    ("Vlasov 2026, infrared through silicon", 2190, 1064, "lr"),
    ("Shao 2024, extreme ultraviolet (best axis)", 50, 18, "lr"),
    ("Lee 2024, wafer, 405 nm", 1700, 405, "lr"),
    ("Neumann 2008, light through glass", 150, 633, "lens"),
    ("Kuznetsova 2007, slanted beams + reference", 170, 633, "lens"),
    ("Park 2022, 193 nm, reflection", 80, 193, "lens"),
    ("Zhu 2025, reflection", 435, 632, "lens"),
]


def fig_benchmark():
    groups = [("lt", "No lens, light through the sample", BLUE),
              ("lr", "No lens, reflected light", ORANGE),
              ("lens", "With a lens, for comparison", INK2)]
    fig, ax = plt.subplots(figsize=(9.6, 7.0))
    y = 0
    ticks, names = [], []
    print("Published results, half-period over wavelength:")
    for key, title, col in groups:
        rows = sorted([r for r in PUBLISHED if r[3] == key],
                      key=lambda r: r[1] / r[2])
        for label, hp, wl, _ in rows:
            ratio = hp / wl
            ax.barh(y, ratio, color=col, height=0.7)
            ax.text(ratio * 1.06, y, f"{ratio:.2f}", va="center", fontsize=8)
            ticks.append(y)
            names.append(label)
            print(f"  {label}: {ratio:.2f}")
            y += 1
        ax.text(11.5, y - len(rows) / 2 - 0.5, title, color=col, fontsize=9,
                ha="right", va="center", fontweight="bold")
        y += 0.8
    ax.axvline(0.25, color=AQUA, lw=1.6)
    ax.text(0.26, -1.0, "0.25: the limit in air, and the target "
            "(100 nm lines at 405 nm)", color=AQUA, fontsize=8, va="center")
    ax.set_xscale("log")
    ax.set_xlim(0.15, 12)
    ax.set_xticks([0.25, 0.5, 1, 2, 5, 10])
    ax.set_xticklabels(["0.25", "0.5", "1", "2", "5", "10"])
    ax.set_yticks(ticks)
    ax.set_yticklabels(names, fontsize=8.5)
    ax.set_ylim(y, -1.6)
    ax.set_xlabel("Finest line width shown, as a multiple of the wavelength used "
                  "(smaller is better)")
    tidy(ax)
    ax.grid(False, axis="y")
    save(fig, "benchmark")


# --------------------------------------------------------------------------
# 7. How far below the pixel size others have got
# --------------------------------------------------------------------------
def fig_pixel_ratio():
    rows = [
        ("Jiang 2020: diffuser, 1.67 µm pixels", 1670 / 780, BLUE),
        ("Song 2020: diffuser, 1.85 µm pixels", 1850 / 550, BLUE),
        ("Jiang 2022: blood film on sensor, 1.85 µm", 1850 / 435, BLUE),
        ("Luo 2015: tilted light, 1.12 µm pixels", 1120 / 250, BLUE),
        ("Greenbaum 2013: shifted light, 1.12 µm", 1120 / 225, BLUE),
        ("Jiang 2021: coded sensor, 532 nm, 1.85 µm", 1850 / 345, BLUE),
        ("Jiang 2021: coded sensor, 405 nm, 1.85 µm", 1850 / 308, BLUE),
        ("This project, stage 2: 200 nm lines", PITCH_NM / 200, YELLOW),
        ("This project, stage 2: 150 nm lines", PITCH_NM / 150, YELLOW),
        ("This project, goal: 100 nm lines", PITCH_NM / 100, ORANGE),
    ]
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    for i, (label, ratio, col) in enumerate(rows):
        ax.barh(i, ratio, color=col, height=0.7)
        ax.text(ratio + 0.15, i, f"{ratio:.1f}", va="center", fontsize=8.5)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows], fontsize=8.5)
    ax.invert_yaxis()
    ax.axvline(1850 / 308, color=INK2, ls="--", lw=1)
    ax.text(1850 / 308 + 0.1, -0.75, "largest published", fontsize=8, color=INK2)
    ax.set_xlim(0, 13)
    ax.set_xlabel("Pixel width divided by the finest line width resolved")
    tidy(ax)
    ax.grid(False, axis="y")
    save(fig, "pixel-ratio")
    print("Pixel width over line width:")
    for label, ratio, _ in rows:
        print(f"  {label}: {ratio:.1f}")


# --------------------------------------------------------------------------
# 8. Where the beat between a beam pair travels
# --------------------------------------------------------------------------
def fig_beat_path():
    """Side view of the rays that meet at one pixel, for a sensor 3.68 mm wide
    held 1 mm above the chip. Drawn to scale in millimetres. Straight rays
    only; the sensor body blocks light that would have to pass through it."""
    from matplotlib.lines import Line2D

    gap, half = 1.0, SENSOR_MM / 2
    t_in = np.tan(np.radians(72))
    t_out = np.tan(np.radians(64))
    px = -1.3                      # the pixel looked at
    a = px + gap * t_out           # chip point whose fine lines turn beam 1 back
    b = px + gap * t_in            # chip point that mirrors beam 2 to the pixel
    c = px - gap * t_in            # chip point that mirrors beam 1 to the pixel
    fig, axes = plt.subplots(2, 1, figsize=(11.5, 5.6))
    for ax, pair in zip(axes, (False, True)):
        ax.set_xlim(-6.6, 6.6)
        ax.set_ylim(-0.75, 1.75)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.add_patch(Rectangle((-6.5, -0.3), 13, 0.3, color=SILICON))
        ax.text(6.45, -0.15, "chip", fontsize=8.5, ha="right", va="center")
        ax.add_patch(Rectangle((-half, gap), 2 * half, 0.22, color=BLUE))
        ax.text(0, gap + 0.36, "sensor, 3.68 mm wide, 1 mm above the chip",
                fontsize=8.5, color=BLUE, ha="center")
        ax.plot([px], [gap], "v", color=INK, ms=7)
        ax.text(px - 0.15, gap - 0.05, "pixel", fontsize=8.5, ha="right", va="top")
        arrow(ax, (a - 1.25 * t_in, 1.25), (a, 0), color=YELLOW, lw=2.0)
        arrow(ax, (a, 0), (px, gap), color=VIOLET, lw=2.0)
        ax.plot([a], [0], "s", color=MASK, ms=5)
        ax.text(a, -0.52, "fine lines", fontsize=8, ha="center")
        handles = [Line2D([], [], color=YELLOW, lw=2, label="beam 1, arriving at 72°"),
                   Line2D([], [], color=VIOLET, lw=2,
                          label="beam 1 turned back by the fine lines")]
        if pair:
            arrow(ax, (b + 1.25 * t_in, 1.25), (b, 0), color=AQUA, lw=2.0)
            arrow(ax, (b, 0), (px, gap), color=AQUA, lw=1.4, ls="--")
            handles += [Line2D([], [], color=AQUA, lw=2, label="beam 2, arriving at 72°"),
                        Line2D([], [], color=AQUA, lw=1.4, ls="--",
                               label="beam 2 mirrored by the chip: the reference")]
            ax.set_title("Beam pair: the turned-back light and the reference "
                         "reach the pixel 8° apart. Stripes about 8 µm wide.",
                         fontsize=9.5)
        else:
            arrow(ax, (c - 1.25 * t_in, 1.25), (c, 0), color=YELLOW, lw=1.2)
            arrow(ax, (c, 0), (px, gap), color=YELLOW, lw=1.2, ls="--")
            handles += [Line2D([], [], color=YELLOW, lw=1.2, ls="--",
                               label="beam 1 mirrored by the chip")]
            ax.set_title("One beam: the turned-back light meets only beam 1's "
                         "own mirror reflection, 136° apart. Stripes about "
                         "220 nm wide.", fontsize=9.5)
        ax.legend(handles=handles, frameon=False, fontsize=8, ncol=2,
                  loc="lower left", bbox_to_anchor=(0.0, -0.32))
    fig.subplots_adjust(hspace=0.55)
    save(fig, "beat-path")
    print(f"Beat path, gap 1 mm: pixel at {px} mm; fine lines at {a:.2f} mm; "
          f"reference mirrored at {b:.2f} mm; separation {b - a:.2f} mm")
    lit = gap * t_in - half
    print(f"  chip under the sensor lit by both beams: |x| < {lit:.2f} mm; "
          f"smallest gap with any such region {half / t_in:.2f} mm")
    print(f"  pixels reached by both turned-back light (64 deg) and reference: "
          f"x from {-half:.2f} to {lit - gap * t_out:.2f} mm")
    s72 = np.sin(np.radians(72))
    for out in (0.85, 0.90):
        print(f"  scattered sine {out}, reference sine {s72:.3f}: stripe period "
              f"at the sensor {WAVELENGTH_NM / (s72 - out) / 1e3:.1f} um; "
              f"against own reflection {WAVELENGTH_NM / (s72 + out):.0f} nm")
    print(f"  sideways travel per mm of gap at 72 deg: {t_in:.2f} mm")
    c64, c72 = np.cos(np.radians(64)), np.cos(np.radians(72))
    slope = 2 * s72
    offset = s72 * gap * (t_out + t_in) + gap / c64 - gap / c72
    print(f"  route difference, signal minus reference: {slope:.2f} mm per mm "
          f"across the sensor, {slope * px + offset:.2f} mm at the pixel drawn")
    for width in (0.5, 2.0):
        lc = (WAVELENGTH_NM ** 2 / width) * 1e-6
        print(f"  diode spread {width} nm: coherence length {lc:.2f} mm, band "
              f"on the sensor {2 * lc / slope:.2f} mm, largest gap by the "
              f"rule 2 lambda^2 / spread {2 * lc:.2f} mm")
    print(f"  grating period for 72 deg: {WAVELENGTH_NM / s72:.0f} nm; a 2400 "
          f"line/mm grating gives {1e6 / 2400 / 2:.0f} nm stripes at "
          f"{np.degrees(np.arcsin(WAVELENGTH_NM * 2400e-6)):.1f} deg")
    print(f"  cone needed for a 1 um repeat: NA {WAVELENGTH_NM / 2000:.2f}, "
          f"{np.degrees(np.arcsin(WAVELENGTH_NM / 2000)):.1f} deg")
    sigma = 550 / 2.355
    for period in (450, 200):
        print(f"  pixel as a 550 nm bump, contrast passed at {period} nm "
              f"period: {np.exp(-2 * np.pi ** 2 * sigma ** 2 / period ** 2):.2g}")


if __name__ == "__main__":
    import sys

    fig_family()
    fig_angle_coverage()
    fig_pulse()
    print_steps()
    fig_benchmark()
    fig_pixel_ratio()
    fig_beat_path()
    if "--fast" not in sys.argv:
        fig_toy()
