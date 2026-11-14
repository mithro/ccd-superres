"""Figures and numbers for the reconstruction-by-elimination page.

Run from the repository root:

    python docs/diagrams/make_constrained_diagrams.py

Writes constrained-*.svg and .png next to this file and prints every number
quoted on docs/constrained-reconstruction.md. All results come from the level
1 simulator with the random seeds stated below.
"""

import sys
import warnings
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from make_diagrams import AQUA, BLUE, INK, INK2, ORANGE, _clean, plt, save  # noqa: E402

from ccdsr import constrained as c  # noqa: E402
from ccdsr import level1 as l1  # noqa: E402

DX = 20.0
LEVELS = (0.2, 1.0)
OPTICS = l1.Optics1D(gap_nm=300)
SURFACE, GROUPS = l1.bar_groups([4000, 2000, 1200, 800, 480], DX)
START, STOP = GROUPS[4][1], GROUPS[4][2]
LAYOUTS = c.allowed_layouts(12, 1)
TRUTH = np.where(SURFACE[START:STOP:12] > 0.6, 1.0, 0.0)
TRUE_INDEX = int(np.where((LAYOUTS == TRUTH).all(axis=1))[0][0])
COARSE = dict(smoothness=(1000.0, 1e-2), rounds=40, max_step_px=3.0)


def frames_for(seed, full_e=2500.0, **scan):
    return l1.simulate(SURFACE, DX, OPTICS, l1.Scan1D(n_pixels=64, n_frames=160, shift_px=0.37, **scan),
                       l1.Noise1D(full_e=full_e), seed=seed)


def contrasts(x):
    return [l1.bar_contrast(x, g, DX) for g in GROUPS]


def materials():
    """What each physical constraint adds, with positions known."""
    names = ["no constraint", "reflectance between 0 and 1", "two known materials"]
    rows = {n: [] for n in names}
    wrong = []
    for seed in range(5):
        f = frames_for(seed)
        rms = lambda x: float(np.sqrt(np.mean((x - SURFACE) ** 2)))
        x0 = l1.least_squares(f)[0]
        x1, _ = c.material_reconstruction(f, None, (0.0, 1.0))
        x2, s2 = c.material_reconstruction(f, LEVELS)
        for n, x in zip(names, (x0, x1, x2)):
            rows[n].append(contrasts(x) + [rms(x)])
        wrong.append([float(np.mean(s2[a:b] != SURFACE[a:b])) for _, a, b in GROUPS])
        if seed == 1:
            shown = (x0, x1, x2)
    print("Materials (mean of seeds 0-4): contrast of the 4, 2, 1.2, 0.8, 0.48 µm groups, then rms error")
    print("  true surface   ", np.round(contrasts(SURFACE), 2))
    for n in names:
        print(f"  {n:28s}", np.round(np.mean(rows[n], axis=0), 3))
    print("  share of grid cells given the wrong material, per group:", np.round(np.mean(wrong, axis=0), 3))
    print("  transfer at 0.48 µm:", round(float(abs(l1.transfer(np.array([1 / 480.0]), OPTICS)[0])), 4))

    lo, hi = GROUPS[3][1] - 50, STOP + 50
    x = np.arange(SURFACE.size) * DX / 1e3
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    traces = [("true surface", SURFACE, INK), ("fit with no constraint", shown[0], ORANGE),
              ("fit with reflectance kept between 0 and 1", shown[1], AQUA),
              ("fit with two known materials (0.2 and 1.0)", shown[2], BLUE)]
    for k, (name, y, col) in enumerate(traces):
        off = 1.6 * (len(traces) - 1 - k)
        ax.plot(x[lo:hi], y[lo:hi] + off, color=col, lw=1.3)
        ax.text(x[lo], off + 1.2, name, fontsize=9.5, color=INK)
    ax.set_yticks([0, 1])
    ax.set_ylim(-0.2, 6.4)
    ax.set_ylabel("reflectance (each trace offset upward)")
    ax.set_xlabel("position along the scan (µm)")
    ax.set_title("0.8 µm bars (left) and 0.48 µm bars (right), 1.12 µm pixels, positions known", loc="left",
                 fontsize=11)
    _clean(ax)
    fig.tight_layout()
    save(fig, "constrained-materials")


