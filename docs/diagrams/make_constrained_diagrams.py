"""Figures and numbers for the reconstruction-by-elimination page.

Run from the repository root:

    python docs/diagrams/make_constrained_diagrams.py

Writes constrained-*.svg and .png next to this file and prints every number
quoted on docs/constrained-reconstruction.md. All results come from the level
1 simulator with the random seeds stated below.
"""

import dataclasses
import sys
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
    """What each physical constraint adds, with positions known and equal smoothing."""
    rows = [("plain fit, usual smoothing (0.01)", lambda f: l1.least_squares(f)[0]),
            ("plain fit, light smoothing (0.001)", lambda f: l1.least_squares(f, smoothness=1e-3)[0]),
            ("reflectance between 0 and 1", lambda f: c.material_reconstruction(f, None, (0.0, 1.0))[0]),
            ("two known materials", lambda f: c.material_reconstruction(f, LEVELS)[0]),
            ("three materials offered, one absent", lambda f: c.material_reconstruction(f, (0.2, 0.6, 1.0))[0])]
    seeds = range(15)
    out = {n: [] for n, _ in rows}
    wrong, shown = [], {}
    for seed in seeds:
        f = frames_for(seed)
        for n, fn in rows:
            x = fn(f)
            out[n].append(contrasts(x) + [float(np.sqrt(np.mean((x - SURFACE) ** 2)))])
            if seed == 1:
                shown[n] = x
        s2 = c.material_reconstruction(f, LEVELS)[1]
        wrong.append([float(np.mean(s2[a:b] != SURFACE[a:b])) for _, a, b in GROUPS])
    print("Materials (seeds 0-14): mean contrast of the 4, 2, 1.2, 0.8, 0.48 µm groups, rms error, "
          "then lowest and highest 0.48 µm contrast")
    print("  true surface   ", np.round(contrasts(SURFACE), 2))
    for n, _ in rows:
        v = np.array(out[n])
        print(f"  {n:38s}", np.round(v.mean(axis=0), 3), round(v[:, 4].min(), 2), round(v[:, 4].max(), 2))
    print("  share of grid cells given the wrong material, per group:", np.round(np.mean(wrong, axis=0), 3))
    print("  transfer at 0.48 µm:", round(float(abs(l1.transfer(np.array([1 / 480.0]), OPTICS)[0])), 4))

    lo, hi = GROUPS[3][1] - 50, STOP + 50
    x = np.arange(SURFACE.size) * DX / 1e3
    fig, ax = plt.subplots(figsize=(9.6, 6.6))
    traces = [("true surface", SURFACE, INK),
              ("plain fit, usual smoothing", shown[rows[0][0]], INK2),
              ("plain fit, light smoothing", shown[rows[1][0]], ORANGE),
              ("light smoothing, reflectance kept between 0 and 1", shown[rows[2][0]], AQUA),
              ("light smoothing, two known materials (0.2 and 1.0)", shown[rows[3][0]], BLUE)]
    for k, (name, y, col) in enumerate(traces):
        off = 1.7 * (len(traces) - 1 - k)
        ax.plot(x[lo:hi], y[lo:hi] + off, color=col, lw=1.3)
        ax.text(x[lo], off + 1.25, name, fontsize=9.5, color=INK)
    ax.set_yticks([0, 1])
    ax.set_ylim(-0.3, 8.5)
    ax.set_ylabel("reflectance (each trace offset upward)")
    ax.set_xlabel("position along the scan (µm)")
    ax.set_title("bars repeating every 0.8 µm (left) and 0.48 µm (right), 1.12 µm pixels, positions known",
                 loc="left", fontsize=11)
    _clean(ax)
    fig.tight_layout()
    save(fig, "constrained-materials")


def _outcome(result):
    """Classify an elimination: 'true', 'set', 'none' or 'wrong'.

    'true': the only arrangement of bars left is the true one (it may be left
    at more than one neighbouring shift). 'set': the true arrangement is left
    together with others.
    'none': the method reported that nothing fits. 'wrong': something is left
    and the true layout is not part of it.
    """
    if not result.fits:
        return "none"
    shapes = result.surviving_shapes(LAYOUTS, 12)
    truth = np.repeat(TRUTH, 12).astype(np.int8)
    filled = np.nonzero(truth)[0]
    truth = truth[filled[0]:filled[-1] + 1]
    if any(s.size == truth.size and (s == truth).all() for s in shapes):
        return "true" if len(shapes) == 1 else "set"
    return "wrong"


