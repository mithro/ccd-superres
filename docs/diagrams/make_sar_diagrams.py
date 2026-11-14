"""Generate the diagrams for docs/research/synthetic-aperture-radar.md.

Run from the repository root:

    python docs/diagrams/make_sar_diagrams.py

Writes SVG (used by the document) and PNG copies next to this file, all with
the prefix ``sar-``, and prints the numbers quoted in the document.

Everything here is an analytic formula or a small one-dimensional toy
calculation written for the figure. None of it is a result from the
project's simulator levels. Only numpy and matplotlib are needed.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle

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
        "svg.hashsalt": "ccd-superres",
    }
)

PITCH_NM = 1120.0  # IMX219 pixel pitch
WAVELENGTH_NM = 405.0
SLANT_DEG = 70.0


def save(fig, name):
    fig.savefig(OUT / f"sar-{name}.svg", bbox_inches="tight", metadata={"Date": None})
    fig.savefig(OUT / f"sar-{name}.png", bbox_inches="tight", dpi=160)
    plt.close(fig)


def tidy(ax):
    ax.grid(True, color=GRID, lw=0.6, which="major")
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def arrow(ax, p0, p1, color=INK, lw=1.4, style="-|>", scale=11, **kw):
    ax.add_patch(
        FancyArrowPatch(
            p0, p1, arrowstyle=style, mutation_scale=scale, color=color, lw=lw,
            shrinkA=0, shrinkB=0, **kw
        )
    )


def blank(ax, xlim, ylim):
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.axis("off")


# --------------------------------------------------------------------------
# 1. Radar modes beside the instrument arrangement that matches each
# --------------------------------------------------------------------------
def fig_modes():
    fig, axes = plt.subplots(2, 4, figsize=(13.2, 6.0))
    titles = [
        "Stripmap\nbeam fixed, sweeps a strip",
        "Spotlight\nbeam steered to stay on one patch",
        "Receiver moves,\ntransmitter stands still",
        "Inverse: radar still,\ntarget turns",
    ]
    lower = [
        "Light source rides\nwith the sensor",
        "Light direction stepped\nor swept during the scan",
        "Light fixed to the chip stage,\nsensor moves (the baseline)",
        "Chip turns under a fixed\nslanted beam",
    ]
    for col in range(4):
        # ---------------- radar row
        ax = axes[0, col]
        blank(ax, (0, 10), (0, 6.4))
        ax.set_title(titles[col], fontsize=9.5)
        ax.add_patch(Rectangle((0.3, 0.3), 9.4, 0.35, color=SILICON))
        ax.text(9.7, 0.02, "ground", ha="right", va="top", fontsize=8, color=INK2)
        xs = [2.0, 5.0, 8.0]
        if col == 0:
            for x in xs:
                ax.add_patch(Polygon([(x, 5.2), (x - 1.0, 0.65), (x + 1.0, 0.65)],
                                     color=BLUE, alpha=0.18, lw=0))
                ax.add_patch(Rectangle((x - 0.3, 5.2), 0.6, 0.3, color=BLUE))
            arrow(ax, (1.2, 5.95), (8.8, 5.95), color=INK2)
            ax.text(5, 6.05, "flight path", ha="center", va="bottom", fontsize=8, color=INK2)
        elif col == 1:
            for x in xs:
                ax.add_patch(Polygon([(x, 5.2), (4.2, 0.65), (5.8, 0.65)],
                                     color=BLUE, alpha=0.18, lw=0))
                ax.add_patch(Rectangle((x - 0.3, 5.2), 0.6, 0.3, color=BLUE))
            arrow(ax, (1.2, 5.95), (8.8, 5.95), color=INK2)
            ax.text(5, 6.05, "flight path", ha="center", va="bottom", fontsize=8, color=INK2)
        elif col == 2:
            ax.add_patch(Polygon([(0.9, 4.2), (2.6, 0.65), (7.6, 0.65)],
                                 color=ORANGE, alpha=0.18, lw=0))
            ax.add_patch(Rectangle((0.6, 4.2), 0.6, 0.3, color=ORANGE))
            ax.text(0.9, 4.6, "transmitter", ha="center", va="bottom", fontsize=8, color=ORANGE)
            for x in (4.0, 6.0, 8.0):
                ax.add_patch(Rectangle((x - 0.3, 5.2), 0.6, 0.3, color=BLUE))
                arrow(ax, (5.0, 0.7), (x, 5.15), color=BLUE, lw=1.0)
            arrow(ax, (3.4, 5.95), (8.8, 5.95), color=INK2)
            ax.text(6.1, 6.05, "receiver path", ha="center", va="bottom", fontsize=8, color=INK2)
        else:
            ax.add_patch(Rectangle((0.6, 4.6), 0.6, 0.3, color=BLUE))
            ax.text(0.9, 5.0, "radar", ha="center", va="bottom", fontsize=8, color=BLUE)
            ax.add_patch(Polygon([(1.2, 4.7), (4.0, 1.4), (7.4, 1.4)],
                                 color=BLUE, alpha=0.18, lw=0))
            ax.add_patch(Rectangle((4.3, 1.1), 2.8, 0.5, color=MASK))
            ax.text(5.7, 1.85, "target", ha="center", va="bottom", fontsize=8, color=INK2)
            ax.add_patch(
                FancyArrowPatch((7.6, 0.9), (7.6, 2.0), connectionstyle="arc3,rad=0.9",
                                arrowstyle="-|>", mutation_scale=11, color=INK2, lw=1.2))
        # ---------------- instrument row
        ax = axes[1, col]
        blank(ax, (0, 10), (0, 6.4))
        ax.set_title(lower[col], fontsize=9.5, color=INK)
        ax.add_patch(Rectangle((0.3, 0.6), 9.4, 0.5, color=SILICON))
        ax.text(9.7, 0.5, "chip", ha="right", va="top", fontsize=8, color=INK2)
        sx = 3.2 if col != 3 else 3.0
        ax.add_patch(Rectangle((sx, 2.2), 4.0, 0.35, color=BLUE))
        ax.text(sx + 2.0, 2.62, "sensor", ha="center", va="bottom", fontsize=8, color=BLUE)
        if col == 0:
            ax.add_patch(Rectangle((1.9, 2.2), 0.5, 0.35, color=ORANGE))
            ax.plot([2.4, 3.2], [2.38, 2.38], color=INK2, lw=1.2)
            for dx in (0.0, 0.5, 1.0):
                arrow(ax, (2.15, 2.2), (3.0 + dx * 1.6, 1.12), color=ORANGE, lw=1.0)
            arrow(ax, (2.2, 3.6), (7.0, 3.6), color=INK2)
            ax.text(4.6, 3.7, "source and sensor move together", ha="center",
                    va="bottom", fontsize=8, color=INK2)
        elif col == 1:
            for ang, a in ((-62, 0.9), (-35, 0.6), (35, 0.6), (62, 0.9)):
                t = np.deg2rad(ang)
                p1 = (5.2, 1.12)
                p0 = (5.2 + 4.3 * np.sin(t), 1.12 + 4.3 * np.cos(t) * 0.55 + 0.4)
                arrow(ax, p0, p1, color=ORANGE, lw=1.0, alpha=a)
            ax.text(5.2, 4.3, "directions used in turn", ha="center", fontsize=8, color=ORANGE)
            arrow(ax, (3.4, 3.3), (7.0, 3.3), color=INK2)
        elif col == 2:
            for x in (0.6, 1.4, 2.2):
                arrow(ax, (x, 3.9), (x + 2.6, 1.12), color=ORANGE, lw=1.0)
            ax.text(0.5, 4.05, "fixed beam", ha="left", va="bottom", fontsize=8, color=ORANGE)
            arrow(ax, (3.4, 3.3), (7.0, 3.3), color=INK2)
            ax.text(5.2, 3.4, "sensor moves", ha="center", va="bottom", fontsize=8, color=INK2)
        else:
            for x in (0.4, 1.2, 2.0):
                arrow(ax, (x, 3.9), (x + 2.6, 1.12), color=ORANGE, lw=1.0)
            ax.text(0.3, 4.05, "fixed beam", ha="left", va="bottom", fontsize=8, color=ORANGE)
            ax.add_patch(
                FancyArrowPatch((8.2, 0.3), (8.2, 1.5), connectionstyle="arc3,rad=0.9",
                                arrowstyle="-|>", mutation_scale=11, color=INK2, lw=1.2))
            ax.text(8.9, 1.75, "chip turns", ha="center", va="bottom", fontsize=8, color=INK2)
    fig.text(0.008, 0.73, "Radar", rotation=90, va="center", fontsize=11, weight="bold")
    fig.text(0.008, 0.27, "This instrument", rotation=90, va="center", fontsize=11,
             weight="bold")
    fig.subplots_adjust(left=0.035, right=0.995, top=0.92, bottom=0.02, wspace=0.05,
                        hspace=0.22)
    save(fig, "modes-map")


# --------------------------------------------------------------------------
# 2. Classical autofocus rehearsal: phase errors, PGA and sharpness
# --------------------------------------------------------------------------
def pga(data, iterations=8):
    """Phase gradient autofocus on aperture-domain data (lines x aperture)."""
    n = data.shape[1]
    total = np.zeros(n)
    width = n // 2
    for _ in range(iterations):
        img = np.fft.fftshift(np.fft.ifft(data, axis=1), axes=1)
        peaks = np.argmax(np.abs(img), axis=1)
        centred = np.array([np.roll(row, n // 2 - p) for row, p in zip(img, peaks)])
        window = np.zeros(n)
        window[n // 2 - width // 2: n // 2 + width // 2 + 1] = 1.0
        g = np.fft.fft(np.fft.ifftshift(centred * window, axes=1), axis=1)
        grad = np.angle(np.sum(np.conj(g[:, :-1]) * g[:, 1:], axis=0))
        est = np.concatenate([[0.0], np.cumsum(grad)])
        est -= np.polyval(np.polyfit(np.arange(n), est, 1), np.arange(n))
        data = data * np.exp(-1j * est)
        total += est
        width = max(8, int(width * 0.6))
    return data, total


def sharpness(img):
    p = np.abs(img) ** 2
    return np.sum(p ** 2) / np.sum(p) ** 2


def sharpness_autofocus(data, iterations=300):
    """Maximise image sharpness over one phase per pulse, by gradient ascent.

    The gradient of the sum of squared brightness with respect to each
    pulse's phase has a closed form, so every step costs two transforms.
    """
    n = data.shape[1]
    phase = np.zeros(n)

    def score(p):
        return np.sum(np.abs(np.fft.ifft(data * np.exp(-1j * p), axis=1)) ** 4)

    best = score(phase)
    step = 1.0
    for _ in range(iterations):
        g = data * np.exp(-1j * phase)
        img = np.fft.ifft(g, axis=1)
        back = np.fft.ifft(np.abs(img) ** 2 * np.conj(img), axis=1)
        grad = 4 * np.sum(np.imag(g * back), axis=0)
        grad /= np.abs(grad).max() + 1e-30
        while step > 1e-4:
            trial = phase + step * grad
            s = score(trial)
            if s > best:
                phase, best = trial, s
                step *= 1.5
                break
            step *= 0.5
    return data * np.exp(-1j * phase), phase


def detrended(phase):
    """Remove the constant and the straight-line part, which only shift the picture.

    Phases are compared modulo a full turn, because a pulse that is out by a
    whole number of turns is not in error at all.
    """
    n = len(phase)
    spec = np.fft.fft(np.exp(1j * phase), 64 * n)
    k = int(np.argmax(np.abs(spec)))
    ramp = 2 * np.pi * k / (64 * n) * np.arange(n)
    rest = np.angle(np.exp(1j * (phase - ramp)) * np.exp(-1j * np.angle(spec[k])))
    x = np.arange(n)
    return rest - np.polyval(np.polyfit(x, rest, 1), x)


def detrended_rms(phase):
    return np.std(detrended(phase))


def fig_autofocus():
    rng = np.random.default_rng(7)
    lines, n = 48, 512
    scene = 0.05 * (rng.normal(size=(lines, n)) + 1j * rng.normal(size=(lines, n)))
    for r in range(lines):
        for _ in range(3):
            scene[r, rng.integers(40, n - 40)] += (
                rng.uniform(1.5, 4.0) * np.exp(2j * np.pi * rng.uniform()))
    clean = np.fft.fft(scene, axis=1)
    u = np.linspace(-1, 1, n)
    # Low-order bend (wrong speed and a slow wander) plus a small fast part.
    err = 9.0 * u ** 2 - 5.0 * u ** 3 + 2.0 * np.sin(2 * np.pi * 1.7 * u + 0.6)
    err_fast = err + 0.25 * rng.normal(size=n)
    data = clean * np.exp(1j * err_fast)
    data += 0.5 * (rng.normal(size=data.shape) + 1j * rng.normal(size=data.shape))

    fixed_pga, est_pga = pga(data.copy())
    fixed_sh, est_sh = sharpness_autofocus(data.copy())

    x_all = np.arange(n)
    rms_in = np.std(err_fast - np.polyval(np.polyfit(x_all, err_fast, 1), x_all))
    rms_pga = detrended_rms(err_fast - est_pga)
    rms_sh = detrended_rms(err_fast - est_sh)
    print("autofocus rehearsal:")
    print(f"  phase error applied      {rms_in:5.2f} rad rms")
    print(f"  left after PGA           {rms_pga:5.2f} rad rms")
    print(f"  left after sharpness     {rms_sh:5.2f} rad rms")
    for name, d in (("blurred", data), ("PGA", fixed_pga), ("sharpness", fixed_sh),
                    ("no error", clean)):
        print(f"  sharpness of image, {name:10s} {sharpness(np.fft.ifft(d, axis=1)) * 1e3:6.2f} e-3")

    fig = plt.figure(figsize=(11.5, 5.6))
    gs = fig.add_gridspec(2, 4, height_ratios=[1.0, 0.8], hspace=0.42, wspace=0.12)
    panels = [("True scene", scene), ("Recorded with path error", np.fft.ifft(data, axis=1)),
              ("After phase gradient autofocus", np.fft.ifft(fixed_pga, axis=1)),
              ("After sharpness maximisation", np.fft.ifft(fixed_sh, axis=1))]
    for k, (title, img) in enumerate(panels):
        ax = fig.add_subplot(gs[0, k])
        a = np.abs(img)
        ax.imshow(a[:, 120:392], cmap="gray_r", aspect="auto", vmax=2.5,
                  interpolation="nearest")
        ax.set_title(title, fontsize=9.5)
        ax.set_xticks([])
        ax.set_yticks([])
        if k == 0:
            ax.set_ylabel("Line of the image")
        ax.set_xlabel("Position along the path")
    ax = fig.add_subplot(gs[1, :])
    x = np.arange(n)
    lin = lambda p: p - np.polyval(np.polyfit(x, p, 1), x)
    ax.plot(x, lin(err_fast), color=INK2, lw=1.0, label=f"Error applied ({rms_in:.1f} rad rms)")
    ax.plot(x, lin(err_fast) - detrended(err_fast - est_pga), color=BLUE, lw=1.6,
            label=f"Estimated by phase gradient autofocus (leaves {rms_pga:.2f} rad rms)")
    ax.plot(x, lin(err_fast) - detrended(err_fast - est_sh), color=ORANGE, lw=1.6, ls="--",
            label=f"Estimated by sharpness maximisation (leaves {rms_sh:.2f} rad rms)")
    ax.set_xlabel("Pulse number along the path")
    ax.set_ylabel("Phase error (radians)")
    ax.set_xlim(0, n - 1)
    ax.legend(frameon=False, fontsize=8.5, ncol=1, loc="upper center")
    tidy(ax)
    save(fig, "autofocus-demo")
    return rms_in, rms_pga, rms_sh


# --------------------------------------------------------------------------
# 3. Brightness-only autofocus: gap from sharpness and from sub-aperture drift
# --------------------------------------------------------------------------
SUB = 11  # fine samples per pixel
DX_NM = PITCH_NM / SUB


FEATURES = [(-310e3, 600, 0.35, 0.0), (-180e3, 400, 1.0, 1.2), (-60e3, 1200, 0.5, 0.6),
            (20e3, 500, 0.3, 0.0), (95e3, 300, 1.0, 1.5), (150e3, 900, 0.6, -0.8),
            (260e3, 700, 0.4, 0.3), (330e3, 400, 1.0, 2.0)]


def hologram(gap_um, rng, n_pix=2048, photons=20000.0, feats=None):
    """Brightness on the pixels above a mostly flat mirror with a few lines."""
    n = n_pix * SUB
    x = (np.arange(n) - n / 2) * DX_NM
    refl = np.ones(n, dtype=complex)
    feats = FEATURES if feats is None else feats
    for centre, width, amp, phase in feats:
        refl[np.abs(x - centre) < width / 2] = amp * np.exp(1j * phase)
    f = np.fft.fftfreq(n, d=DX_NM)
    arg = 1.0 - (WAVELENGTH_NM * f) ** 2
    kz = 2 * np.pi / WAVELENGTH_NM * np.sqrt(np.maximum(arg, 0.0))
    h = np.where(arg > 0, np.exp(1j * kz * gap_um * 1e3), 0.0)
    field = np.fft.ifft(np.fft.fft(refl) * h)
    inten = np.abs(field) ** 2
    pix = inten.reshape(n_pix, SUB).mean(axis=1)
    if rng is not None:
        pix = rng.poisson(pix * photons) / photons
    return pix, x.reshape(n_pix, SUB).mean(axis=1), np.abs(refl.reshape(n_pix, SUB).mean(axis=1))


def refocus(pix, gap_um, band=None):
    """Propagate the recorded brightness back by an assumed gap."""
    n = len(pix)
    f = np.fft.fftfreq(n, d=PITCH_NM)
    kz = 2 * np.pi / WAVELENGTH_NM * np.sqrt(1.0 - (WAVELENGTH_NM * f) ** 2)
    spec = np.fft.fft(pix - pix.mean()) * np.exp(-1j * kz * gap_um * 1e3)
    if band == "+":
        spec = np.where(f > 0, spec, 0.0)
    elif band == "-":
        spec = np.where(f < 0, spec, 0.0)
    return np.fft.ifft(spec)


def subpixel_shift(a, b, upsample=64):
    """Shift of b relative to a, in samples, from the correlation peak."""
    n = len(a)
    spec = np.fft.fft(a - a.mean()) * np.conj(np.fft.fft(b - b.mean()))
    big = np.zeros(n * upsample, dtype=complex)
    big[: n // 2] = spec[: n // 2]
    big[-n // 2:] = spec[-n // 2:]
    corr = np.fft.ifft(big).real
    k = int(np.argmax(corr))
    if k > n * upsample // 2:
        k -= n * upsample
    return -k / upsample


def half_picture_shift(pix, gap_um):
    """Shift, in pixels, between pictures made from the two halves of the views."""
    a = np.abs(refocus(pix, gap_um, "+")) ** 2
    b = np.abs(refocus(pix, gap_um, "-")) ** 2
    return subpixel_shift(a, b)


def fig_gap_autofocus():
    rng = np.random.default_rng(3)
    true_gap = 300.0
    pix, xp, truth = hologram(true_gap, rng)
    trial = np.arange(240.0, 360.01, 1.0)
    sharp = np.array([sharpness(refocus(pix, g)) for g in trial])
    best = trial[int(np.argmax(sharp))]
    fine = np.arange(best - 3, best + 3.001, 0.05)
    sharp_fine = np.array([sharpness(refocus(pix, g)) for g in fine])
    best_fine = fine[int(np.argmax(sharp_fine))]

    drift_gap = np.arange(260.0, 340.01, 4.0)
    drift = []
    for g in drift_gap:
        drift.append(half_picture_shift(pix, g))
    drift = np.array(drift)
    slope, icept = np.polyfit(drift_gap, drift, 1)
    gap_from_drift = -icept / slope
    resid_um = np.std(drift - (slope * drift_gap + icept)) / abs(slope)
    predicted = WAVELENGTH_NM / (2 * PITCH_NM) * 1e3 / PITCH_NM  # pixels per um, upper bound
    # Repeat with fresh noise to see how far the two estimates scatter.
    est_s, est_d = [], []
    for seed in range(20):
        p2, _, _ = hologram(true_gap, np.random.default_rng(100 + seed))
        s2 = [sharpness(refocus(p2, g)) for g in fine]
        est_s.append(fine[int(np.argmax(s2))])
        d2 = [half_picture_shift(p2, g) for g in (280.0, 320.0)]
        est_d.append(280.0 - d2[0] * 40.0 / (d2[1] - d2[0]))
    print("gap autofocus on brightness-only recording (true gap 300 um):")
    print(f"  sharpness peak at          {best_fine:7.2f} um")
    print(f"  drift zero crossing at     {gap_from_drift:7.2f} um")
    print(f"  drift slope                {slope:7.4f} px/um (upper bound for evenly weighted views {predicted:.4f})")
    print(f"  scatter about the line     {resid_um:7.2f} um of gap")
    print(f"  20 noise trials, sharpness {np.mean(est_s):7.2f} +- {np.std(est_s):.2f} um")
    print(f"  20 noise trials, drift     {np.mean(est_d):7.2f} +- {np.std(est_d):.2f} um")
    print("  bias against line width, no noise (all eight lines the same width):")
    for width in (300, 1000, 2000, 4000, 8000):
        feats = [(c, width, 0.5, 0.0) for c, _, _, _ in FEATURES]
        p3, _, _ = hologram(true_gap, None, feats=feats)
        wide = np.arange(288.0, 312.01, 0.1)
        s3 = wide[int(np.argmax([sharpness(refocus(p3, g)) for g in wide]))]
        d3 = [half_picture_shift(p3, g) for g in (290.0, 310.0)]
        print(f"    width {width:5d} nm: sharpness {s3 - true_gap:+5.1f} um, "
              f"drift {290.0 - d3[0] * 20.0 / (d3[1] - d3[0]) - true_gap:+5.1f} um")
    na = WAVELENGTH_NM / (2 * PITCH_NM)
    print(f"  depth of focus lambda/NA^2 {WAVELENGTH_NM / na ** 2 / 1e3:7.2f} um (NA {na:.3f})")

    fig, axes = plt.subplots(2, 2, figsize=(11.5, 6.6))
    ax = axes[0, 0]
    sel = slice(700, 1348)
    ax.plot(xp[sel] / 1e3, pix[sel], color=INK2, lw=0.7)
    ax.set_title("What the pixels record: brightness only, 300 µm above the surface",
                 fontsize=9.5)
    ax.set_xlabel("Position (µm)")
    ax.set_ylabel("Brightness (flat mirror = 1)")
    tidy(ax)
    ax = axes[0, 1]
    for g, c, lab in ((true_gap + 40, ORANGE, "refocused with the gap wrong by 40 µm"),
                      (best_fine, BLUE, "refocused at the gap autofocus found")):
        ax.plot(xp[sel] / 1e3, np.abs(refocus(pix, g))[sel], color=c, lw=1.0, label=lab)
    ax.plot(xp[sel] / 1e3, 0.45 * (1 - truth[sel]) - 0.42, color=INK, lw=1.0,
            label="true lines (drawn below, not to scale)")
    ax.set_title("Refocused by computation", fontsize=9.5)
    ax.set_xlabel("Position (µm)")
    ax.set_ylabel("Strength of refocused picture")
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    tidy(ax)
    ax = axes[1, 0]
    ax.plot(trial, sharp / sharp.max(), color=BLUE, lw=1.6)
    ax.axvline(true_gap, color=INK2, lw=1.0, ls=":")
    ax.text(true_gap + 1.5, 0.3, "true gap", fontsize=8.5, color=INK2)
    ax.set_title("Method 1: try many gaps, keep the sharpest picture", fontsize=9.5)
    ax.set_xlabel("Gap assumed in the refocusing (µm)")
    ax.set_ylabel("Sharpness (best = 1)")
    tidy(ax)
    ax = axes[1, 1]
    ax.plot(drift_gap, drift * PITCH_NM / 1e3, "o", color=ORANGE, ms=5,
            label="measured shift between the two half-pictures")
    ax.plot(drift_gap, (slope * drift_gap + icept) * PITCH_NM / 1e3, color=INK2, lw=1.0,
            label="straight-line fit")
    ax.axhline(0, color=GRID, lw=1.0)
    ax.axvline(true_gap, color=INK2, lw=1.0, ls=":")
    ax.set_title("Method 2: split the views in two and measure how far they disagree",
                 fontsize=9.5)
    ax.set_xlabel("Gap assumed in the refocusing (µm)")
    ax.set_ylabel("Shift between half-pictures (µm)")
    ax.legend(frameon=False, fontsize=8)
    tidy(ax)
    fig.tight_layout()
    save(fig, "gap-autofocus-demo")


# --------------------------------------------------------------------------
# 4. How well positions must be known
# --------------------------------------------------------------------------
def fig_phase_tolerance():
    rng = np.random.default_rng(11)
    periods = [(203.0, VIOLET, "203 nm: finest surface period, light from all directions"),
               (405.0, BLUE, "405 nm: finest surface period, light straight down"),
               (2240.0, AQUA, "2 240 nm: finest stripe two pixels can sample")]
    err = np.logspace(-0.5, 3, 200)
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.3))
    ax = axes[0]
    print("position tolerance (random error, energy kept in the sharp picture):")
    for period, colour, label in periods:
        sigma = 2 * np.pi * err / period
        ax.plot(err, np.exp(-sigma ** 2), color=colour, lw=1.8, label=label)
        mc_err = np.array([0.01, 0.03, 0.1, 0.2, 0.4]) * period
        kept = []
        for e in mc_err:
            ph = 2 * np.pi * rng.normal(scale=e, size=(200, 512)) / period
            kept.append(np.mean(np.abs(np.mean(np.exp(1j * ph), axis=1)) ** 2))
        ax.plot(mc_err, kept, "o", color=colour, ms=4)
        for target_db in (-20.0, -10.0):
            s = np.sqrt(10 ** (target_db / 10))
            print(f"  period {period:6.0f} nm: sidelobe energy {target_db:.0f} dB at "
                  f"{s * period / (2 * np.pi):6.1f} nm rms ({s:.2f} rad)")
    ax.set_xscale("log")
    ax.set_xlabel("Random position error, frame to frame (nm, rms)")
    ax.set_ylabel("Share of energy left in the sharp picture")
    ax.set_title("Random errors: energy leaks out of the picture", fontsize=10)
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    tidy(ax)

    ax = axes[1]
    n = 2048
    u = np.linspace(-1, 1, n)
    x = np.fft.fftshift(np.fft.fftfreq(8 * n, d=1 / n))
    for q, colour in ((0.0, INK2), (np.pi / 4, AQUA), (np.pi, BLUE), (3 * np.pi, ORANGE)):
        ap = np.exp(1j * q * u ** 2)
        psf = np.abs(np.fft.fftshift(np.fft.fft(ap, 8 * n))) ** 2
        psf /= (n ** 2)
        half = psf >= psf.max() / 2
        width = np.ptp(x[half])
        if q == 0:
            width0 = width
        lab = "no error" if q == 0 else f"{q:.1f} rad at the ends"
        ax.plot(x, psf, color=colour, lw=1.5,
                label=f"{lab}: peak {psf.max():.2f}, width ×{width / width0:.1f}")
        print(f"  bend of {q:5.2f} rad at aperture edge: peak {psf.max():.3f}, "
              f"width x{width / width0:.2f}")
    ax.set_xlim(-5, 5)
    ax.set_xlabel("Position in the picture (resolution cells)")
    ax.set_ylabel("Brightness of a point (ideal peak = 1)")
    ax.set_title("Slow bends: a point spreads out", fontsize=10)
    ax.legend(frameon=False, fontsize=8)
    tidy(ax)
    fig.tight_layout()
    save(fig, "phase-tolerance")


# --------------------------------------------------------------------------
# 5. Sampling with many receivers: blind speeds and the jitter cure
# --------------------------------------------------------------------------
def noise_penalty(offsets, q):
    """Noise growth when q fine samples per pixel are rebuilt from the offsets."""
    k = np.arange(q) - q // 2
    a = np.exp(2j * np.pi * np.outer(offsets, k))
    s = np.linalg.svd(a, compute_uv=False)
    if s[-1] < 1e-9 * s[0]:
        return np.inf
    return np.sqrt(len(offsets) * np.mean(1.0 / s ** 2))


def fig_blind_speeds():
    rng = np.random.default_rng(5)
    q, frames = 8, 64
    steps = np.linspace(0.02, 3.0, 2981)
    regular = np.array([noise_penalty((np.arange(frames) * s) % 1.0, q) for s in steps])
    jit = []
    for s in steps:
        vals = [noise_penalty((np.arange(frames) * s + rng.normal(scale=0.2, size=frames)) % 1.0, q)
                for _ in range(8)]
        jit.append(np.median(vals))
    jit = np.array(jit)
    print("multi-receiver sampling (8 fine samples per pixel from 64 frames):")
    print(f"  regular steps: share of speeds with penalty > 2: "
          f"{np.mean(~(regular < 2)) * 100:.1f} %")
    print(f"  jittered 0.2 px: median penalty {np.median(jit):.2f}, worst {jit.max():.2f}")
    for s in (1.0, 0.5, 1.25, 1.37):
        print(f"  step {s:.3f} px: regular {noise_penalty((np.arange(frames) * s) % 1.0, q):.2f}")

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.2), gridspec_kw={"width_ratios": [1.0, 1.9]})
    ax = axes[0]
    for row, (s, lab) in enumerate(((1.37, "1.37 pixels per frame"),
                                    (1.25, "1.25 pixels per frame"),
                                    (1.00, "1.00 pixel per frame"))):
        off = (np.arange(16) * s) % 1.0
        ax.plot(off, np.full_like(off, row), "o", color=BLUE, ms=6, alpha=0.6)
        ax.text(0.0, row + 0.22, lab, fontsize=8.5, color=INK)
    off = (np.arange(16) * 1.0 + rng.normal(scale=0.2, size=16)) % 1.0
    ax.plot(off, np.full_like(off, -1), "o", color=ORANGE, ms=6, alpha=0.6)
    ax.text(0.0, -1 + 0.22, "1.00 pixel per frame, with 0.2 pixel jitter", fontsize=8.5)
    ax.set_xlim(-0.03, 1.03)
    ax.set_ylim(-1.5, 2.7)
    ax.set_yticks([])
    ax.set_xlabel("Where 16 frames sample inside one pixel width")
    ax.set_title("Sample positions", fontsize=10)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax = axes[1]
    shown = np.where(np.isfinite(regular), regular, 1e3)
    ax.plot(steps, shown, color=BLUE, lw=0.9, label="steady speed")
    ax.plot(steps, jit, color=ORANGE, lw=1.2, label="same speed with 0.2 pixel random jitter")
    ax.set_yscale("log")
    ax.set_ylim(0.9, 300)
    ax.set_xlim(0, 3)
    ax.set_xlabel("Movement between frames (pixels)")
    ax.set_ylabel("Noise growth in the fine picture (1 = ideal)")
    ax.set_title("Noise cost of rebuilding 8 fine samples per pixel from 64 frames", fontsize=10)
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    tidy(ax)
    fig.tight_layout()
    save(fig, "blind-speeds")


# --------------------------------------------------------------------------
# 6. Depth from colour steps: radar's stepped frequency, at light wavelengths
# --------------------------------------------------------------------------
def fig_depth_from_colour():
    c_um_thz = 299.792458  # speed of light in um * THz
    n_oxide = 1.46
    z = np.linspace(-4, 4, 4001)  # depth in oxide, um
    lines = np.array([405.0, 450.0, 520.0, 638.0])
    sweep = 1.0 / np.linspace(1 / 638.0, 1 / 405.0, 241)
    dense = 1.0 / np.linspace(1 / 638.0, 1 / 405.0, 16)

    def response(wl_nm, window=False):
        k = 2 * np.pi / (wl_nm * 1e-3)
        w = np.hanning(len(k) + 2)[1:-1] if window else np.ones(len(k))
        r = np.abs((w[None, :] * np.exp(2j * n_oxide * np.outer(z, k))).sum(axis=1))
        return r / r.max()

    band_thz = c_um_thz * (1 / 0.405 - 1 / 0.638)
    res_air = c_um_thz / (2 * band_thz)
    print("depth from colour steps:")
    print(f"  band 405 to 638 nm = {band_thz:.0f} THz")
    print(f"  depth resolution c/2B = {res_air:.2f} um in air, {res_air / n_oxide:.2f} um in oxide")
    step_thz = band_thz / 15
    print(f"  16 even steps: unambiguous depth {c_um_thz / (2 * step_thz) / n_oxide:.1f} um in oxide")
    r_sweep = response(sweep)
    half = z[r_sweep >= 0.5]
    print(f"  full sweep response width at half height {np.ptp(half):.2f} um in oxide")

    fig, axes = plt.subplots(1, 3, figsize=(12.0, 3.8), sharey=True)
    for ax, wl, title in ((axes[0], lines, "4 laser diodes\n405, 450, 520, 638 nm"),
                          (axes[1], dense, "16 evenly spaced colours\n405 to 638 nm"),
                          (axes[2], sweep, "Continuous sweep or white light\n405 to 638 nm")):
        ax.plot(z, response(wl), color=BLUE, lw=1.3)
        ax.set_title(title, fontsize=9.5)
        ax.set_xlabel("Depth below the reference surface, in oxide (µm)")
        ax.set_xlim(-4, 4)
        tidy(ax)
    axes[0].set_ylabel("Response to one reflecting layer at depth 0")
    fig.tight_layout()
    save(fig, "depth-from-colour")


# --------------------------------------------------------------------------
# 7. Which surface detail is covered: fixed beams against a turning chip
# --------------------------------------------------------------------------
def fig_rotation_coverage():
    s = np.sin(np.deg2rad(SLANT_DEG))
    n = 601
    f = np.linspace(-2.2, 2.2, n)
    fx, fy = np.meshgrid(f, f)

    def cover(azimuths):
        m = np.zeros_like(fx, dtype=bool)
        for a in azimuths:
            m |= (fx - s * np.cos(a)) ** 2 + (fy - s * np.sin(a)) ** 2 <= 1.0
        return m

    cases = [("Light straight down", np.hypot(fx, fy) <= 1.0),
             ("2 slanted beams along one axis", cover([0, np.pi])),
             ("4 slanted beams along both axes", cover(np.arange(4) * np.pi / 2)),
             ("Chip turned through a full circle\nunder 1 slanted beam",
              cover(np.linspace(0, 2 * np.pi, 361)))]
    fig, axes = plt.subplots(1, 4, figsize=(13.0, 3.9))
    print(f"surface detail covered (units of 1/wavelength, beams at {SLANT_DEG:.0f} deg):")
    for ax, (title, m) in zip(axes, cases):
        ax.imshow(m, extent=[f[0], f[-1], f[0], f[-1]], origin="lower",
                  cmap=matplotlib.colors.ListedColormap([SURFACE, "#a9c8ee"]))
        ax.add_patch(Circle((0, 0), 2.0, fill=False, ec=INK2, lw=0.9, ls="--"))
        target = WAVELENGTH_NM / 200.0
        ax.add_patch(Circle((0, 0), target, fill=False, ec=ORANGE, lw=1.3))
        ax.set_title(title, fontsize=9.5)
        ax.set_xlabel("Detail along x (1/wavelength)")
        ax.set_xticks([-2, -1, 0, 1, 2])
        ax.set_yticks([-2, -1, 0, 1, 2])
        reach = []
        for ang in (0.0, 45.0):
            t = np.deg2rad(ang)
            r = np.linspace(0, 2.2, 2201)
            inside = np.interp(r * np.cos(t), f, np.arange(n)), np.interp(r * np.sin(t), f, np.arange(n))
            vals = m[np.round(inside[1]).astype(int), np.round(inside[0]).astype(int)]
            edge = r[vals][-1] if vals.any() else 0.0
            reach.append(edge)
        print(f"  {title.splitlines()[0]:36s} along a wire axis: period {WAVELENGTH_NM / reach[0]:5.0f} nm"
              f"   at 45 deg: period {WAVELENGTH_NM / reach[1]:5.0f} nm")
    axes[0].set_ylabel("Detail along y (1/wavelength)")
    fig.text(0.5, 0.0, "Blue: surface detail that reaches the sensor.   Dashed circle: limit for any "
             "method that works across a gap.   Orange circle: 100 nm lines and spaces.",
             ha="center", va="top", fontsize=9, color=INK2)
    fig.tight_layout()
    save(fig, "rotation-coverage")


if __name__ == "__main__":
    fig_modes()
    fig_autofocus()
    fig_gap_autofocus()
    fig_phase_tolerance()
    fig_blind_speeds()
    fig_depth_from_colour()
    fig_rotation_coverage()