def elimination():
    """Listing all 4,096 layouts of the 0.48 µm group and striking out those the data contradict."""
    f = frames_for(2)
    _, base = c.material_reconstruction(f, LEVELS)
    misfits, survivors = c.eliminate_candidates(f, base, START, 12, LAYOUTS, LEVELS)
    excess = np.sort(misfits - misfits.min())
    print("Elimination, seed 2, full light: survivors", int(survivors.sum()), "true survives",
          bool(survivors[TRUE_INDEX]), "second-best excess", round(float(excess[1]), 0),
          "layout counts for minimum width 1, 2, 3 cells:", [len(c.allowed_layouts(12, k)) for k in (1, 2, 3)])
    lights = [2500, 250, 50, 25, 10, 5]
    table = []
    for full in lights:
        counts, kept, best = [], [], []
        for seed in range(40):
            g = frames_for(100 + seed, full_e=full)
            m, s = c.eliminate_candidates(g, SURFACE, START, 12, LAYOUTS, LEVELS)
            counts.append(int(s.sum()))
            kept.append(bool(s[TRUE_INDEX]))
            best.append(int(np.argmin(m)) == TRUE_INDEX)
        table.append((full, np.median(counts), np.min(counts), np.max(counts), np.mean(kept), np.mean(best)))
    print("Light sweep, seeds 100-139 (electrons at full brightness, median / min / max survivors of 4096, "
          "share of trials true layout survives, share of trials true layout is the best fit):")
    for row in table:
        print("  ", row[0], row[1], row[2], row[3], round(row[4], 3), round(row[5], 3))
    table = np.array(table)

    fig, (a, b) = plt.subplots(1, 2, figsize=(11.2, 4.3))
    rank = np.arange(1, excess.size + 1)
    a.semilogy(rank[1:], excess[1:], ".", ms=2.5, color=ORANGE, label="wrong layouts")
    a.semilogy([1], [1.0], "o", ms=7, color=BLUE, label="true layout (best fit, drawn at 1)")
    a.axhline(49, color=INK2, lw=0.9, ls=(0, (2, 3)))
    a.text(4000, 62, "eliminated above this line", ha="right", fontsize=8.5, color=INK2)
    a.set_xscale("log")
    a.set_xlabel("candidate layouts, best fit first")
    a.set_ylabel("misfit above the best candidate")
    a.set_title("all 4,096 layouts of twelve 240 nm cells, full light", loc="left", fontsize=10.5)
    a.legend(frameon=False, fontsize=8.5, loc="lower right")
    b.loglog(table[:, 0], table[:, 1], "o-", color=BLUE, ms=5, lw=1.4, label="median")
    b.fill_between(table[:, 0], table[:, 2], table[:, 3], color=BLUE, alpha=0.15, lw=0, label="range over 40 trials")
    b.set_xlabel("electrons per reading at full brightness")
    b.set_ylabel("layouts not eliminated (of 4,096)")
    b.set_title("less light leaves more layouts standing", loc="left", fontsize=10.5)
    b.set_ylim(0.7, 5000)
    b.legend(frameon=False, fontsize=8.5, loc="upper right")
    for ax in (a, b):
        _clean(ax)
    fig.tight_layout()
    save(fig, "constrained-elimination")


