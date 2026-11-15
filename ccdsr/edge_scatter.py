"""Wave calculation: a feature on the chip under skimming light in the slot.

One mode of the slot (see ``ccdsr/slot_modes.py``) is launched along a short
length of slot with the small wave solver of ``ccdsr/fdfd.py``. A line of
material standing on the chip is put in its way, and the light absorbed by
the sensor is recorded along the slot, with and without the line. The
difference shows what a pixel would see of the line: how much light the
line throws up into the sensor, over what width, and how deep a shadow it
leaves further in.

Two dimensions, one polarisation (field along the line), one wavelength,
flat surfaces, stair-stepped materials. Lengths are in nanometres.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .fdfd import solve
from .light_entry import ALUMINIUM, SILICON


@dataclass
class ScatterResult:
    """Light absorbed by the sensor along the slot, with and without a feature."""

    x_nm: np.ndarray            #: position along the slot, measured from the feature's centre
    bare: np.ndarray            #: light entering the sensor per unit length, no feature
    with_feature: np.ndarray    #: the same with the feature in place
    arriving: float             #: power travelling in the slot just before the feature, no feature
    gap_nm: float

    @property
    def change(self):
        """Extra light entering the sensor because of the feature."""
        return self.with_feature - self.bare

    def thrown_up(self, half_width_nm=None):
        """Share of the arriving power that the feature sends into the sensor
        within ``half_width_nm`` of itself (default: one gap either side)."""
        half = self.gap_nm if half_width_nm is None else half_width_nm
        near = np.abs(self.x_nm) <= half
        step = self.x_nm[1] - self.x_nm[0]
        return float(np.sum(self.change[near]) * step / self.arriving)

    def ratio(self, pixel_nm=1120.0):
        """Reading with the feature divided by the reading without it, each
        averaged over one pixel width."""
        return _smooth(self.with_feature, self.x_nm, pixel_nm) / _smooth(self.bare, self.x_nm, pixel_nm)

    def _inside(self, pixel_nm=1120.0):
        # leave out the ends, where the pixel average runs off the data
        return np.abs(self.x_nm - self.x_nm.mean()) <= (np.ptp(self.x_nm) / 2 - pixel_nm)

    def peak_ratio(self):
        """Largest value of :meth:`ratio` along the run."""
        return float(np.max(self.ratio()[self._inside()]))

    def peak_offset_nm(self):
        """Where that largest value is, measured from the feature (positive
        is further in, away from the lit edge)."""
        keep = self._inside()
        return float(self.x_nm[keep][np.argmax(self.ratio()[keep])])

    def extent_nm(self, threshold=0.1):
        """Length of slot over which the reading differs from the bare
        reading by more than ``threshold`` (as a share). Returns the first
        and last such positions; the run may be too short to contain the
        whole of it."""
        keep = self._inside()
        differs = np.where(keep & (np.abs(self.ratio() - 1) > threshold))[0]
        if differs.size == 0:
            return (float("nan"), float("nan"))
        return (float(self.x_nm[differs[0]]), float(self.x_nm[differs[-1]]))


def _smooth(values, x_nm, width_nm):
    cells = max(1, int(round(width_nm / (x_nm[1] - x_nm[0]))))
    return np.convolve(values, np.ones(cells) / cells, mode="same")


def run(gap_nm=5000.0, height_nm=300.0, width_nm=1000.0, material=ALUMINIUM, mode=1,
        wavelength_nm=550.0, spacing_nm=20.0, before_nm=18000.0, after_nm=20000.0,
        chip=SILICON, sensor=SILICON):
    """Launch slot mode ``mode`` at a line of ``material`` standing on the chip.

    The line is ``width_nm`` wide and ``height_nm`` high. ``before_nm`` is
    the run of slot between the launch point and the line, ``after_nm`` the
    run beyond it.
    """
    dx = spacing_nm
    pml = int(round(800 / dx))
    skin = int(round(300 / dx))                 # silicon kept each side, before the absorbing layer
    ng = int(round(gap_nm / dx))
    lead = int(round(2000 / dx))
    nx = 2 * pml + lead + int(round((before_nm + after_nm) / dx)) + lead
    nz = ng + 2 * (skin + pml)
    z0 = pml + skin                             # first row of air
    xs = pml + lead                             # launch column
    xc = xs + int(round(before_nm / dx))        # centre of the line

    def layout(with_line):
        eps = np.empty((nx, nz), dtype=complex)
        eps[:, :z0] = complex(chip) ** 2
        eps[:, z0:z0 + ng] = 1.0
        eps[:, z0 + ng:] = complex(sensor) ** 2
        if with_line and height_nm > 0:
            half = int(round(width_nm / dx / 2))
            eps[xc - half:xc + half, z0:z0 + int(round(height_nm / dx))] = complex(material) ** 2
        return eps

    source = np.zeros((nx, nz), dtype=complex)
    across = (np.arange(ng) + 0.5) / ng
    source[xs, z0:z0 + ng] = np.sin(mode * np.pi * across) / dx

    top = z0 + ng - 2                           # row just below the sensor's surface
    columns = np.arange(xs + lead, nx - pml - lead)
    results = []
    for with_line in (False, True):
        field = solve(layout(with_line), source, wavelength_nm, dx, pml_cells=pml)
        results.append(field.flow_z(top)[columns])
        if not with_line:
            before = xc - int(round(2000 / dx))
            arriving = float(np.sum(field.flow_x(before)[z0:z0 + ng]) * dx)
    return ScatterResult(x_nm=(columns - xc) * dx, bare=results[0], with_feature=results[1],
                         arriving=arriving, gap_nm=gap_nm)
