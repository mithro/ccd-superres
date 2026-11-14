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

import warnings
from dataclasses import dataclass
from itertools import product

import numpy as np
from scipy.sparse.linalg import LinearOperator, cg

from . import level1 as l1

__all__ = ["material_reconstruction", "solve_surface_and_positions", "allowed_layouts",
           "eliminate_candidates", "Elimination", "chi_squared", "misfit"]


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
    x, info = cg(LinearOperator((n, n), matvec=normal, dtype=float), rhs, x0=start, rtol=1e-8, maxiter=300,
                 M=LinearOperator((n, n), matvec=lambda v: filt(v, 1 / diag), dtype=float))
    if info != 0:
        warnings.warn("constrained fit stopped before converging", RuntimeWarning, stacklevel=3)
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

    ``smoothness`` is the same quantity as in :func:`ccdsr.level1.least_squares`
    but defaults to a tenth of its value there. Compare the two only at the
    same smoothness: a weaker preference for smoothness by itself brings back
    fine detail (and noise), whatever the constraints.

    Returns ``(estimate, snapped)``: the final fit, which is pulled towards
    the allowed values but not forced onto them, and the same surface moved
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
    """Surface and frame positions together.

    First the positions are estimated with the smooth-path constraint,
    starting from a heavily smoothed picture. Then the surface is rebuilt with
    the material constraint at those positions. A shift of all frames
    together cannot be found from the readings, so the result is positioned
    wherever the starting path put it.

    Returns ``(estimate, snapped, positions)``.
    """
    positions, _ = l1.estimate_positions(frames, start_positions_nm, rounds=rounds, smoothness=smoothness,
                                         max_step_px=max_step_px, path_stiffness=path_stiffness)
    estimate, snapped = material_reconstruction(frames, levels, bounds, positions)
    return estimate, snapped, positions


# -------------------------------------------------- listing and eliminating

def allowed_layouts(n_cells, min_run=1):
    """Every way to fill ``n_cells`` layout cells with two materials under a width rule.

    A layout is a row of 0s and 1s. ``min_run`` is the smallest number of
    cells in a row that a feature or a space may have. Runs that touch the
    ends of the region are exempt, because they may continue outside it; if
    what lies outside is known, some of the layouts returned are in fact not
    allowed. Returns an array ``(n_layouts, n_cells)``.
    """
    keep = []
    for bits in product((0, 1), repeat=n_cells):
        runs, run = [], 1
        for a, b in zip(bits, bits[1:]):
            if a == b:
                run += 1
            else:
                runs.append(run)
                run = 1
        runs.append(run)
        if len(runs) <= 2 or min(runs[1:-1]) >= min_run:
            keep.append(bits)
    return np.array(keep, dtype=float)


def _variance(frames, predicted):
    return np.maximum((np.maximum(predicted, 0) if frames.noise.photon else 0.0) + frames.noise.read_e**2,
                      1e-12)


def _predict(frames, surface, positions_nm):
    pos = frames.positions_nm if positions_nm is None else positions_nm
    s = l1.sampling_matrix(pos, frames.n_grid, frames.dx_nm)
    return l1._scale(frames) * (s @ l1.blur(np.asarray(surface, dtype=float), frames.dx_nm, frames.optics,
                                            frames.scan))


def chi_squared(frames: l1.Frames1D, surface, positions_nm=None):
    """Whether a candidate surface fits the readings at all.

    The sum over readings of (measured minus predicted) squared, each divided
    by the noise variance expected for that reading. For the true surface it
    comes out close to the number of readings, give or take about the square
    root of twice that number.
    """
    predicted = _predict(frames, surface, positions_nm)
    return float(np.sum((frames.readings.ravel() - predicted) ** 2 / _variance(frames, predicted)))


def misfit(frames: l1.Frames1D, surface, positions_nm=None):
    """How badly a candidate surface disagrees with the readings, for comparing candidates.

    :func:`chi_squared` plus the sum of the logarithm of the expected noise
    variance of each reading. The second term is needed because the noise
    depends on the brightness: without it a brighter candidate, which expects
    more noise, is let off more lightly and wins unfairly. Twice the negative
    log-likelihood under Gaussian noise, up to a constant. Only differences
    between candidates mean anything.
    """
    predicted = _predict(frames, surface, positions_nm)
    variance = _variance(frames, predicted)
    return float(np.sum((frames.readings.ravel() - predicted) ** 2 / variance + np.log(variance)))


