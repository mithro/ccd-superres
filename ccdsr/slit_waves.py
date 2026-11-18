"""Wave calculation: a slit in a metal film held close over fine lines.

This is the wave check of the slit mask of the routes study
(``docs/research/ordinary-light-routes.md``, route B). It is a cross-section,
so everything runs unchanged along the third direction, the slit lies along
the lines, and the picture repeats sideways every ``cell_nm`` (one slit per
repeat, close to one slit per pixel). From the lamp upward the layers are:

* glass, standing for the chip's insulating layers, in which a plane wave
  travels up from a lamp behind the chip;
* metal lines set into the top of the glass, flush with its surface;
* an air gap;
* a metal film with one slit, lying on the sensor's silicon;
* silicon, where the light that arrives is counted as the reading.

The field is found with :func:`ccdsr.fdfd.solve_periodic`, which solves
Maxwell's equations up to the grid spacing. Moving the lines sideways under
the slit and recording the reading gives what a scan would record.

Polarisation "p" has the electric field across the lines and the slit; "s"
has it along them. Lengths are in nanometres.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path

import numpy as np

from .backlight import silicon_nk
from .fdfd import solve_periodic

_DATA = Path(__file__).resolve().parent / "data"
_METAL_FILES = {"aluminium": "aluminium_rakic1995.csv", "copper": "copper_johnson1972.csv"}
GLASS = 1.46          #: silica between the wires of a chip, visible to near-infrared (Malitson 1965: 1.45 to 1.47)


@lru_cache(maxsize=None)
def _metal_table(name):
    rows = np.loadtxt(_DATA / _METAL_FILES[name], delimiter=",", comments="#", skiprows=7)
    return rows[:, 0] * 1000.0, rows[:, 1], rows[:, 2]


def metal_index(name, wavelength_nm):
    """Complex refractive index of "aluminium" or "copper" at one wavelength.

    Interpolated from the tables in ``ccdsr/data`` (Rakic 1995 for aluminium
    films, Johnson and Christy 1972 for copper), 300 nm to 1500 nm.
    """
    if name not in _METAL_FILES:
        raise ValueError(f"metal is one of {sorted(_METAL_FILES)}, not {name!r}")
    w, n, k = _metal_table(name)
    if not w[0] <= wavelength_nm <= w[-1]:
        raise ValueError(f"wavelength outside the table ({w[0]:.0f} nm to {w[-1]:.0f} nm)")
    return complex(np.interp(wavelength_nm, w, n), np.interp(wavelength_nm, w, k))


def silicon_index(wavelength_nm):
    """Complex refractive index of silicon (Green 2008, as in ``ccdsr.backlight``)."""
    n, k = silicon_nk(wavelength_nm)
    return complex(n, k)


@dataclass(frozen=True)
class SlitCase:
    """One cross-section. Every length is in nanometres."""

    wavelength_nm: float = 1050.0
    polarisation: str = "p"            #: "p": electric field across the slit; "s": along it
    gap_nm: float = 50.0               #: air between the top of the lines and the film
    slit_nm: float = 100.0             #: width of the slit; 0 for an unbroken film
    film_nm: float = 50.0              #: thickness of the film; 0 for no film (an open pixel)
    period_nm: float | None = 200.0    #: repeat of the lines; None for no lines
    line_nm: float | None = None       #: width of each line; half the period if None
    line_thickness_nm: float = 100.0
    single_line: bool = False          #: one line per cell instead of a row of them
    shift_nm: float = 0.0              #: sideways position of a line's centre from the slit's centre
    angle_deg: float = 0.0             #: direction of the lamp's light in the glass, from straight up
    cell_nm: float = 1200.0            #: sideways repeat of the whole picture
    spacing_nm: float = 2.5            #: grid spacing
    film_metal: str | complex = "aluminium"
    line_metal: str | complex = "copper"
    glass_index: float = GLASS
    #: Glass between the lamp side's absorbing layer and the lines, silicon
    #: between the film and the far absorbing layer, and the thickness of
    #: the absorbing layers in grid cells. The defaults are checked for a
    #: 1,200 nm cell with light straight on (answers within 0.2 %). Other
    #: cells and slanted light can send light out at shallow angles, which
    #: needs more room: use ``roomy()``.
    below_nm: float = 300.0
    above_nm: float = 150.0
    pml_cells: int = 40

    def roomy(self):
        """The same case with deeper buffers and absorbing layers, safe for any cell and angle tried."""
        return replace(self, below_nm=600.0, above_nm=600.0, pml_cells=int(round(200.0 / self.spacing_nm)))

    def index_of(self, metal):
        return metal_index(metal, self.wavelength_nm) if isinstance(metal, str) else complex(metal)


@dataclass(frozen=True)
class Layout:
    """Where things are on the grid of one case."""

    eps: np.ndarray        #: square of the refractive index, shape (nx, nz)
    source_row: int
    reading_row: int       #: row in the silicon where the light is counted
    surface_row: int       #: first row of the air gap
    film_rows: tuple       #: first row of the film and first row of silicon
    x_nm: np.ndarray       #: sideways position of each column, zero at the slit's centre


def _cells(length_nm, spacing_nm):
    n = length_nm / spacing_nm
    if abs(n - round(n)) > 1e-6:
        raise ValueError(f"{length_nm} nm is not a whole number of grid cells of {spacing_nm} nm")
    return int(round(n))


def layout(case):
    """Lay the materials of ``case`` on the grid."""
    h = case.spacing_nm
    nx = _cells(case.cell_nm, h)
    n_below, n_line = _cells(case.below_nm, h), _cells(case.line_thickness_nm, h)
    n_gap, n_film, n_above = _cells(case.gap_nm, h), _cells(case.film_nm, h), _cells(case.above_nm, h)
    z0 = case.pml_cells + n_below                 # first row of the lines
    z1 = z0 + n_line                              # first row of the air gap
    z2 = z1 + n_gap                               # first row of the film
    z3 = z2 + n_film                              # first row of silicon
    nz = z3 + n_above + case.pml_cells
    x = (np.arange(nx) + 0.5) * h - case.cell_nm / 2

    eps = np.empty((nx, nz), dtype=complex)
    eps[:, :z1] = case.glass_index**2
    eps[:, z1:z2] = 1.0
    eps[:, z2:z3] = case.index_of(case.film_metal) ** 2
    eps[:, z3:] = silicon_index(case.wavelength_nm) ** 2

    slit = np.abs(x) < case.slit_nm / 2
    eps[slit, z2:z3] = 1.0

    if case.period_nm is not None:
        width = case.period_nm / 2 if case.line_nm is None else case.line_nm
        repeat = case.cell_nm if case.single_line else case.period_nm
        if abs(case.cell_nm / repeat - round(case.cell_nm / repeat)) > 1e-9:
            raise ValueError("the cell must hold a whole number of periods")
        _cells(case.shift_nm, h)                  # a shift off the grid would change the lines' width
        offset = (x - case.shift_nm + repeat / 2) % repeat - repeat / 2
        eps[np.abs(offset) < width / 2, z0:z1] = case.index_of(case.line_metal) ** 2

    return Layout(eps=eps, source_row=case.pml_cells + 8, reading_row=z3 + 3, surface_row=z1,
                  film_rows=(z2, z3), x_nm=x)


def _source(case, shape, row):
    """Unit source row launching a plane wave at the case's angle, and the phase step across one cell."""
    k0 = 2 * np.pi / case.wavelength_nm
    kx = k0 * case.glass_index * np.sin(np.radians(case.angle_deg))
    x = np.arange(shape[0]) * case.spacing_nm
    source = np.zeros(shape, dtype=complex)
    source[:, row] = np.exp(1j * kx * x)
    return source, kx * shape[0] * case.spacing_nm


