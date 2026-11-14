"""Generate the diagrams and numbers for docs/research/beamforming.md.

Run from the repository root:

    python docs/diagrams/make_beamforming_diagrams.py

Writes SVG (used by the document) and PNG copies next to this file, all with
the prefix ``beam-``, and prints every derived number quoted on the page.

Everything here is a formula or a small toy calculation, not a result from
the simulator. Each function says what it leaves out. Random numbers use
fixed seeds, so the figures and the printed numbers are reproducible.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, Rectangle
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import lsqr

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
        "svg.hashsalt": "beam",
    }
)

# Baseline instrument numbers, from docs/design.md section 5.1.
WAVELENGTH_UM = 0.405
PITCH_UM = 1.12
SENSOR_PIXELS = (3280, 2464)
SENSOR_MM = (3.68, 2.76)
FULL_WELL_E = 4500.0
READ_NOISE_E = 3.0


def save(fig, name):
    fig.savefig(OUT / f"beam-{name}.svg", bbox_inches="tight",
                metadata={"Date": None})
    fig.savefig(OUT / f"beam-{name}.png", bbox_inches="tight", dpi=160)
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


# ---------------------------------------------------------------------------
# 1. What each kind of receiver records (illustrative)
# ---------------------------------------------------------------------------

def receiver_map():
    """Three receivers side by side. Illustrative, not to scale."""
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 4.3))
    titles = [
        "Antenna or microphone:\nrecords the wave itself",
        "Bare pixel:\nrecords brightness only",
        "Pixel plus a reference beam (dashed):\nbrightness now depends on timing",
    ]
    t = np.linspace(0, 1, 400)
    for ax, title in zip(axes, titles):
        blank(ax, (0, 10), (-1.2, 8.4))
        ax.set_title(title, fontsize=10.5, color=INK)

    # Panel 1: a wave arriving at two receivers, traces show delay.
    ax = axes[0]
    for x in (3.0, 7.0):
        ax.add_patch(Rectangle((x - 0.5, 4.3), 1.0, 0.5, color=INK2))
    for k in range(5):
        ax.plot([1.2 + k * 0.3, 8.2 + k * 0.3], [7.9 - k * 0.45, 6.5 - k * 0.45],
                color=BLUE, lw=1.2)
    arrow(ax, (8.9, 7.7), (8.2, 6.1), color=BLUE)
    ax.text(9.0, 7.85, "wave", color=BLUE, fontsize=9, ha="center")
    for x, phase, col in ((3.0, 0.0, ORANGE), (7.0, 1.6, AQUA)):
        ax.plot(x - 1.6 + 3.2 * t, 2.6 + 0.8 * np.sin(2 * np.pi * 3 * t - phase),
                color=col, lw=1.4)
        ax.plot([x, x], [4.3, 3.6], color=INK2, lw=1)
    ax.text(5.0, 0.0, "Two signals with a measurable delay.\n"
            "The delay gives the direction.", ha="center", fontsize=9, color=INK2)

    # Panel 2: same wave onto pixels: constant brightness.
    ax = axes[1]
    for x in (3.0, 7.0):
        ax.add_patch(Rectangle((x - 0.5, 4.3), 1.0, 0.5, color=SILICON, ec=INK2))
    for k in range(5):
        ax.plot([1.2 + k * 0.3, 8.2 + k * 0.3], [7.9 - k * 0.45, 6.5 - k * 0.45],
                color=BLUE, lw=1.2)
    for x, col in ((3.0, ORANGE), (7.0, AQUA)):
        ax.plot([x - 1.6, x + 1.6], [2.9, 2.9], color=col, lw=1.6)
        ax.plot([x, x], [4.3, 3.6], color=INK2, lw=1)
    ax.text(5.0, 0.0, "Two equal, steady readings.\n"
            "The delay, and so the direction, is lost.", ha="center", fontsize=9,
            color=INK2)

    # Panel 3: wave plus reference: fringes across the pixels.
    ax = axes[2]
    xs = np.linspace(1.4, 8.6, 7)
    for x in xs:
        ax.add_patch(Rectangle((x - 0.4, 4.3), 0.8, 0.5, color=SILICON, ec=INK2))
    for k in range(5):
        ax.plot([1.2 + k * 0.3, 8.2 + k * 0.3], [7.9 - k * 0.45, 6.5 - k * 0.45],
                color=BLUE, lw=1.2)
    for k in range(4):
        ax.plot([1.0, 9.0], [6.2 - k * 0.4, 6.2 - k * 0.4], color=VIOLET, lw=1.0,
                ls=(0, (4, 2)))
    level = 2.9 + 0.75 * np.cos(2 * np.pi * (xs - 1.4) / 4.8)
    ax.bar(xs, level - 1.9, width=0.7, bottom=1.9, color=YELLOW, edgecolor=INK2,
           linewidth=0.6)
    ax.text(5.0, 0.0, "Readings rise and fall across the row (fringes).\n"
            "Their spacing gives the direction, their position the timing.",
            ha="center", fontsize=9, color=INK2)
    save(fig, "receiver-map")


# ---------------------------------------------------------------------------
# 2. Array response of the pixel grid
# ---------------------------------------------------------------------------

def _array_factor(u, u0, pitch, n, wavelength):
    x = np.pi * pitch * (u - u0) / wavelength
    num = np.sin(n * x)
    den = n * np.sin(x)
    out = np.ones_like(x)
    ok = np.abs(den) > 1e-12
    out[ok] = num[ok] / den[ok]
    return np.abs(out)


def array_factor(steer_u=0.25, n=64, fill=8):
    """Response of a row of pixels, used as an array, against arrival angle.

    Scalar plane waves, ideal rectangular pixels as wide as the pitch. Leaves
    out the true angular response of a pixel, which is not known (design 4.9).
    """
    u = np.linspace(-1, 1, 20001)
    elem = np.abs(np.sinc(PITCH_UM * u / WAVELENGTH_UM))
    af1 = _array_factor(u, steer_u, PITCH_UM, n, WAVELENGTH_UM)
    af2 = _array_factor(u, steer_u, PITCH_UM / fill, n * fill, WAVELENGTH_UM)

    fig, axes = plt.subplots(2, 1, figsize=(9.5, 6.2), sharex=True)
    for ax, af, title in (
        (axes[0], af1, f"One frame: {n} pixels at {PITCH_UM} µm spacing"),
        (axes[1], af2, f"Scan fills in {fill} positions per pixel: spacing "
                       f"{1000 * PITCH_UM / fill:.0f} nm"),
    ):
        ax.plot(u, 20 * np.log10(np.maximum(af, 1e-4)), color=BLUE, lw=1.0,
                label="array of point receivers")
        ax.plot(u, 20 * np.log10(np.maximum(elem, 1e-4)), color=ORANGE, lw=1.3,
                ls=(0, (5, 2)), label="one pixel alone")
        ax.axvline(steer_u, color=INK2, lw=0.8, ls=":")
        ax.set_ylim(-45, 3)
        ax.set_ylabel("response (dB)")
        ax.set_title(title, fontsize=10.5, loc="left")
        tidy(ax)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, fontsize=9,
               frameon=False, bbox_to_anchor=(0.5, -0.04))
    axes[1].text(steer_u + 0.02, -6, "steered here", fontsize=8.5, color=INK2,
                 bbox=dict(facecolor=SURFACE, edgecolor="none", pad=1.5))
    axes[1].set_xlabel("sine of the arrival angle (0 = straight down, 1 = grazing)")
    sec = axes[0].secondary_xaxis("top", functions=(
        lambda s: np.degrees(np.arcsin(np.clip(s, -1, 1))),
        lambda d: np.sin(np.radians(d))))
    sec.set_xticks([-60, -30, -15, 0, 15, 30, 60])
    sec.set_xlabel("arrival angle (degrees)")
    save(fig, "array-factor")

    lobe = WAVELENGTH_UM / PITCH_UM
    print("ARRAY RESPONSE")
    print(f"  grating lobe spacing in sine of angle: {lobe:.3f} "
          f"({np.degrees(np.arcsin(lobe)):.1f} degrees from straight down)")
    print(f"  lobes inside +-90 degrees when steered to 0: "
          f"{2 * int(np.floor(1 / lobe)) + 1}")
    print(f"  spacing needed for no ambiguity (half wavelength): "
          f"{1000 * WAVELENGTH_UM / 2:.1f} nm = pitch / "
          f"{PITCH_UM / (WAVELENGTH_UM / 2):.2f}")
    print(f"  first zero of one ideal pixel: sine {lobe:.3f}")
    for deg in (10, 20, 30, 45, 60, 72):
        s = np.sin(np.radians(deg))
        print(f"  ideal pixel response at {deg:2d} degrees: "
              f"{abs(np.sinc(PITCH_UM * s / WAVELENGTH_UM)):.3f}")


# ---------------------------------------------------------------------------
# 3. Beam directions as a sparse array: the difference co-array
# ---------------------------------------------------------------------------

def _bands(beams, half_band):
    """Object-frequency bands (in units of 1/wavelength) reached by beam pairs."""
    beams = np.asarray(beams, float)
    diffs = sorted({round(abs(a - b), 6) for a in beams for b in beams})
    return [(d - half_band, d + half_band) for d in diffs], diffs


def _covered(bands, top):
    grid = np.linspace(0, top, 20001)
    hit = np.zeros_like(grid, bool)
    for lo, hi in bands:
        hit |= (grid >= lo) & (grid <= hi)
    return hit.mean()


def coarray(max_sine=0.95):
    """Which surface detail each set of beam directions can mix down.

    One dimension, thin weakly scattering surface, every beam's mirror
    reflection reaching every pixel. Half-band is how fine a fringe the pixel
    grid can still record, as a fraction of 1/wavelength. Leaves out the
    strength of each term and the unwanted object-object terms.
    """
    unit3 = 2 * max_sine / 3
    unit6 = 2 * max_sine / 6
    sets = [
        ("2 beams, opposite", [-max_sine, max_sine]),
        ("3 beams, no repeated spacing", [-max_sine, -max_sine + unit3, max_sine]),
        ("4 beams, evenly spaced", list(np.linspace(-max_sine, max_sine, 4))),
        ("4 beams, no repeated spacing",
         [-max_sine + unit6 * k for k in (0, 1, 4, 6)]),
    ]
    half_bands = [
        ("pixel records fringes down to one pixel wide", WAVELENGTH_UM / PITCH_UM),
        ("pixel records fringes down to two pixels wide",
         WAVELENGTH_UM / (2 * PITCH_UM)),
    ]
    top = 2 * max_sine

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4), sharey=True)
    print("BEAM DIRECTIONS AS A SPARSE ARRAY (difference co-array)")
    for ax, (label, hb) in zip(axes, half_bands):
        print(f"  half-band {hb:.3f} / wavelength ({label})")
        for row, (name, beams) in enumerate(sets):
            bands, diffs = _bands(beams, hb)
            y = len(sets) - 1 - row
            for lo, hi in bands:
                ax.add_patch(Rectangle((max(lo, 0), y - 0.28),
                                       min(hi, 2.4) - max(lo, 0), 0.56,
                                       color=BLUE, alpha=0.45, lw=0))
            for d in diffs:
                ax.plot([d, d], [y - 0.28, y + 0.28], color=INK, lw=1.0)
            frac = _covered(bands, top)
            n = len(beams)
            pairs = n * (n - 1) // 2
            distinct = len([d for d in diffs if d > 0])
            print(f"    {name:32s} sines {np.round(beams, 3)} pairs {pairs} "
                  f"distinct spacings {distinct} covered {100 * frac:5.1f} %")
        ax.axvline(top, color=ORANGE, lw=1.2, ls=(0, (5, 2)))
        ax.text(top - 0.02, len(sets) - 0.45, "steepest\nbeam pair", color=ORANGE,
                fontsize=8.5, ha="right", va="top")
        ax.set_xlim(0, 2.4)
        ax.set_ylim(-0.6, len(sets) - 0.2)
        ax.set_yticks(range(len(sets)))
        ax.set_yticklabels([s[0] for s in sets][::-1])
        ax.set_xlabel("fineness of surface detail (ripples per wavelength)")
        ax.set_title(label, fontsize=10, loc="left")
        tidy(ax)
        sec = ax.secondary_xaxis("top", functions=(
            lambda f: 1000 * WAVELENGTH_UM / (2 * np.maximum(f, 1e-6)),
            lambda w: 1000 * WAVELENGTH_UM / (2 * np.maximum(w, 1e-6))))
        sec.set_xticks([400, 200, 150, 125, 107])
        sec.set_xlabel("line width (nm) at 405 nm")
    save(fig, "coarray")

    # Rough two-dimensional count: patches of side 2*half_band tiling half a
    # disc of radius `top` (the other half is its mirror image).
    for label, hb in half_bands:
        area = 0.5 * np.pi * top ** 2
        patches = area / (2 * hb) ** 2
        n = int(np.ceil((1 + np.sqrt(1 + 8 * patches)) / 2))
        print(f"  2-D estimate, {label}: {patches:.0f} patches, "
              f"at least {n} beams if no spacing repeats")


# ---------------------------------------------------------------------------
# 4. Adaptive and subspace methods on a toy array
# ---------------------------------------------------------------------------

def _spectra(R, m, grid, n_src=2):
    A = np.exp(2j * np.pi * np.outer(np.arange(m), grid))
    das = np.real(np.einsum("ij,ik,kj->j", A.conj(), R, A)) / m ** 2
    Ri = np.linalg.inv(R + 1e-6 * np.trace(R).real / m * np.eye(m))
    capon = 1.0 / np.real(np.einsum("ij,ik,kj->j", A.conj(), Ri, A))
    w, v = np.linalg.eigh(R)
    En = v[:, : m - n_src]
    music = 1.0 / np.sum(np.abs(En.conj().T @ A) ** 2, axis=0)
    return das, capon, music


def _smooth(X, sub):
    """Forward-backward spatial smoothing of snapshots X (elements x shots)."""
    m = X.shape[0]
    J = np.eye(sub)[::-1]
    R = np.zeros((sub, sub), complex)
    count = 0
    for s in range(m - sub + 1):
        Xs = X[s: s + sub]
        Rs = Xs @ Xs.conj().T / X.shape[1]
        R += Rs + J @ Rs.conj() @ J
        count += 2
    return R / count


def _dip_db(y, grid, src):
    """Depth of the dip between the two sources, in dB below the lower of
    the map values at the two true positions. Positive means separated."""
    at = [y[np.argmin(np.abs(grid - x))] for x in src]
    mid = y[np.argmin(np.abs(grid - np.mean(src)))]
    return 10 * np.log10(min(at) / mid)


def adaptive_demo(m=32, shots=200, sep=0.4, snr_db=20.0, seed=7):
    """Two point scatterers closer than the array's ordinary limit.

    The array records the wave itself (pixels with a reference beam), 32
    samples in a row, one dimension, far field. Left: each shot lights the
    two scatterers with an unrelated phase (independent shots). Right: every
    shot has the same phase relation (one fixed laser beam). Leaves out
    model error, which is what limits these methods in practice.
    """
    rng = np.random.default_rng(seed)
    rayleigh = 1.0 / m
    src = np.array([-0.5, 0.5]) * sep * rayleigh
    A = np.exp(2j * np.pi * np.outer(np.arange(m), src))
    sigma = 10 ** (-snr_db / 20)
    noise = sigma * (rng.normal(size=(m, shots)) + 1j * rng.normal(size=(m, shots))) / np.sqrt(2)
    s_inc = (rng.normal(size=(2, shots)) + 1j * rng.normal(size=(2, shots))) / np.sqrt(2)
    common = (rng.normal(size=shots) + 1j * rng.normal(size=shots)) / np.sqrt(2)
    s_coh = np.vstack([common, common * np.exp(1j * np.radians(70))])
    grid = np.linspace(-2.5 * rayleigh, 2.5 * rayleigh, 1201)

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.3), sharey=True)
    print("ADAPTIVE METHODS, TOY ARRAY")
    print(f"  {m} samples, {shots} shots, separation {sep} of the ordinary "
          f"limit, signal-to-noise {snr_db:.0f} dB per sample per shot")
    cases = (
        ("Independent shots", s_inc, False),
        ("Every shot alike (one fixed beam)", s_coh, True),
    )
    for ax, (title, s, coherent) in zip(axes, cases):
        X = A @ s + noise
        R = X @ X.conj().T / shots
        das, capon, music = _spectra(R, m, grid)
        curves = [("delay and sum", das, INK2, "-"),
                  ("minimum variance (Capon)", capon, BLUE, "-"),
                  ("subspace (MUSIC)", music, ORANGE, "-")]
        if coherent:
            sub = 20
            Rs = _smooth(X, sub)
            _, _, music_s = _spectra(Rs, sub, grid)
            curves.append(("MUSIC after spatial smoothing", music_s, AQUA, "-"))
        for name, y, col, ls in curves:
            ydb = 10 * np.log10(y / y.max())
            ax.plot(grid / rayleigh, ydb, color=col, lw=1.5, ls=ls, label=name)
            dip = _dip_db(y, grid, src)
            print(f"  {title:34s} {name:30s} dip between the two: "
                  f"{dip:5.1f} dB ({'separated' if dip > 3 else 'not separated'})")
        for x in src / rayleigh:
            ax.axvline(x, color=INK, lw=0.8, ls=":")
        ax.set_ylim(-40, 2)
        ax.set_xlabel("position (units of the array's ordinary resolution limit)")
        ax.set_title(title, fontsize=10.5, loc="left")
        tidy(ax)
    handles, labels = axes[1].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, fontsize=9,
               frameon=False, bbox_to_anchor=(0.5, -0.06))
    axes[0].set_ylabel("map value relative to its peak (dB)")
    save(fig, "adaptive-demo")


# ---------------------------------------------------------------------------
# 5. Self-calibration of pixel gains from the scan
# ---------------------------------------------------------------------------

def _scan(name, rows, cols, frames):
    """Sensor positions (whole pixels) for a named toy scan pattern."""
    k = np.arange(frames)
    if name == "one straight pass":
        return [(int(i), 0) for i in k]
    if name == "two passes, shifted sideways by 5":
        return [(int(i), 0) for i in k] + [(int(i), 5) for i in k]
    if name == "three passes, shifted by 0, 5 and 8":
        return ([(int(i), 0) for i in k] + [(int(i), 5) for i in k]
                + [(int(i), 8) for i in k])
    if name == "one pass along, one pass across":
        return [(int(i), 0) for i in k] + [(0, int(i)) for i in k]
    raise ValueError(name)


def _design(positions, rows, cols, with_exposure):
    """Sparse matrix of the log model: log reading = gain + scene + exposure."""
    py = max(p[0] for p in positions) + rows
    px = max(p[1] for p in positions) + cols
    n_gain = rows * cols
    n_scene = py * px
    r_idx, c_idx = [], []
    rr, cc = np.meshgrid(np.arange(rows), np.arange(cols), indexing="ij")
    rr, cc = rr.ravel(), cc.ravel()
    row0 = 0
    for f, (dy, dx) in enumerate(positions):
        n = rr.size
        rows_here = row0 + np.arange(n)
        r_idx += [rows_here, rows_here]
        c_idx += [rr * cols + cc, n_gain + (rr + dy) * px + (cc + dx)]
        if with_exposure:
            r_idx.append(rows_here)
            c_idx.append(np.full(n, n_gain + n_scene + f))
        row0 += n
    r_idx = np.concatenate(r_idx)
    c_idx = np.concatenate(c_idx)
    n_par = n_gain + n_scene + (len(positions) if with_exposure else 0)
    used = np.unique(c_idx)
    remap = -np.ones(n_par, int)
    remap[used] = np.arange(used.size)
    Amat = coo_matrix((np.ones(r_idx.size), (r_idx, remap[c_idx])),
                      shape=(row0, used.size)).tocsr()
    return Amat, n_gain, (py, px), remap


def _null_dim(Amat):
    s = np.linalg.svd(Amat.toarray(), compute_uv=False)
    rank = int((s > 1e-8 * s[0]).sum())
    return Amat.shape[1] - rank


def _solve_gains(name, rows, cols, frames, rng, gain_sd=0.02, mean_e=2000.0,
                 exposure_sd=0.02, with_exposure=True):
    positions = _scan(name, rows, cols, frames)
    Amat, n_gain, (py, px), remap = _design(positions, rows, cols, with_exposure)
    gain = 1 + gain_sd * rng.normal(size=(rows, cols))
    scene = mean_e * rng.uniform(0.4, 1.6, size=(py, px))
    y = []
    for dy, dx in positions:
        e = 1 + exposure_sd * rng.normal() if with_exposure else 1.0
        clean = e * gain * scene[dy: dy + rows, dx: dx + cols]
        y.append(rng.poisson(clean).ravel())
    logy = np.log(np.maximum(np.concatenate(y), 1.0))
    sol = lsqr(Amat, logy, atol=1e-12, btol=1e-12, iter_lim=20000)[0]
    est = np.exp(sol[:n_gain]).reshape(rows, cols)
    return gain, est


def _gauge_error(gain, est, remove_plane):
    """Fractional gain error after removing what no method could know."""
    err = np.log(est) - np.log(gain)
    rows, cols = gain.shape
    rr, cc = np.meshgrid(np.arange(rows), np.arange(cols), indexing="ij")
    basis = [np.ones(err.size)]
    if remove_plane:
        basis += [rr.ravel().astype(float), cc.ravel().astype(float)]
    B = np.stack(basis, axis=1)
    coef = np.linalg.lstsq(B, err.ravel(), rcond=None)[0]
    return (err.ravel() - B @ coef).reshape(rows, cols)


def selfcal_demo(rows=12, cols=12, seed=11):
    """Pixel gains solved from the scan alone, on a 12 by 12 toy sensor.

    Whole-pixel steps, unknown random scene, unknown gain per pixel (2 per
    cent spread), unknown brightness per frame (2 per cent spread), photon
    noise at 2000 electrons per reading. Log-linear least squares. Leaves out
    blur, sub-pixel steps, offsets and read noise.
    """
    names = [
        "one straight pass",
        "two passes, shifted sideways by 5",
        "three passes, shifted by 0, 5 and 8",
        "one pass along, one pass across",
    ]
    print("SELF-CALIBRATION OF PIXEL GAINS, TOY SENSOR")
    print(f"  {rows} x {cols} pixels. Combinations the data cannot fix:")
    null = {}
    for name in names:
        row = []
        for with_exp in (False, True):
            Amat, *_ = _design(_scan(name, rows, cols, 16), rows, cols, with_exp)
            row.append(_null_dim(Amat))
        null[name] = row
        print(f"    {name:38s} frame brightness known: {row[0]:3d}   "
              f"unknown: {row[1]:3d}")

    rng = np.random.default_rng(seed)
    gain, est_bad = _solve_gains(names[0], rows, cols, 32, rng)
    err_bad = _gauge_error(gain, est_bad, remove_plane=True)
    gain2, est_good = _solve_gains(names[3], rows, cols, 32, rng)
    err_good = _gauge_error(gain2, est_good, remove_plane=True)
    print(f"  32 frames per pass. Gain error (r.m.s., per cent): "
          f"one straight pass {100 * err_bad.std():.2f}, "
          f"along and across {100 * err_good.std():.2f}")

    frames_list = [4, 8, 16, 32, 64, 128]
    curve = []
    for frames in frames_list:
        vals = []
        for rep in range(4):
            g, e = _solve_gains(names[3], rows, cols, frames,
                                np.random.default_rng(100 + 10 * frames + rep))
            vals.append(_gauge_error(g, e, True).std())
        curve.append(100 * float(np.mean(vals)))
    shot = [100 / np.sqrt(2000.0 * 2 * f) for f in frames_list]
    print("  frames per pass, gain error %, photon-noise floor % "
          "(1/sqrt(electrons collected by the pixel)):")
    for f, c, s in zip(frames_list, curve, shot):
        print(f"    {f:4d}  {c:.3f}  {s:.3f}")

    fig = plt.figure(figsize=(12.5, 4.2))
    gs = fig.add_gridspec(1, 5, width_ratios=[1, 1, 0.06, 0.42, 1.7], wspace=0.3)
    vmax = 4.0
    for i, (err, title) in enumerate((
        (err_bad, "One straight pass:\nerror left in the gains"),
        (err_good, "One pass along, one across:\nerror left in the gains"),
    )):
        ax = fig.add_subplot(gs[0, i])
        im = ax.imshow(100 * err, cmap="RdBu_r", vmin=-vmax, vmax=vmax)
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("pixel column")
        if i == 0:
            ax.set_ylabel("pixel row (scan direction)")
    cax = fig.add_subplot(gs[0, 2])
    fig.colorbar(im, cax=cax, label="gain error (per cent)")
    ax = fig.add_subplot(gs[0, 4])
    ax.loglog(frames_list, curve, "o-", color=BLUE, lw=1.6,
              label="toy solve, along and across")
    ax.loglog(frames_list, shot, color=ORANGE, lw=1.3, ls=(0, (5, 2)),
              label="photon-noise floor of one pixel")
    ax.axhline(2.0, color=INK2, lw=0.9, ls=":")
    ax.text(frames_list[0], 2.15, "spread of the true gains", fontsize=8.5,
            color=INK2)
    ax.set_xlabel("frames in each pass")
    ax.set_ylabel("gain error, r.m.s. (per cent)")
    ax.set_xticks(frames_list)
    ax.set_xticklabels([str(f) for f in frames_list])
    ax.set_ylim(0.1, 4)
    ax.set_yticks([0.1, 0.2, 0.5, 1, 2, 4])
    ax.set_yticklabels(["0.1", "0.2", "0.5", "1", "2", "4"])
    ax.minorticks_off()
    ax.legend(fontsize=8.5, frameon=False, loc="lower left")
    tidy(ax)
    save(fig, "selfcal-demo")

    print("  photon-noise floor of a pixel gain on the real sensor "
          "(per cent), readings x electrons each:")
    for n_read, e_each in ((100, 2000), (1000, 2000), (10000, 2000), (10000, 4000)):
        print(f"    {n_read:6d} x {e_each}: {100 / np.sqrt(n_read * e_each):.4f}")
    return null


# ---------------------------------------------------------------------------
# 6. Tables of derived numbers
# ---------------------------------------------------------------------------

def counting_tables():
    px = SENSOR_PIXELS[0] * SENSOR_PIXELS[1]
    area_um2 = SENSOR_MM[0] * SENSOR_MM[1] * 1e6
    step = WAVELENGTH_UM / 4
    unknowns = area_um2 / step ** 2
    per_pixel = (PITCH_UM / step) ** 2
    print("COUNTING: NUMBERS WANTED AGAINST NUMBERS RECORDED")
    print(f"  pixels per frame: {px:,}")
    print(f"  finest period that travels: {1000 * WAVELENGTH_UM / 2:.1f} nm, "
          f"sample spacing {1000 * step:.2f} nm")
    print(f"  surface samples under the sensor: {unknowns:.3g}")
    print(f"  surface samples per pixel area: {per_pixel:.0f} "
          f"(twice that, {2 * per_pixel:.0f}, if brightness and height are both wanted)")
    print(f"  frames needed at the very least: {unknowns / px:.0f}")

    print("AVERAGING GAIN")
    for n in (100, 1000, 13000, 100000):
        print(f"  {n:7d} readings: noise falls by {np.sqrt(n):7.1f} "
              f"({10 * np.log10(n):.0f} dB)")

    print("REFERENCE BEAM (HETERODYNE) GAIN, per pixel per frame")
    print("  scattered electrons | direct SNR with 3 e read noise | "
          "SNR with reference filling the well")
    for ns in (0.1, 1.0, 10.0, 100.0):
        direct = ns / np.sqrt(ns + READ_NOISE_E ** 2)
        het = 2 * np.sqrt(ns * FULL_WELL_E) / np.sqrt(FULL_WELL_E + ns + READ_NOISE_E ** 2)
        print(f"  {ns:6.1f}  {direct:6.3f}  {het:6.3f}")
    print(f"  weakest scattered share of the reference seen at SNR 1 in one "
          f"reading: {1 / (4 * FULL_WELL_E):.2e}")
    for n in (1e3, 1e6):
        print(f"    after combining {n:.0e} readings: "
              f"{1 / (4 * FULL_WELL_E * n):.1e}")

    print("SIZE OF THE CORRELATION MATRIX")
    for side in (16, 32, 64, None):
        m = side * side if side else px
        entries = float(m) ** 2
        gb = entries * 8 / 1e9
        tiles = px / m
        print(f"  tile {side if side else 'whole sensor'}: receivers {m:,}, "
              f"entries {entries:.3g}, memory {gb:.3g} GB, tiles {tiles:,.0f}")

    print("RADIO SELF-CALIBRATION COUNTS (pairs = n(n-1)/2)")
    for n in (27, 64, 350):
        print(f"  {n} antennas: {n * (n - 1) // 2} pairs, {n} gains, "
              f"ratio {(n - 1) / 2:.1f}")


def crowding_table():
    """Scaling of the noise cost of separating crowded points [BF28].

    The law is error ~ SRF**(2p - 1) x noise, where SRF is how many times
    finer than the ordinary limit the points sit and p is how many points
    crowd together. This prints the scale factors, not exact errors.
    """
    print("NOISE COST OF SEPARATING CROWDED POINTS, scale factor SRF^(2p-1)")
    for srf in (1.5, 2.0, 3.0, 4.0):
        row = [srf ** (2 * p - 1) for p in (1, 2, 3)]
        print(f"  {srf:3.1f} times finer: 1 point {row[0]:6.1f}, "
              f"2 points {row[1]:7.1f}, 3 points {row[2]:8.1f}")


def nearfield_table():
    """Fading of detail finer than the wavelength, with slanted light."""
    k0 = 2 * np.pi / WAVELENGTH_UM
    print("NEAR FIELD: GAP AT WHICH DETAIL HAS FADED BY A GIVEN AMOUNT")
    print("  line width nm | light angle deg | fade per 100 nm (dB) | "
          "gap for 20 dB (nm) | 40 dB | 60 dB")
    for width in (100, 80, 60, 40):
        k_obj = np.pi / (width / 1000.0)
        for deg in (0, 72):
            kt = k_obj - k0 * np.sin(np.radians(deg))
            if kt <= k0:
                print(f"  {width:4d} {deg:3d}  travels (does not fade)")
                continue
            kz = np.sqrt(kt ** 2 - k0 ** 2)
            per100 = 20 * np.log10(np.e) * kz * 0.1
            gaps = [1000 * d * np.log(10) / (20 * kz) for d in (20, 40, 60)]
            print(f"  {width:4d} {deg:3d}  {per100:6.1f}  "
                  f"{gaps[0]:6.0f} {gaps[1]:6.0f} {gaps[2]:6.0f}")


if __name__ == "__main__":
    receiver_map()
    array_factor()
    coarray()
    adaptive_demo()
    selfcal_demo()
    counting_tables()
    crowding_table()
    nearfield_table()