def elimination():
    """Listing all 4,096 layouts of the 0.48 µm group and striking out those the data contradict."""
    f = frames_for(2)
    _, base = c.material_reconstruction(f, LEVELS)
    r = c.eliminate_candidates(f, base, START, 12, LAYOUTS, LEVELS)
    excess = np.sort(r.misfits[0] - r.misfits.min())
    print("Elimination, seed 2, full light, reconstructed surroundings: survivors", r.n_survivors,
          "true survives", bool(r.survivors[0, TRUE_INDEX]), "second-best excess", round(float(excess[1]), 0),
          "margin", round(r.margin, 1), "fits", r.fits, "local chi2 per reading", round(r.local_chi2_per_reading, 2),
          "layout counts for minimum width 1, 2, 3 cells:", [len(c.allowed_layouts(12, k)) for k in (1, 2, 3)])
    lights = [2500, 250, 50, 25, 10, 5]
    table = []
    for full in lights:
        counts, kept, best, fits = [], [], [], []
        for seed in range(40):
            g = frames_for(100 + seed, full_e=full)
            q = c.eliminate_candidates(g, SURFACE, START, 12, LAYOUTS, LEVELS)
            counts.append(q.n_survivors)
            kept.append(bool(q.survivors[0, TRUE_INDEX]))
            best.append(q.best[1] == TRUE_INDEX)
            fits.append(q.fits)
        table.append((full, np.median(counts), np.min(counts), np.max(counts), np.mean(kept), np.mean(best),
                      np.mean(fits)))
    print("Light sweep, seeds 100-139, true surroundings (electrons at full brightness; median / min / max "
          "survivors of 4096; share of trials: true layout kept, true layout is best fit, best passes absolute test):")
    for row in table:
        print("  ", row[0], row[1], row[2], row[3], round(row[4], 3), round(row[5], 3), round(row[6], 3))
    table = np.array(table)

    print("When an assumption is wrong, seeds 0-11, full light, reconstructed surroundings "
          "(counts of: only the true layout left / true layout among several / nothing fits / wrong layout left):")
    wrong_gap = l1.Optics1D(gap_nm=330)
    cases = [
        ("nothing wrong", LEVELS, None, 0.0, (0,)),
        ("materials assumed 0.25 and 0.95", (0.25, 0.95), None, 0.0, (0,)),
        ("gap assumed 330 nm, really 300 nm", LEVELS, wrong_gap, 0.0, (0,)),
        ("whole scan 120 nm from where assumed, not searched", LEVELS, None, 120.0, (0,)),
        ("whole scan 120 nm from where assumed, shifts searched", LEVELS, None, 120.0, tuple(range(-8, 9))),
    ]
    for name, levels, optics, offset, shifts in cases:
        tally = {"true": 0, "set": 0, "none": 0, "wrong": 0}
        for seed in range(12):
            g = frames_for(seed)
            if optics is not None:
                g = dataclasses.replace(g, optics=optics)
            pos = g.positions_nm + offset
            _, b = c.material_reconstruction(g, levels, positions_nm=pos)
            tally[_outcome(c.eliminate_candidates(g, b, START, 12, LAYOUTS, levels, positions_nm=pos,
                                                  shifts=shifts))] += 1
        print(f"  {name:52s}", tally["true"], tally["set"], tally["none"], tally["wrong"])

    fig, (a, b) = plt.subplots(1, 2, figsize=(11.2, 4.3))
    rank = np.arange(1, excess.size + 1)
    a.semilogy(rank[1:], excess[1:], ".", ms=2.5, color=ORANGE, label="wrong layouts")
    a.semilogy([1], [1.0], "o", ms=7, color=BLUE, label="true layout (best fit, drawn at 1)")
    a.axhline(r.margin, color=INK2, lw=0.9, ls=(0, (2, 3)))
    a.text(4000, r.margin * 1.25, "eliminated above this line", ha="right", fontsize=8.5, color=INK2)
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


def _position_trial(seeds, stiffness, settings=COARSE, **scan):
    errors = []
    for seed in seeds:
        f = frames_for(seed, **scan)
        est, _ = l1.estimate_positions(f, path_stiffness=stiffness, **settings)
        errors.append(l1.position_error(f, est))
    e = np.array(errors)
    solved = e < 20
    return e, int(solved.sum()), (float(np.median(e[solved])) if solved.any() else float("nan"))