@lru_cache(maxsize=None)
def _arriving(wavelength_nm, spacing_nm, polarisation, glass_index, pml_cells, angle_deg, cell_nm):
    """Power per unit width sent upward by the unit source row in plain glass."""
    case = SlitCase(wavelength_nm=wavelength_nm, spacing_nm=spacing_nm, glass_index=glass_index,
                    angle_deg=angle_deg, cell_nm=cell_nm)
    nx = _cells(cell_nm, spacing_nm) if angle_deg else 2
    nz = 2 * pml_cells + 60
    eps = np.full((nx, nz), glass_index**2, dtype=complex)
    source, phase = _source(case, eps.shape, pml_cells + 8)
    field = solve_periodic(eps, source, wavelength_nm, spacing_nm, pml_cells, polarisation, phase)
    return float(np.mean(field.flow_z(nz - pml_cells - 10)))


def solve_case(case):
    """Field of one case. Returns ``(field, layout)``."""
    lay = layout(case)
    source, phase = _source(case, lay.eps.shape, lay.source_row)
    field = solve_periodic(lay.eps, source, case.wavelength_nm, case.spacing_nm, case.pml_cells,
                           case.polarisation, phase)
    return field, lay


def _arriving_for(case):
    return _arriving(case.wavelength_nm, case.spacing_nm, case.polarisation, case.glass_index,
                     case.pml_cells, case.angle_deg, case.cell_nm)


