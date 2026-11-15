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

    def flow_z(self, iz):
        """Power flowing in +z through the row ``iz``, per unit length in x.

        In units where a plane wave of unit amplitude in air carries 1.
        """
        d = (self.e[:, iz + 1] - self.e[:, iz - 1]) / (2 * self.spacing_nm)
        return np.imag(np.conj(self.e[:, iz]) * d) / self.k0

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