def temporal():
    """The smooth-path constraint on frame positions."""
    methods = [("each frame free", dict()), ("each frame free, coarse start", COARSE),
               ("smooth path, coarse start", dict(path_stiffness=10.0, **COARSE))]
    errors = {n: [] for n, _ in methods}
    shown = None
    for seed in range(8):
        f = frames_for(seed, wander_px=1.0, wander_frames=20.0)
        for n, kw in methods:
            est, _ = l1.estimate_positions(f, **kw)
            errors[n].append(l1.position_error(f, est))
            if seed == 0:
                shown = shown or {}
                shown[n] = (est - l1.nominal_positions(f))[:, 0]
        if seed == 0:
            true_path = (f.positions_nm - l1.nominal_positions(f))[:, 0]
            limit = l1.position_precision_limit(f)
    print("Temporal, wander 1 pixel rms over 20 frames, seeds 0-7. Per-frame reference limit (nm):", round(limit, 2))
    for n, _ in methods:
        e = np.array(errors[n])
        print(f"  {n:32s} errors nm {np.round(e, 1)}  solved (<20 nm): {int((e < 20).sum())}/8  "
              f"median of solved {np.median(e[e < 20]):.1f}")

    larger = []
    for seed in range(4):
        f = frames_for(seed, wander_px=2.0, wander_frames=20.0)
        est, _ = l1.estimate_positions(f, path_stiffness=10.0, **COARSE)
        larger.append(l1.position_error(f, est))
    print("  wander 2 pixels rms, smooth path, seeds 0-3: errors nm", np.round(larger, 1))

    fig, (a, b) = plt.subplots(1, 2, figsize=(11.2, 4.3))
    t = np.arange(true_path.size)
    centre = lambda v: (v - v.mean()) / 1e3
    a.plot(t, centre(true_path), color=INK, lw=2.2, label="true path")
    a.plot(t, centre(shown["each frame free, coarse start"]), color=ORANGE, lw=1.1, label="estimate, each frame free")
    a.plot(t, centre(shown["smooth path, coarse start"]), color=BLUE, lw=1.1, ls=(0, (4, 2)),
           label="estimate, smooth path required")
    a.set_xlabel("frame number")
    a.set_ylabel("position error of the frame (µm)")
    a.set_title("one scan (seed 0): the sensor wanders by about a pixel", loc="left", fontsize=10.5)
    a.legend(frameon=False, fontsize=8.5)
    for k, (n, _) in enumerate(methods):
        b.semilogy(np.full(8, k) + np.linspace(-0.15, 0.15, 8), errors[n], "o", ms=5.5,
                   color=[INK2, ORANGE, BLUE][k])
    b.axhline(limit, color=INK2, lw=0.9, ls=(0, (2, 3)))
    b.text(2.45, limit * 1.15, "limit for one frame alone", ha="right", fontsize=8.5, color=INK2)
    b.set_xticks([0, 1, 2])
    b.set_xticklabels(["each frame free", "each frame free,\ncoarse start", "smooth path,\ncoarse start"], fontsize=9)
    b.set_xlim(-0.5, 2.5)
    b.set_ylabel("position error left after estimation (nm, rms)")
    b.set_title("eight scans: error left over", loc="left", fontsize=10.5)
    for ax in (a, b):
        _clean(ax)
    fig.tight_layout()
    save(fig, "constrained-temporal")


def together():
    """All constraints at once, positions unknown."""
    print("Together, wander 1 pixel rms, seeds 0-4: position error nm; contrast (five groups) with assumed "
          "positions and no constraints; with everything; layouts surviving; true layout survives")
    for seed in range(5):
        f = frames_for(seed, wander_px=1.0, wander_frames=20.0)
        _, _, pos = c.solve_surface_and_positions(f, LEVELS)
        aligned = l1.align_positions(f, pos)
        fitted, snapped = c.material_reconstruction(f, LEVELS, positions_nm=aligned)
        _, s = c.eliminate_candidates(f, snapped, START, 12, LAYOUTS, LEVELS, positions_nm=aligned)
        plain = l1.least_squares(f, positions_nm=l1.align_positions(f, l1.nominal_positions(f)))[0]
        print("  ", seed, round(l1.position_error(f, pos), 1), np.round(contrasts(plain), 2),
              np.round(contrasts(fitted), 2), int(s.sum()), bool(s[TRUE_INDEX]))


if __name__ == "__main__":
    warnings.simplefilter("ignore", RuntimeWarning)
    materials()
    elimination()
    temporal()
    together()