def reading(case):
    """Share of the lamp's light falling on one cell that enters the silicon.

    The light is counted three grid rows inside the silicon, over the whole
    cell, and divided by what the same lamp sends through plain glass. An
    open pixel on bare silicon under plain glass and a 50 nm gap scores
    0.56 to 0.79, depending on the colour; the rest is reflected.
    """
    field, lay = solve_case(case)
    return float(np.mean(field.flow_z(lay.reading_row))) / _arriving_for(case)


def balance(case):
    """Where the lamp's light goes: shares reflected, entering the silicon, and absorbed on the way.

    The three add to 1 when the calculation conserves energy, which the
    tests check.
    """
    field, lay = solve_case(case)
    arriving = _arriving_for(case)
    up = float(np.mean(field.flow_z(lay.source_row + 6))) / arriving       # arriving minus reflected
    into = float(np.mean(field.flow_z(lay.reading_row))) / arriving
    return {"reflected": 1 - up, "into_silicon": into, "absorbed": up - into}


def default_shifts(period_nm, steps=4, spacing_nm=2.5):
    """Line positions from "line under the slit" to "space under the slit".

    With light arriving straight on, the picture is symmetric about the
    slit, so half a period is enough. At least ``steps`` equal steps are
    used, and more if that is needed for every position to fall on the grid.
    """
    while abs(period_nm / 2 / steps / spacing_nm - round(period_nm / 2 / steps / spacing_nm)) > 1e-9:
        steps += 1
        if steps > 64:
            raise ValueError("half the period is not a whole number of grid cells")
    return np.linspace(0.0, period_nm / 2, steps + 1)


@dataclass(frozen=True)
class ScanResult:
    """Readings as the lines move under the slit.

    ``shifts_nm`` either runs from 0 to half a period with both ends
    included (the other half is the mirror image), or covers a whole period
    in equal steps without repeating the first position.
    """

    case: SlitCase
    shifts_nm: np.ndarray
    readings: np.ndarray

    def _whole_period(self):
        s, r = self.shifts_nm, self.readings
        if np.isclose(s[-1], self.case.period_nm / 2):
            s = np.concatenate([s, self.case.period_nm - s[-2:0:-1]])
            r = np.concatenate([r, r[-2:0:-1]])
        return s, r

    @property
    def mean(self):
        """Reading averaged over one period of the lines."""
        return float(np.mean(self._whole_period()[1]))

    @property
    def _first(self):
        s, r = self._whole_period()
        return 2 * np.mean(r * np.exp(-2j * np.pi * s / self.case.period_nm))

    @property
    def swing(self):
        """Strength of the lines in the readings.

        Amplitude of the part of the readings that repeats once per period
        of the lines, divided by the mean: 0 when the slit does not see the
        lines, and 1 when the reading swings between zero and twice its
        mean.
        """
        return float(abs(self._first) / self.mean)

    @property
    def brightest_over(self):
        """"space" or "line": which of the two under the slit gives the higher reading."""
        return "space" if self._first.real < 0 else "line"


def scan(case, shifts_nm=None):
    """Readings of ``case`` with the lines at each of ``shifts_nm``."""
    if case.period_nm is None:
        raise ValueError("a scan needs lines")
    if shifts_nm is None:
        shifts_nm = (default_shifts(case.period_nm, spacing_nm=case.spacing_nm) if case.angle_deg == 0
                     else np.arange(8) * case.period_nm / 8)
    shifts = np.asarray(shifts_nm, dtype=float)
    return ScanResult(case=case, shifts_nm=shifts,
                      readings=np.array([reading(replace(case, shift_nm=float(s))) for s in shifts]))


def fade_length_nm(period_nm, wavelength_nm):
    """Fade length of the simple model: the gap over which the lines' strength falls by e.

    The same expression as ``ccdsr.near_contact.fade_length_nm`` for air.
    """
    k2 = 1 / period_nm**2 - 1 / wavelength_nm**2
    return float("inf") if k2 <= 0 else 1 / (2 * np.pi * np.sqrt(k2))


def fitted_fade_length_nm(gaps_nm, swings):
    """Fade length that best fits ``|swing| = a * exp(-gap / length)`` (a straight-line fit to the logarithm)."""
    slope, _ = np.polyfit(np.asarray(gaps_nm, dtype=float), np.log(np.abs(swings)), 1)
    return float(-1 / slope)
