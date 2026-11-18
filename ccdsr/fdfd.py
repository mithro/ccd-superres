"""A small two-dimensional wave solver (finite differences, one frequency).

This is the first piece of level 4 of the simulation chain: it solves
Maxwell's equations exactly, up to the grid spacing, on a small
cross-section. It handles one case: structures that do not change along the
third direction, lit by light whose electric field points along that
direction (the "s" polarisation of the other modules). The field ``E`` then
obeys

    d2E/dx2 + d2E/dz2 + k0^2 * eps(x, z) * E = source,

with ``eps`` the square of the complex refractive index. The edges of the
grid are padded with absorbing layers (perfectly matched layers) so that
outgoing waves leave without reflecting.

A second entry point, :func:`solve_periodic`, handles structures that repeat
along ``x`` (a grating, a row of slits) lit by a plane wave, in either
polarisation. With the magnetic field ``H`` along the third direction (the
"p" polarisation, electric field across the lines) the equation is

    d/dx (1/eps dH/dx) + d/dz (1/eps dH/dz) + k0^2 * H = source.

The grid is uniform, the materials are stair-stepped onto it, and the
equations are solved directly with a sparse matrix. That limits the size to
about a million grid points, a few tens of micrometres of cross-section.
Lengths are in nanometres.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla


def _stretch(n, pml_cells, k0, spacing_nm, half=False):
    """Complex stretching factor along one axis, 1 outside the absorbing layers."""
    s = np.ones(n, dtype=complex)
    if pml_cells <= 0:
        return s
    pos = np.arange(n, dtype=float) + (0.5 if half else 0.0)
    depth = np.maximum(pml_cells - pos, pos - (n - 1 - pml_cells)) / pml_cells
    depth = np.clip(depth, 0.0, None)
    strength = -4.0 * np.log(1e-8) / (2.0 * k0 * pml_cells * spacing_nm)
    return s + 1j * strength * depth**3


@dataclass
class Field:
    """Solution on the grid. ``e[ix, iz]`` is the complex field."""

    e: np.ndarray
    spacing_nm: float
    k0: float
    inv_eps: np.ndarray | None = None      #: 1 / eps on the grid for the "p" polarisation, else None

    def flow_z(self, iz):
        """Power flowing in +z through the row ``iz``, per unit length in x.

        In units where a plane wave of unit amplitude in air carries 1. For
        the "p" polarisation ``e`` holds the magnetic field and the flow is
        weighted by ``1 / eps``; use rows where the material does not change
        from one grid point to the next.
        """
        d = (self.e[:, iz + 1] - self.e[:, iz - 1]) / (2 * self.spacing_nm)
        weight = 1.0 if self.inv_eps is None else self.inv_eps[:, iz]
        return np.imag(np.conj(self.e[:, iz]) * weight * d) / self.k0

    def flow_x(self, ix):
        """Power flowing in +x through the column ``ix``, per unit length in z."""
        d = (self.e[ix + 1, :] - self.e[ix - 1, :]) / (2 * self.spacing_nm)
        return np.imag(np.conj(self.e[ix, :]) * d) / self.k0


def solve(eps, source, wavelength_nm, spacing_nm, pml_cells=40):
    """Solve for the field on a grid.

    ``eps`` and ``source`` are arrays of shape ``(nx, nz)``: the square of the
    refractive index at each grid point, and the driving term. Returns a
    :class:`Field`.
    """
    eps = np.asarray(eps, dtype=complex)
    nx, nz = eps.shape
    k0 = 2 * np.pi / wavelength_nm
    h2 = spacing_nm**2

    def second_derivative(n):
        s = _stretch(n, pml_cells, k0, spacing_nm)
        s_half = _stretch(n, pml_cells, k0, spacing_nm, half=True)      # between i and i + 1
        up = 1.0 / (s[:-1] * s_half[:-1])                                # couples i to i + 1
        down = 1.0 / (s[1:] * s_half[:-1])                               # couples i + 1 to i
        centre = np.zeros(n, dtype=complex)
        centre[:-1] -= 1.0 / (s[:-1] * s_half[:-1])
        centre[1:] -= 1.0 / (s[1:] * s_half[:-1])
        centre[0] -= 1.0 / (s[0] * s_half[0])                             # field is zero outside
        centre[-1] -= 1.0 / (s[-1] * s_half[-1])
        return sp.diags([down, centre, up], [-1, 0, 1], format="csr") / h2

    dxx = sp.kron(second_derivative(nx), sp.identity(nz), format="csr")
    dzz = sp.kron(sp.identity(nx), second_derivative(nz), format="csr")
    operator = (dxx + dzz + sp.diags(k0**2 * eps.ravel())).tocsc()
    e = spla.spsolve(operator, np.asarray(source, dtype=complex).ravel())
    return Field(e=e.reshape(nx, nz), spacing_nm=spacing_nm, k0=k0)


def solve_periodic(eps, source, wavelength_nm, spacing_nm, pml_cells=40, polarisation="s", bloch_phase=0.0):
    """Solve for the field of a structure that repeats along ``x``.

    ``eps`` and ``source`` have shape ``(nx, nz)`` and describe one repeat.
    The field at ``x + nx * spacing`` is the field at ``x`` times
    ``exp(1j * bloch_phase)``: zero for light arriving straight on, and
    ``k0 * n * sin(angle) * nx * spacing`` for a plane wave arriving at an
    angle in a medium of index ``n`` (the source must carry the same phase
    slope). Absorbing layers close the grid in ``z`` only.

    ``polarisation`` is "s" (electric field along the lines, the solved
    field is ``E``) or "p" (magnetic field along the lines, the solved field
    is ``H``). For "p" the value of ``1 / eps`` between two grid points is
    one over the mean of ``eps`` at the two, which is exact for a flat
    boundary half way between them (``1 / eps`` times the slope of ``H`` is
    what stays continuous across a boundary).
    """
    if polarisation not in ("s", "p"):
        raise ValueError(f"polarisation is 's' or 'p', not {polarisation!r}")
    eps = np.asarray(eps, dtype=complex)
    nx, nz = eps.shape
    k0 = 2 * np.pi / wavelength_nm
    h = spacing_nm
    n = nx * nz
    index = np.arange(n).reshape(nx, nz)
    inv = 1.0 / eps if polarisation == "p" else np.ones_like(eps)
    wrap = np.exp(1j * bloch_phase)

    # x: forward difference from node i to the point half way to i + 1, the last one wrapping round
    right = np.roll(index, -1, axis=0)
    phase = np.ones((nx, nz), dtype=complex)
    phase[-1, :] = wrap
    forward_x = (sp.csr_matrix((phase.ravel(), (index.ravel(), right.ravel())), shape=(n, n))
                 - sp.identity(n, format="csr")) / h
    weight_x = 2.0 / (eps + np.roll(eps, -1, axis=0)) if polarisation == "p" else np.ones_like(eps)
    backward_x = -forward_x.conj().T                      # node i: (q at i + 1/2) - (q at i - 1/2), over h
    dxx = backward_x @ sp.diags(weight_x.ravel()) @ forward_x

    # z: the same with complex stretching in the absorbing layers and zero field outside the grid
    s_node = _stretch(nz, pml_cells, k0, h)
    s_half = _stretch(nz, pml_cells, k0, h, half=True)
    rows, cols = index[:, :-1].ravel(), index[:, 1:].ravel()
    ones = np.ones(rows.size)
    forward_z = (sp.csr_matrix((ones, (rows, cols)), shape=(n, n))
                 - sp.csr_matrix((np.ones(n), (index.ravel(), index.ravel())), shape=(n, n))) / h
    weight_z = np.empty((nx, nz), dtype=complex)
    weight_z[:, :-1] = 2.0 / (eps[:, :-1] + eps[:, 1:]) if polarisation == "p" else 1.0
    weight_z[:, -1] = inv[:, -1]
    weight_z = weight_z / s_half[None, :]
    backward_z = -forward_z.T                              # at the first node the missing half step holds zero field
    first = sp.csr_matrix(((inv[:, 0] / s_half[0]) / h**2, (index[:, 0], index[:, 0])), shape=(n, n))
    dzz = sp.diags(np.tile(1.0 / s_node, nx)) @ (backward_z @ sp.diags(weight_z.ravel()) @ forward_z - first)

    mass = k0**2 * (eps if polarisation == "s" else np.ones_like(eps))
    operator = (dxx + dzz + sp.diags(mass.ravel())).tocsc()
    u = spla.spsolve(operator, np.asarray(source, dtype=complex).ravel())
    return Field(e=u.reshape(nx, nz), spacing_nm=h, k0=k0, inv_eps=inv if polarisation == "p" else None)