def temporal():
    """The smooth-path constraint on frame positions."""
    seeds = range(40)
    wander = dict(wander_px=1.0, wander_frames=20.0)
    methods = [("each frame free", 0.0, dict()), ("each frame free, coarse start", 0.0, COARSE),
               ("smooth path, coarse start", 10.0, COARSE)]
    f0 = frames_for(0, **wander)
    limit = l1.position_precision_limit(f0)
    before = l1.position_error(f0, l1.nominal_positions(f0))
    print("Temporal, wander 1 pixel rms lasting 20 frames, seeds 0-39. Reference limit for one frame (nm):",
          round(limit, 2), "error before estimation (nm):", round(before, 0))
    errors = {}
    for n, stiff, settings in methods:
        e, solved, med = _position_trial(seeds, stiff, settings, **wander)
        errors[n] = e
        print(f"  {n:32s} solved (<20 nm): {solved}/40  median of solved {med:.1f} nm")
    print("Sweeps with the coarse start, seeds 0-23 (solved of 24, median nm of solved): smooth path | each frame free")
    sweep = range(24)
    for stiff in (0.1, 1.0, 10.0, 100.0, 1000.0):
        _, solved, med = _position_trial(sweep, stiff, **wander)
        print(f"  stiffness {stiff:7.1f}: {solved} {med:.1f}")
    for length in (3.0, 5.0, 10.0, 20.0, 40.0):
        _, s1, m1 = _position_trial(sweep, 10.0, wander_px=1.0, wander_frames=length)
        _, s0, m0 = _position_trial(sweep, 0.0, wander_px=1.0, wander_frames=length)
        print(f"  wander lasting {length:4.0f} frames: {s1} {m1:.1f} | {s0} {m0:.1f}")
    for jitter in (0.01, 0.03):
        _, s1, m1 = _position_trial(sweep, 10.0, jitter_px=jitter, **wander)
        _, s0, m0 = _position_trial(sweep, 0.0, jitter_px=jitter, **wander)
        print(f"  plus jitter {jitter} pixel per frame: {s1} {m1:.1f} | {s0} {m0:.1f}")
    _, s1, m1 = _position_trial(seeds, 10.0, wander_px=2.0, wander_frames=20.0)
    print(f"  wander 2 pixels rms, smooth path, seeds 0-39: {s1}/40 solved, median {m1:.1f} nm")

    nominal = l1.nominal_positions(f0)[:, 0]
    true_path = f0.positions_nm[:, 0] - nominal
    free = l1.estimate_positions(f0, **COARSE)[0][:, 0] - nominal
    tied = l1.estimate_positions(f0, path_stiffness=10.0, **COARSE)[0][:, 0] - nominal
    fig, (a, b) = plt.subplots(1, 2, figsize=(11.2, 4.3))
    t = np.arange(true_path.size)
    a.plot(t, true_path / 1e3, color=INK, lw=2.2, label="true path")
    a.plot(t, free / 1e3, color=ORANGE, lw=1.1, label="estimate, each frame free")
    a.plot(t, tied / 1e3, color=BLUE, lw=1.1, ls=(0, (4, 2)), label="estimate, smooth path required")
    a.set_xlabel("frame number")
    a.set_ylabel("position error of the frame (µm)")
    a.set_title("one scan (seed 0): the sensor wanders by up to 3 µm", loc="left", fontsize=10.5)
    a.legend(frameon=False, fontsize=8.5)
    rng = np.random.default_rng(0)
    for k, (n, _, _) in enumerate(methods):
        b.semilogy(k + rng.uniform(-0.22, 0.22, 40), errors[n], "o", ms=4.5, alpha=0.8,
                   color=[INK2, ORANGE, BLUE][k])
    b.axhline(limit, color=INK2, lw=0.9, ls=(0, (2, 3)))
    b.text(2.45, limit * 1.15, "limit for one frame alone", ha="right", fontsize=8.5, color=INK2)
    b.set_xticks([0, 1, 2])
    b.set_xticklabels(["each frame free", "each frame free,\ncoarse start", "smooth path,\ncoarse start"], fontsize=9)
    b.set_xlim(-0.5, 2.5)
    b.set_ylabel("position error left after estimation (nm, rms)")
    b.set_title("forty scans: error left over", loc="left", fontsize=10.5)
    for ax in (a, b):
        _clean(ax)
    fig.tight_layout()
    save(fig, "constrained-temporal")


