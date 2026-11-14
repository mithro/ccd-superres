"""Reconstruction by ruling out what is physically impossible (level 1, one dimension).

The plain reconstructions in :mod:`ccdsr.level1` accept any surface that
explains the readings. This module adds what is known about the real world
before the scan starts, and uses it to throw away explanations that could not
be true:

- **Materials.** A chip surface is made of a few materials, each with its own
  reflectance. A reflectance below zero, above the brightest material, or
  (where the materials are known) in between two of them over a wide area, is
  not possible.
- **Layout rules.** Chip features are drawn on a grid and cannot be narrower
  than the process allows. :func:`eliminate_candidates` lists every layout
  the rules allow for a small region, predicts the readings each would give,
  and keeps only those the measured readings do not contradict.
- **Time.** The surface does not change during the scan and the sensor has
  inertia, so the frame positions must form a smooth path. That constraint is
  the ``path_stiffness`` argument of :func:`ccdsr.level1.estimate_positions`.

The functions take the readings, positions and the blur model, plus the
stated constraints. They never see the true surface.
"""

from __future__ import annotations

from itertools import product

import numpy as np
from scipy.sparse.linalg import LinearOperator, cg

from . import level1 as l1

__all__ = ["material_reconstruction", "solve_surface_and_positions", "allowed_layouts",
           "eliminate_candidates", "misfit"]


def _solve(frames, positions, smoothness, target=None, pull=0.0, start=None):
    """Least squares with smoothing and an optional pull towards a target surface."""
    n, dx = frames.n_grid, frames.dx_nm
    s = l1.sampling_matrix(positions, n, dx)
    h = l1._grid_transfer(n, dx, frames.optics, frames.scan)
    m = frames.readings.ravel() / l1._scale(frames)
    sts = (s.T @ s).tocsr()
    mean_w = sts.diagonal().mean()
    lam, mu = smoothness * mean_w, pull * mean_w
    lap = (2 * np.sin(np.pi * np.fft.fftfreq(n))) ** 2

    def filt(v, g):
        return np.fft.ifft(np.fft.fft(v) * g).real

    def normal(v):
        return filt(sts @ filt(v, h), np.conj(h)) + lam * filt(v, lap) + mu * v

    rhs = filt(np.asarray(s.T @ m).ravel(), np.conj(h))
    if target is not None:
        rhs = rhs + mu * target
    diag = mean_w * np.abs(h) ** 2 + lam * lap + mu + 1e-12 * mean_w
    x, _ = cg(LinearOperator((n, n), matvec=normal, dtype=float), rhs, x0=start, rtol=1e-8, maxiter=300,
              M=LinearOperator((n, n), matvec=lambda v: filt(v, 1 / diag), dtype=float))
    return x


def _nearest_level(x, levels):
    levels = np.asarray(levels, dtype=float)
    return levels[np.argmin(np.abs(x[:, None] - levels[None, :]), axis=1)]


def material_reconstruction(frames: l1.Frames1D, levels=None, bounds=(0.0, 1.0), positions_nm=None,
                            smoothness=1e-3, pulls=(1e-4, 1e-1), rounds=25):
    """Best fit to the readings among surfaces that the materials allow.

    ``bounds`` is the range of reflectance that is physically possible.
    ``levels`` lists the reflectance of each material present, if known; with
    ``None`` only the bounds are applied.

    Works in rounds. Each round moves the current estimate to the nearest
    allowed surface (clipped to the bounds, or snapped to the nearest material)
    and then refits the readings while being pulled towards that allowed
    surface. The pull is weak at first, so the readings decide, and grows from
    ``pulls[0]`` to ``pulls[1]``, so that the result ends close to an allowed
    surface. It is a search, not a proof: it can settle on a wrong allowed
    surface where the readings are too weak to decide.

    Returns ``(estimate, snapped)``: the final fit, and the same surface moved
    exactly onto the allowed values.
    """
    pos = frames.positions_nm if positions_nm is None else positions_nm

    def allowed(x):
        x = np.clip(x, *bounds)
        return x if levels is None else _nearest_level(x, levels)

    x = _solve(frames, pos, 1e-2)
    for pull in np.geomspace(pulls[0], pulls[1], rounds):
        x = _solve(frames, pos, smoothness, allowed(x), pull, start=x)
    return x, allowed(x)