@dataclass
class Elimination:
    """Outcome of :func:`eliminate_candidates`."""

    misfits: np.ndarray        # (n_shifts, n_layouts)
    survivors: np.ndarray      # same shape, True where not eliminated; all False if nothing fits
    fits: bool                 # does the best candidate pass the absolute test?
    local_chi2_per_reading: float   # chi-squared of the best candidate over nearby readings, per reading
    margin: float              # misfit margin above the best within which candidates are kept
    shifts: tuple              # the grid shifts tried, in grid steps
    best: tuple                # (index into shifts, index into layouts) of the best candidate

    @property
    def n_survivors(self):
        return int(self.survivors.sum())

    def surviving_patterns(self, layouts, cell_cells):
        """The distinct surfaces among the survivors, drawn on the fine grid.

        Different candidates can describe the same surface: a layout moved by
        one cell is another layout at a different shift. Each survivor is
        drawn as a row of 0s and 1s, one entry per grid step, over the window
        from the smallest shift to the end of the region at the largest
        shift, and duplicates are removed. Returns an array
        ``(n_patterns, window)``; entry 0 of a row is at grid index
        ``start_index + min(shifts)``.
        """
        layouts = np.asarray(layouts)
        width = layouts.shape[1] * cell_cells
        low = min(self.shifts)
        rows = set()
        for j, i in zip(*np.nonzero(self.survivors)):
            row = np.zeros(max(self.shifts) - low + width, dtype=np.int8)
            at = self.shifts[j] - low
            row[at:at + width] = np.repeat(layouts[i], cell_cells).astype(np.int8)
            rows.add(row.tobytes())
        window = max(self.shifts) - low + width
        return np.array([np.frombuffer(r, dtype=np.int8) for r in sorted(rows)]).reshape(-1, window)

    def surviving_shapes(self, layouts, cell_cells):
        """The distinct surviving surfaces with their position ignored.

        Each pattern from :meth:`surviving_patterns` with the empty margin at
        both ends removed, duplicates dropped: the same bars found at two
        neighbouring shifts count once. Returns a list of arrays.
        """
        shapes = set()
        for row in self.surviving_patterns(layouts, cell_cells):
            filled = np.nonzero(row)[0]
            shapes.add(row[filled[0]:filled[-1] + 1].tobytes() if filled.size else b"")
        return [np.frombuffer(b, dtype=np.int8) for b in sorted(shapes)]

    def surviving_shifts_nm(self, dx_nm):
        """Smallest and largest shift among the survivors, in nanometres."""
        rows = np.nonzero(self.survivors.any(axis=1))[0]
        return (self.shifts[rows.min()] * dx_nm, self.shifts[rows.max()] * dx_nm) if rows.size else None


def eliminate_candidates(frames: l1.Frames1D, base_surface, start_index, cell_cells, layouts, levels,
                         positions_nm=None, shifts=(0,), false_rejection=0.01, fit_sigmas=5.0, local_px=1.5):
    """Test every candidate layout of a small region against the readings.

    ``base_surface`` is the surface outside the region (for instance a
    reconstruction). The region starts at grid index ``start_index`` and is
    made of layout cells ``cell_cells`` grid steps wide. Each row of
    ``layouts`` gives one candidate: 0 for the first material in ``levels``
    and 1 for the second. ``shifts`` lists displacements of the whole region,
    in grid steps, that are also to be tried: use it when the position of the
    scan on the surface, or of the drawing grid, is not known exactly. The
    candidates are then every layout at every shift.

    Every candidate's readings are predicted with the forward model. Two tests
    follow.

    *Relative.* A candidate is eliminated when its :func:`misfit` exceeds the
    best one's by more than ``2 * ln(K / false_rejection)``, where ``K`` is
    the number of candidates. If the model is right, the chance that the true
    candidate is eliminated this way is at most ``false_rejection``.

    *Absolute.* The best candidate must itself fit: its chi-squared over the
    readings taken within ``local_px`` pixels of the region must not exceed
    their number by more than ``fit_sigmas`` standard deviations. If it does,
    no candidate explains the data (wrong materials, wrong positions, wrong
    base surface or wrong blur model), nothing survives, and ``fits`` is
    False. Only nearby readings are used so that errors in the base surface
    far from the region do not condemn every candidate.

    Returns an :class:`Elimination`.
    """
    pos = frames.positions_nm if positions_nm is None else positions_nm
    n, dx = frames.n_grid, frames.dx_nm
    s = l1.sampling_matrix(pos, n, dx)
    light = l1._scale(frames)
    lo, hi = levels
    layouts = np.asarray(layouts, dtype=float)
    n_cells = layouts.shape[1]
    width = n_cells * cell_cells
    m = frames.readings.ravel()
    base = np.array(base_surface, dtype=float)
    cover = np.arange(start_index + min(shifts), start_index + max(shifts) + width) % n
    base[cover] = lo
    predicted0 = light * (s @ l1.blur(base, dx, frames.optics, frames.scan))
    misfits = np.empty((len(shifts), layouts.shape[0]))
    all_responses = []
    for j, shift in enumerate(shifts):
        # the forward model is linear, so each cell's contribution is computed once
        responses = []
        for k in range(n_cells):
            bump = np.zeros(n)
            bump[(start_index + shift + k * cell_cells + np.arange(cell_cells)) % n] = hi - lo
            responses.append(light * (s @ l1.blur(bump, dx, frames.optics, frames.scan)))
        responses = np.array(responses)
        all_responses.append(responses)
        for i in range(0, layouts.shape[0], 256):
            predicted = predicted0[None, :] + layouts[i:i + 256] @ responses
            variance = _variance(frames, predicted)
            misfits[j, i:i + 256] = np.sum((m[None, :] - predicted) ** 2 / variance + np.log(variance), axis=1)
    margin = 2 * np.log(misfits.size / false_rejection)
    best = np.unravel_index(int(np.argmin(misfits)), misfits.shape)
    predicted = predicted0 + layouts[best[1]] @ all_responses[best[0]]
    length = n * dx
    centre = (start_index + shifts[best[0]] + width / 2) * dx
    distance = np.abs((np.asarray(pos).ravel() - centre + length / 2) % length - length / 2)
    near = distance <= width * dx / 2 + local_px * frames.optics.pitch_nm
    chi2 = float(np.sum((m[near] - predicted[near]) ** 2 / _variance(frames, predicted[near])))
    count = int(near.sum())
    fits = chi2 <= count + fit_sigmas * np.sqrt(2 * count)
    survivors = (misfits <= misfits.min() + margin) if fits else np.zeros(misfits.shape, dtype=bool)
    return Elimination(misfits, survivors, bool(fits), chi2 / count, float(margin), tuple(shifts),
                       (int(best[0]), int(best[1])))