def together(seeds=range(24)):
    """All constraints at once: positions unknown, and the whole scan misplaced by an unknown amount."""
    shifts = tuple(range(-8, 9))
    tally = {"true": 0, "set": 0, "none": 0, "wrong": 0}
    first_raised = int(np.nonzero(TRUTH)[0][0]) * 12 * DX
    rows, placed = [], 0
    print(f"Together, wander 1 pixel rms, overall offset unknown within 150 nm, seeds {seeds[0]}-{seeds[-1]}: "
          "offset nm; position error nm; contrast of 0.8 and 0.48 µm bars for a plain fit (0.01) at the assumed "
          "positions; a plain fit (0.001) at the estimated positions; two materials (0.001) at the estimated "
          "positions; outcome; local chi2 per reading; error of the place found for the layout, nm (min, max)")
    for seed in seeds:
        f = frames_for(seed, wander_px=1.0, wander_frames=20.0)
        offset = float(np.random.default_rng(1000 + seed).uniform(-150, 150))
        start = l1.nominal_positions(f) + offset
        fitted, snapped, pos = c.solve_surface_and_positions(f, LEVELS, start_positions_nm=start)
        r = c.eliminate_candidates(f, snapped, START, 12, LAYOUTS, LEVELS, positions_nm=pos, shifts=shifts)
        outcome = _outcome(r)
        tally[outcome] += 1
        aligned = l1.align_positions(f, pos)                       # for scoring the contrast only
        scored = contrasts(c.material_reconstruction(f, LEVELS, positions_nm=aligned)[0])[3:]
        same = contrasts(l1.least_squares(f, smoothness=1e-3, positions_nm=aligned)[0])[3:]
        plain = contrasts(l1.least_squares(f, positions_nm=l1.align_positions(f, start))[0])[3:]
        err = l1.position_error(f, pos)
        # the surface belongs to the estimated positions, so it is displaced by their mean error
        expected = first_raised + float(np.mean(pos - f.positions_nm))
        edges = r.surviving_edges_nm(LAYOUTS, 12, DX)
        place = None if edges is None else (round(edges[0] - expected, 1), round(edges[1] - expected, 1))
        if outcome == "true":
            rows.append([err] + plain + same + scored)
            placed += max(abs(place[0]), abs(place[1])) <= DX
        print("  ", seed, round(offset), round(err, 1), np.round(plain, 2), np.round(same, 2), np.round(scored, 2),
              outcome, round(r.local_chi2_per_reading, 2), place)
    print("  totals: only the true layout", tally["true"], "| true among several", tally["set"],
          "| nothing fits", tally["none"], "| wrong layout", tally["wrong"],
          "| of the solved, layout placed within 20 nm:", placed)
    if rows:
        med = np.median(np.array(rows), axis=0)
        print("  medians over the solved scans: position error nm", round(med[0], 1),
              "| plain 0.01 assumed positions (0.8, 0.48 µm)", np.round(med[1:3], 2),
              "| plain 0.001 estimated positions", np.round(med[3:5], 2),
              "| two materials 0.001 estimated positions", np.round(med[5:7], 2))


def wrong_noise_model():
    """What happens when the light level or the read noise given to the method is wrong."""
    print("Wrong noise model, seeds 0-5, full light, true surroundings and positions "
          "(outcomes true / set / none / wrong of 6; range of local chi2 per reading):")
    cases = [("light level assumed 1 % too high", dict(full_e=2500 * 1.01)),
             ("light level assumed 2 % too high", dict(full_e=2500 * 1.02)),
             ("light level assumed 5 % too high", dict(full_e=2500 * 1.05)),
             ("read noise assumed 15 electrons (true 2)", dict(read_e=15.0))]
    for name, change in cases:
        tally = {"true": 0, "set": 0, "none": 0, "wrong": 0}
        chi = []
        for seed in range(6):
            f = frames_for(seed)
            g = dataclasses.replace(f, noise=dataclasses.replace(f.noise, **change))
            r = c.eliminate_candidates(g, SURFACE, START, 12, LAYOUTS, LEVELS)
            tally[_outcome(r)] += 1
            chi.append(r.local_chi2_per_reading)
        print(f"   {name}: {tally['true']} / {tally['set']} / {tally['none']} / {tally['wrong']}; "
              f"{min(chi):.2f} to {max(chi):.2f}")


if __name__ == "__main__":
    only = sys.argv[1:]
    for step in (materials, elimination, wrong_noise_model, temporal, together):
        if not only or step.__name__ in only:
            step()
    if not only or "together_fresh" in only:
        together(range(100, 124))     # scans not used when the settings were chosen