def solve_surface_and_positions(frames: l1.Frames1D, levels=None, bounds=(0.0, 1.0),
                                start_positions_nm=None, path_stiffness=10.0, rounds=40,
                                smoothness=(1000.0, 1e-2), max_step_px=3.0):
    """Surface and frame positions together, using every constraint.

    First the positions are estimated with the smooth-path constraint, with
    the surface kept within the physical bounds at every round. Then the
    surface is rebuilt with the material constraint at those positions.

    Returns ``(estimate, snapped, positions)``.
    """
    def bounded(f, pos, level):
        est, _ = l1.least_squares(f, smoothness=level, positions_nm=pos)
        return np.clip(est, *bounds)

    positions, _ = l1.estimate_positions(frames, start_positions_nm, rounds=rounds, smoothness=smoothness,
                                         max_step_px=max_step_px, path_stiffness=path_stiffness,
                                         reconstruct=bounded)
    estimate, snapped = material_reconstruction(frames, levels, bounds, positions)
    return estimate, snapped, positions


# -------------------------------------------------- listing and eliminating

def allowed_layouts(n_cells, min_run=1):
    """Every way to fill ``n_cells`` layout cells with two materials under a width rule.

    A layout is a row of 0s and 1s. ``min_run`` is the smallest number of
    cells in a row that a feature or a space may have (runs that touch the
    ends of the region are exempt, because they may continue outside it).
    Returns an array ``(n_layouts, n_cells)``.
    """
    keep = []
    for bits in product((0, 1), repeat=n_cells):
        ok, run = True, 1
        runs = []
        for a, b in zip(bits, bits[1:]):
            if a == b:
                run += 1
            else:
                runs.append(run)
                run = 1
        runs.append(run)
        if len(runs) > 2 and min(runs[1:-1]) < min_run:
            ok = False
        if ok:
            keep.append(bits)
    return np.array(keep, dtype=float)


def misfit(frames: l1.Frames1D, surface, positions_nm=None):
    """How badly a candidate surface disagrees with the readings.

    The sum over readings of (measured minus predicted) squared, each divided
    by the noise variance expected for that reading. For the true surface it
    comes out close to the number of readings.
    """
    pos = frames.positions_nm if positions_nm is None else positions_nm
    s = l1.sampling_matrix(pos, frames.n_grid, frames.dx_nm)
    light = l1._scale(frames)
    predicted = light * (s @ l1.blur(np.asarray(surface, dtype=float), frames.dx_nm, frames.optics, frames.scan))
    variance = (np.maximum(predicted, 0) if frames.noise.photon else 0.0) + frames.noise.read_e**2
    return float(np.sum((frames.readings.ravel() - predicted) ** 2 / np.maximum(variance, 1e-12)))


def eliminate_candidates(frames: l1.Frames1D, base_surface, start_index, cell_cells, layouts, levels,
                         positions_nm=None, sigmas=7.0):
    """Test every candidate layout of a small region against the readings.

    ``base_surface`` is the surface outside the region (for instance a
    reconstruction). The region starts at grid index ``start_index`` and is
    made of layout cells ``cell_cells`` grid steps wide. Each row of
    ``layouts`` gives one candidate: 0 for the first material in ``levels``
    and 1 for the second.

    Every candidate's readings are predicted with the forward model and
    compared with the measured ones. A candidate is eliminated when its misfit
    exceeds that of the best candidate by more than ``sigmas**2``. The default
    of 7 (a margin of 49) was set by trial: with 4,096 candidates the true
    layout was never eliminated in 40 trials at each light level down to 10
    electrons at full brightness, and once in 40 at 5 electrons. A margin of
    25 eliminated the true layout in a third of trials at 10 electrons,
    because among thousands of wrong candidates some fit the noise better
    than the truth does by chance.

    Returns ``(misfits, survivors)``: the misfit of each candidate and a
    boolean array marking those not eliminated.
    """
    pos = frames.positions_nm if positions_nm is None else positions_nm
    n, dx = frames.n_grid, frames.dx_nm
    s = l1.sampling_matrix(pos, n, dx)
    light = l1._scale(frames)
    lo, hi = levels
    n_cells = layouts.shape[1]
    base = np.array(base_surface, dtype=float)
    base[start_index:start_index + n_cells * cell_cells] = lo
    predicted0 = light * (s @ l1.blur(base, dx, frames.optics, frames.scan))
    # the forward model is linear, so each cell's contribution is computed once
    responses = []
    for k in range(n_cells):
        bump = np.zeros(n)
        bump[start_index + k * cell_cells:start_index + (k + 1) * cell_cells] = hi - lo
        responses.append(light * (s @ l1.blur(bump, dx, frames.optics, frames.scan)))
    responses = np.array(responses)
    m = frames.readings.ravel()
    misfits = np.empty(layouts.shape[0])
    for i in range(0, layouts.shape[0], 256):
        predicted = predicted0[None, :] + layouts[i:i + 256] @ responses
        variance = (np.maximum(predicted, 0) if frames.noise.photon else 0.0) + frames.noise.read_e**2
        misfits[i:i + 256] = np.sum((m[None, :] - predicted) ** 2 / np.maximum(variance, 1e-12), axis=1)
    survivors = misfits <= misfits.min() + sigmas**2
    return misfits, survivors
