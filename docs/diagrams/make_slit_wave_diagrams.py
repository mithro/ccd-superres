"""Generate the figures and numbers for docs/slit-waves.md.

Run from the repository root:

    python docs/diagrams/make_slit_wave_diagrams.py            # figures and tables from saved runs
    python docs/diagrams/make_slit_wave_diagrams.py --rerun    # redo the wave runs (about 1,800 solves,
                                                               # half an hour on four processor cores)

Writes SVG and PNG figures next to this file with the prefix ``slit-waves-``,
the tables of the page to ``results/slit-waves/tables.md``, and with
``--rerun`` the file ``results/slit-waves/readings.json`` that both are
made from. A rerun that is interrupted picks up where it stopped.
"""

import json
import os
import sys
from dataclasses import asdict, replace
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from ccdsr.near_contact import slit_light  # noqa: E402
from ccdsr.slit_waves import (ScanResult, SlitCase, default_shifts, fade_length_nm,  # noqa: E402
                              fitted_fade_length_nm, layout, reading, solve_case)

OUT = Path(__file__).resolve().parent
RESULTS = ROOT / "results" / "slit-waves"
READINGS = RESULTS / "readings.json"

WAVELENGTHS = (1050.0, 650.0, 450.0)
COLOUR_NAME = {1050.0: "near-infrared 1,050 nm", 650.0: "red 650 nm", 450.0: "blue 450 nm"}
GAPS = (20.0, 50.0, 100.0, 150.0, 200.0, 300.0)
REFERENCE_GAPS = GAPS
PERIODS = (120.0, 150.0, 200.0, 300.0, 400.0)
LINE_GAPS = (20.0, 50.0, 100.0, 200.0)
LINE_SHIFTS = tuple(np.arange(0.0, 601.0, 25.0))
SLANT = 30.0
WIDE = 2400.0                                   # a repeat twice as wide, to see what the repeat itself does
WIDE_SHIFTS = tuple(np.arange(0.0, 1201.0, 50.0))


def key(case):
    return json.dumps(asdict(case), sort_keys=True, default=str)


def scan_cases(case):
    shifts = default_shifts(case.period_nm) if case.angle_deg == 0 else np.arange(8) * case.period_nm / 8
    return [replace(case, shift_nm=float(s)) for s in shifts]


def study():
    """Every cross-section of the study, as a dictionary of named groups of cases."""
    groups = {"main": [], "thick-film": [], "references": [], "lines-only": [], "periods": [],
              "single-line": [], "aluminium-lines": [], "slanted": [], "fine-grid": [], "wide-cell": []}
    for lam in WAVELENGTHS:
        for pol in "ps":
            for gap in GAPS:
                for slit in (50.0, 100.0):
                    groups["main"] += scan_cases(SlitCase(lam, pol, gap, slit))
            for gap in REFERENCE_GAPS:
                small = dict(period_nm=None, cell_nm=20.0)
                groups["references"].append(SlitCase(lam, pol, gap, 0.0, 0.0, **small))        # open pixel
                for film in (50.0, 100.0):
                    groups["references"].append(SlitCase(lam, pol, gap, 0.0, film, **small))   # unbroken film
                    for slit in (50.0, 100.0, 200.0):
                        groups["references"].append(SlitCase(lam, pol, gap, slit, film, period_nm=None))
            for period in PERIODS:
                groups["lines-only"].append(SlitCase(lam, pol, 50.0, 0.0, 0.0, period_nm=period, cell_nm=period))
        for gap in GAPS:
            for slit in (50.0, 100.0):
                groups["thick-film"] += scan_cases(SlitCase(lam, "p", gap, slit, 100.0))
            for period in PERIODS:
                if period != 200.0:
                    groups["periods"] += scan_cases(SlitCase(lam, "p", gap, 50.0, period_nm=period))
            groups["aluminium-lines"] += scan_cases(SlitCase(lam, "p", gap, 50.0, line_metal="aluminium"))
            groups["slanted"] += scan_cases(SlitCase(lam, "p", gap, 50.0, angle_deg=SLANT))
        for gap in LINE_GAPS:
            groups["single-line"] += [SlitCase(lam, "p", gap, 50.0, line_nm=100.0, single_line=True, shift_nm=s)
                                      for s in LINE_SHIFTS]
        groups["wide-cell"] += scan_cases(SlitCase(lam, "p", 50.0, 50.0, cell_nm=WIDE))
        groups["wide-cell"].append(SlitCase(lam, "p", 50.0, 50.0, period_nm=None, cell_nm=WIDE))
        groups["wide-cell"] += [SlitCase(lam, "p", 50.0, 50.0, line_nm=100.0, single_line=True, shift_nm=s,
                                         cell_nm=WIDE) for s in WIDE_SHIFTS]
        for gap in (20.0, 100.0):
            groups["fine-grid"] += scan_cases(SlitCase(lam, "p", gap, 50.0, spacing_nm=1.25, pml_cells=80))
    return groups


def _one(case):
    return key(case), reading(case)


def rerun():
    from multiprocessing import Pool
    RESULTS.mkdir(parents=True, exist_ok=True)
    done = load() if READINGS.exists() else {}
    cases = {key(c): c for group in study().values() for c in group}
    todo = [c for k, c in cases.items() if k not in done]
    todo.sort(key=lambda c: c.spacing_nm, reverse=True)
    print(f"{len(cases)} cross-sections, {len(todo)} to run", flush=True)
    with Pool(4) as pool:
        for n, (k, value) in enumerate(pool.imap_unordered(_one, todo), start=1):
            done[k] = value
            if n % 20 == 0 or n == len(todo):
                READINGS.write_text(json.dumps(done, indent=0, sort_keys=True))
                print(f"{n} of {len(todo)}", flush=True)
    READINGS.write_text(json.dumps({k: done[k] for k in sorted(cases)}, indent=0))


def load():
    return json.loads(READINGS.read_text())


# ---------------------------------------------------------------- reading the saved runs

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#dddcd6"
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
YELLOW = "#eda100"
VIOLET = "#7a5bd6"
COLOUR = {1050.0: "#8c2d19", 650.0: "#d6402a", 450.0: BLUE}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "text.color": INK,
    "axes.labelcolor": INK2, "axes.edgecolor": INK2, "xtick.color": INK2,
    "ytick.color": INK2, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "svg.fonttype": "path",
})


class Runs:
    def __init__(self):
        self.data = load()

    def reading(self, case):
        return self.data[key(case)]

    def scan(self, case):
        cases = scan_cases(case)
        return ScanResult(case, np.array([c.shift_nm for c in cases]),
                          np.array([self.reading(c) for c in cases]))


def simple_swing(period_nm, slit_nm, gap_nm, wavelength_nm):
    """Swing of the simple model: black and clear stripes, faded by the gap, averaged over the slit.

    Stripes of equal width have a once-per-period part 4 / pi times their
    mean; the gap multiplies it by exp(-gap / fade length); a slit of width
    w averages it by sin(pi w / p) / (pi w / p).
    """
    return 4 / np.pi * abs(np.sinc(slit_nm / period_nm)) * np.exp(-gap_nm / fade_length_nm(period_nm, wavelength_nm))


def readings_for_clean(swing, full_e=2500.0, times=5.0):
    """Readings spread over the lines' period for the swing to stand ``times`` above the noise.

    Each reading is taken as filled to ``full_e`` electrons, with only the
    noise of counting them (its square root). The swing fitted to N such
    readings has a noise of sqrt(2 / (N * full_e)), so N = 2 * times^2 /
    (full_e * swing^2).
    """
    return 2 * times**2 / (full_e * swing**2)


def equivalent_softness_nm(ratio, period_nm):
    """Width (full width at half maximum) of the Gaussian blur that would cut the swing by ``ratio``."""
    if ratio >= 1:
        return 0.0
    return 2.3548 * period_nm * np.sqrt(np.log(1 / ratio) / (2 * np.pi**2))


def num(x, digits=2):
    """A number for a table: plain when it reads easily, otherwise as a power of ten."""
    if x == 0:
        return "0"
    if abs(x) >= 0.001:
        places = max(0, digits - 1 - int(np.floor(np.log10(abs(x)))))
        return f"{x:,.{places}f}"
    exponent = int(np.floor(np.log10(abs(x))))
    mantissa = x / 10**exponent
    if round(mantissa, digits - 1) >= 10:
        mantissa, exponent = mantissa / 10, exponent + 1
    return f"{mantissa:.{digits - 1}f} × 10{str(exponent).translate(str.maketrans('-0123456789', '⁻⁰¹²³⁴⁵⁶⁷⁸⁹'))}"


def table(header, rows, align=None):
    align = align or ["---"] + ["--:"] * (len(header) - 1)
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join(align) + "|"]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def tables(runs):
    out = []
    pitch = 1200.0

    # 1. light without lines
    rows = []
    for lam in WAVELENGTHS:
        for label, kw in [("Open pixel, no film", dict(slit_nm=0.0, film_nm=0.0, cell_nm=20.0)),
                          ("Unbroken film 50 nm", dict(slit_nm=0.0, film_nm=50.0, cell_nm=20.0)),
                          ("Unbroken film 100 nm", dict(slit_nm=0.0, film_nm=100.0, cell_nm=20.0)),
                          ("Slit 50 nm, film 50 nm", dict(slit_nm=50.0, film_nm=50.0)),
                          ("Slit 100 nm, film 50 nm", dict(slit_nm=100.0, film_nm=50.0)),
                          ("Slit 200 nm, film 50 nm", dict(slit_nm=200.0, film_nm=50.0)),
                          ("Slit 50 nm, film 100 nm", dict(slit_nm=50.0, film_nm=100.0)),
                          ("Slit 100 nm, film 100 nm", dict(slit_nm=100.0, film_nm=100.0)),
                          ("Slit 200 nm, film 100 nm", dict(slit_nm=200.0, film_nm=100.0))]:
            def r(pol, gap=50.0):
                return runs.reading(SlitCase(lam, pol, gap, period_nm=None, **kw))
            open_pixel = 0.5 * sum(runs.reading(SlitCase(lam, pol, 50.0, 0.0, 0.0, period_nm=None, cell_nm=20.0))
                                   for pol in "ps")
            both = 0.5 * (r("p") + r("s"))
            spread = [0.5 * (r("p", g) + r("s", g)) for g in REFERENCE_GAPS]
            simple = "" if kw["slit_nm"] == 0 else num(slit_light(kw["slit_nm"], pitch), 2)
            rows.append([COLOUR_NAME[lam], label, num(r("p")), num(r("s")), num(both), num(both / open_pixel),
                         simple, f"{num(min(spread))} to {num(max(spread))}"])
    out.append(("light", table(["Light", "Arrangement", "Field across the slit (p)", "Field along the slit (s)",
                                "Lamp of both kinds", "As a share of the open pixel", "Simple estimate of that share",
                                "Both kinds, over gaps of 20 nm to 300 nm"], rows, ["---", "---"] + ["--:"] * 6)))

    # 2. the main result
    rows = []
    for lam in WAVELENGTHS:
        for slit in (50.0, 100.0):
            for gap in GAPS:
                s = runs.scan(SlitCase(lam, "p", gap, slit))
                simple = simple_swing(200.0, slit, gap, lam)
                rows.append([COLOUR_NAME[lam], f"{slit:.0f}", f"{gap:.0f}", num(s.mean), num(s.swing),
                             num(simple), num(s.swing / simple), s.brightest_over,
                             num(readings_for_clean(s.swing))])
    out.append(("main", table(["Light", "Slit (nm)", "Gap (nm)", "Reading, mean over the lines", "Swing, wave calculation",
                               "Swing, simple model", "Wave over simple", "Reading is highest over a",
                               "Readings for the lines to stand 5 times above the noise"],
                              rows, ["---", "--:", "--:", "--:", "--:", "--:", "--:", "---", "--:"])))

    # 3. fade lengths
    rows = []
    for lam in WAVELENGTHS:
        for period in PERIODS:
            swings = [runs.scan(SlitCase(lam, "p", g, 50.0, period_nm=period)).swing for g in GAPS]
            use = [i for i, g in enumerate(GAPS) if g <= 150.0]
            fitted = fitted_fade_length_nm([GAPS[i] for i in use], [swings[i] for i in use])
            simple = fade_length_nm(period, lam)
            rows.append([COLOUR_NAME[lam], f"{period / 2:.0f}", f"{period:.0f}", num(simple, 3), num(fitted, 3),
                         num(fitted / simple)] + [num(v) for v in swings])
    out.append(("fade", table(["Light", "Line width (nm)", "Period (nm)", "Fade length, simple model (nm)",
                               "Fade length, fitted to the wave calculation at gaps to 150 nm (nm)", "Ratio"]
                              + [f"Swing at {g:.0f} nm" for g in GAPS], rows, ["---"] + ["--:"] * 11)))

    # 4. the other polarisation and the lamp of both kinds
    rows = []
    for lam in WAVELENGTHS:
        for gap in GAPS:
            p, s = runs.scan(SlitCase(lam, "p", gap, 50.0)), runs.scan(SlitCase(lam, "s", gap, 50.0))
            both = ScanResult(p.case, p.shifts_nm, 0.5 * (p.readings + s.readings))
            rows.append([COLOUR_NAME[lam], f"{gap:.0f}", num(p.mean), num(s.mean), num(s.mean / p.mean),
                         num(p.swing), num(s.swing), num(both.swing)])
    out.append(("polarisation", table(["Light", "Gap (nm)", "Reading, field across (p)", "Reading, field along (s)",
                                       "s over p", "Swing, p", "Swing, s", "Swing, lamp of both kinds"], rows,
                                      ["---"] + ["--:"] * 7)))

    # 5. light through the lines alone
    rows = []
    for lam in WAVELENGTHS:
        for period in PERIODS:
            p, s = (runs.reading(SlitCase(lam, pol, 50.0, 0.0, 0.0, period_nm=period, cell_nm=period)) for pol in "ps")
            rows.append([COLOUR_NAME[lam], f"{period / 2:.0f}", num(p), num(s), num(p / s)])
    out.append(("lines-only", table(["Light", "Line and space width (nm)", "Field across the lines (p)",
                                     "Field along the lines (s)", "p over s"], rows)))

    # 6. variations
    rows = []
    for lam in WAVELENGTHS:
        for gap in GAPS:
            base = runs.scan(SlitCase(lam, "p", gap, 50.0))
            thick = runs.scan(SlitCase(lam, "p", gap, 50.0, 100.0))
            alu = runs.scan(SlitCase(lam, "p", gap, 50.0, line_metal="aluminium"))
            slant = runs.scan(SlitCase(lam, "p", gap, 50.0, angle_deg=SLANT))
            rows.append([COLOUR_NAME[lam], f"{gap:.0f}"] + [f"{num(x.mean)} / {num(x.swing)}"
                                                           for x in (base, thick, alu, slant)])
    out.append(("variations", table(["Light", "Gap (nm)", "Baseline", "Film 100 nm thick", "Aluminium lines",
                                     f"Light slanted {SLANT:.0f}° in the glass"], rows)))

    # 7. grid check
    rows = []
    for lam in WAVELENGTHS:
        for gap in (20.0, 100.0):
            coarse = runs.scan(SlitCase(lam, "p", gap, 50.0))
            fine = runs.scan(SlitCase(lam, "p", gap, 50.0, spacing_nm=1.25, pml_cells=80))
            rows.append([COLOUR_NAME[lam], f"{gap:.0f}", num(coarse.mean, 3), num(fine.mean, 3),
                         f"{100 * (coarse.mean / fine.mean - 1):+.1f} %", num(coarse.swing, 3), num(fine.swing, 3),
                         f"{100 * (coarse.swing / fine.swing - 1):+.1f} %"])
    out.append(("grid", table(["Light", "Gap (nm)", "Reading, grid 2.5 nm", "Reading, grid 1.25 nm", "Difference",
                               "Swing, grid 2.5 nm", "Swing, grid 1.25 nm", "Difference"], rows)))

    # 7b. a repeat twice as wide
    rows = []
    for lam in WAVELENGTHS:
        narrow, wide = runs.scan(SlitCase(lam, "p", 50.0, 50.0)), runs.scan(SlitCase(lam, "p", 50.0, 50.0, cell_nm=WIDE))
        x, change = line_response(runs, lam, 50.0)
        xw, change_w = line_response(runs, lam, 50.0, WIDE)
        rows.append([COLOUR_NAME[lam], num(narrow.mean * 1200.0, 3), num(wide.mean * WIDE, 3), num(narrow.swing, 3),
                     num(wide.swing, 3), f"{100 * change[0]:+.0f} %", f"{100 * change_w[0]:+.0f} %",
                     num(width_at_half(x, change), 3), num(width_at_half(xw, change_w), 3)])
    out.append(("wide-cell", table(["Light", "Light through one slit, repeat 1,200 nm (nm of width)",
                                    "The same, repeat 2,400 nm", "Swing, repeat 1,200 nm", "Swing, repeat 2,400 nm",
                                    "One line under the slit, repeat 1,200 nm", "The same, repeat 2,400 nm",
                                    "Width of the response, repeat 1,200 nm (nm)", "The same, repeat 2,400 nm"],
                                   rows)))

    # 8. one line
    rows = []
    for lam in WAVELENGTHS:
        for gap in LINE_GAPS:
            x, change = line_response(runs, lam, gap)
            peak = change[np.argmax(np.abs(change))]
            rows.append([COLOUR_NAME[lam], f"{gap:.0f}", f"{100 * change[0]:+.1f} %", f"{100 * peak:+.1f} %",
                         f"{x[np.argmax(np.abs(change))]:.0f}", num(width_at_half(x, change), 3)])
    out.append(("single-line", table(["Light", "Gap (nm)", "Change in reading, line under the slit",
                                      "Largest change", "Line's distance from the slit at the largest change (nm)",
                                      "Full width at half of the change under the slit (nm)"], rows)))

    text = "\n\n".join(f"### {name}\n\n{body}" for name, body in out) + "\n"
    (RESULTS / "tables.md").write_text(text)
    return text


def line_response(runs, lam, gap, cell=1200.0):
    """Relative change in the reading against the position of one 100 nm line."""
    shifts = LINE_SHIFTS if cell == 1200.0 else WIDE_SHIFTS
    base = runs.reading(SlitCase(lam, "p", gap, 50.0, period_nm=None, cell_nm=cell))
    r = np.array([runs.reading(SlitCase(lam, "p", gap, 50.0, line_nm=100.0, single_line=True, shift_nm=s,
                                        cell_nm=cell)) for s in shifts])
    return np.array(shifts), r / base - 1


def width_at_half(x, change):
    """Full width of the response around zero shift at half its central value (the response is symmetric)."""
    target = change[0] / 2
    for i in range(1, len(x)):
        if (change[i] - target) * (change[0] - target) <= 0:
            x0, x1, c0, c1 = x[i - 1], x[i], change[i - 1], change[i]
            return 2 * (x0 + (target - c0) * (x1 - x0) / (c1 - c0))
    return float("nan")


# ---------------------------------------------------------------- figures

def save(fig, name):
    for ext in ("svg", "png"):
        fig.savefig(OUT / f"slit-waves-{name}.{ext}", dpi=160, bbox_inches="tight")
    plt.close(fig)


def tidy(ax):
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


MATERIAL = {"glass": "#cfe3f1", "air": "#ffffff", "silicon": "#b9b7c6", "film": "#8d99a6", "line": "#c9813a"}


def figure_layout():
    from matplotlib.patches import Rectangle
    fig, ax = plt.subplots(figsize=(9.2, 4.3))
    gap, film, thick, slit, period = 50.0, 50.0, 100.0, 50.0, 200.0
    ax.add_patch(Rectangle((-600, -330), 1200, 330, color=MATERIAL["glass"]))
    for m in range(-3, 4):
        left = max(-600.0, m * period - 50)
        right = min(600.0, m * period + 50)
        ax.add_patch(Rectangle((left, -thick), right - left, thick, color=MATERIAL["line"]))
    ax.add_patch(Rectangle((-600, gap), 1200, film, color=MATERIAL["film"]))
    ax.add_patch(Rectangle((-slit / 2, gap), slit, film, color=MATERIAL["air"]))
    ax.add_patch(Rectangle((-600, gap + film), 1200, 180, color=MATERIAL["silicon"]))
    ax.plot([-600, 600], [0, 0], color=INK2, linewidth=0.6)
    for x in (-520, -330, 330, 520):
        ax.annotate("", xy=(x, -215), xytext=(x, -315), arrowprops=dict(arrowstyle="-|>", color=YELLOW, lw=2.2))
    ax.text(0, -265, "light from a lamp behind the chip", ha="center", va="center", color=INK, fontsize=10)
    ax.text(-585, -165, "glass of the chip", ha="left", va="center", color=INK, fontsize=10)
    ax.text(-585, gap + film + 110, "silicon of the sensor: light arriving here is the reading", ha="left",
            va="center", color=INK, fontsize=10)
    ax.text(330, gap + film / 2, "metal film (aluminium)", ha="center", va="center", color="white", fontsize=9.5)
    ax.annotate("slit, 50 nm or 100 nm", xy=(0, gap + film / 2), xytext=(-330, gap + film / 2), ha="center",
                va="center", color="white", fontsize=9.5, arrowprops=dict(arrowstyle="-", color="white", lw=0.8))
    ax.annotate("air gap,\n20 nm to 300 nm", xy=(500, gap / 2), xytext=(690, gap / 2), ha="left", va="center",
                fontsize=9.5, arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8), annotation_clip=False)
    ax.annotate("copper lines 100 nm wide\nand 100 nm thick, 200 nm apart\ncentre to centre", xy=(600, -50),
                xytext=(690, -70), ha="left", va="center", fontsize=9.5,
                arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8), annotation_clip=False)
    ax.annotate("", xy=(40, -125), xytext=(160, -125), arrowprops=dict(arrowstyle="<|-|>", color=INK, lw=1.2))
    ax.text(100, -150, "the lines are moved\nsideways under the slit", ha="center", va="top", fontsize=9)
    ax.plot([-600, -400], [-360, -360], color=INK, lw=2)
    ax.text(-500, -385, "200 nm", ha="center", va="top", fontsize=9)
    ax.text(0, -385, "one repeat of the picture: 1,200 nm, about one pixel", ha="center", va="top", fontsize=9,
            color=INK2)
    ax.set_xlim(-610, 610)
    ax.set_ylim(-420, gap + film + 185)
    ax.set_aspect("equal")
    ax.axis("off")
    save(fig, "layout")


def figure_field():
    """Strength of the magnetic field with a line and with a space under the slit, in two colours."""
    from ccdsr.slit_waves import _arriving_for
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 5.6), sharex=True, sharey=True, constrained_layout=True)
    for row, lam in enumerate((1050.0, 650.0)):
        fields = []
        for shift in (0.0, 100.0):
            case = SlitCase(lam, "p", 50.0, 50.0, shift_nm=shift)
            field, lay = solve_case(case)
            # a wave of magnetic strength H in the glass carries H^2 / index
            arriving = np.sqrt(_arriving_for(case) * case.glass_index)
            fields.append((np.abs(field.e) / arriving, lay, case))
        for col, (strength, lay, case) in enumerate(fields):
            ax = axes[row, col]
            h = case.spacing_nm
            z = (np.arange(strength.shape[1]) - lay.surface_row) * h
            keep = (z > -330) & (z < 220)
            image = ax.imshow(strength[:, keep].T, origin="lower", cmap="magma", vmin=0, vmax=2.5,
                              extent=(lay.x_nm[0] - h / 2, lay.x_nm[-1] + h / 2, z[keep][0], z[keep][-1] + h),
                              aspect="equal", interpolation="nearest")
            metal = (np.abs(lay.eps.imag) > 1.0) | (lay.eps.real < 0)
            ax.contour(lay.x_nm, z[keep] + h / 2, metal[:, keep].T.astype(float), levels=[0.5], colors="white",
                       linewidths=0.7)
            z_si = (lay.film_rows[1] - lay.surface_row) * h
            ax.axhline(z_si, color="white", linewidth=0.5, linestyle=":")
            where = "a line" if col == 0 else "a space"
            ax.set_title(f"{COLOUR_NAME[lam].capitalize()}, {where} under the slit", fontsize=10, loc="left")
            if col == 0:
                ax.set_ylabel("Height above the\nchip's surface (nm)")
            if row == 1:
                ax.set_xlabel("Position across the lines (nm)")
    fig.colorbar(image, ax=axes, shrink=0.7, pad=0.02, extend="max",
                 label="Strength of the magnetic field (arriving wave = 1)")
    save(fig, "field")


def figure_swing(runs):
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.9), sharey=True)
    gaps = np.array(GAPS)
    fine = np.linspace(20, 300, 100)
    for ax, lam in zip(axes, WAVELENGTHS):
        for slit, colour, marker in ((50.0, BLUE, "o"), (100.0, ORANGE, "s")):
            swings = [runs.scan(SlitCase(lam, "p", g, slit)).swing for g in gaps]
            ax.plot(gaps, swings, marker=marker, color=colour, linewidth=1.8, markersize=5,
                    label=f"Wave calculation, slit {slit:.0f} nm")
            ax.plot(fine, simple_swing(200.0, slit, fine, lam), color=colour, linewidth=1.2, linestyle="--",
                    label=f"Simple model, slit {slit:.0f} nm")
        ax.set_yscale("log")
        ax.set_ylim(1e-4, 2)
        ax.set_title(COLOUR_NAME[lam].capitalize(), fontsize=10, loc="left")
        ax.set_xlabel("Gap between the lines and the film (nm)")
        tidy(ax)
    axes[0].set_ylabel("Swing of the reading as the lines pass\n(share of the mean reading)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, fontsize=9, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.09))
    save(fig, "swing")


def figure_light(runs):
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.9))
    gaps = np.array(GAPS)
    for ax, slit in zip(axes, (50.0, 100.0)):
        for lam in WAVELENGTHS:
            means = [runs.scan(SlitCase(lam, "p", g, slit)).mean for g in gaps]
            ax.plot(gaps, means, marker="o", color=COLOUR[lam], linewidth=1.8, markersize=5,
                    label=f"Over the lines, {COLOUR_NAME[lam]}")
            bare = [runs.reading(SlitCase(lam, "p", g, slit, period_nm=None)) for g in REFERENCE_GAPS]
            ax.plot(REFERENCE_GAPS, bare, marker="x", color=COLOUR[lam], linewidth=1.0, linestyle=":",
                    markersize=6, label=f"Over plain glass, {COLOUR_NAME[lam]}")
        ax.axhline(slit / 1200.0, color=INK2, linewidth=1.0, linestyle="--")
        ax.text(22, 2.3e-3, "dashed: the slit's share of the area", ha="left", va="bottom",
                fontsize=8.5, color=INK2)
        ax.set_yscale("log")
        ax.set_ylim(2e-3, 0.4)
        ax.set_title(f"Slit {slit:.0f} nm wide", fontsize=10, loc="left")
        ax.set_xlabel("Gap between the lines and the film (nm)")
        tidy(ax)
    axes[0].set_ylabel("Share of the arriving light that\nreaches the silicon (field across the slit)")
    axes[1].legend(frameon=False, fontsize=8, loc="center left", bbox_to_anchor=(1.02, 0.5))
    save(fig, "light")


def figure_single_line(runs):
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.9), sharey=True)
    shades = [BLUE, AQUA, YELLOW, ORANGE]

    def both_sides(x, change):
        return np.concatenate([-x[:0:-1], x]), 100 * np.concatenate([change[:0:-1], change])

    for ax, lam in zip(axes, WAVELENGTHS):
        for gap, colour in zip(LINE_GAPS, shades):
            ax.plot(*both_sides(*line_response(runs, lam, gap)), color=colour, linewidth=1.8,
                    label=f"Gap {gap:.0f} nm")
        xw, cw = line_response(runs, lam, 50.0, WIDE)
        near = xw <= 600
        ax.plot(*both_sides(xw[near], cw[near]), color=INK, linewidth=1.1, linestyle="--",
                label="Gap 50 nm, slits twice as far apart")
        ax.axvspan(-50, 50, color=GRID, alpha=0.6, linewidth=0)
        ax.set_title(COLOUR_NAME[lam].capitalize(), fontsize=10, loc="left")
        tidy(ax)
    axes[1].set_xlabel("Position of the line's centre from the slit's centre (nm)")
    axes[0].set_ylabel("Change in the reading caused by\none line 100 nm wide (%)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, fontsize=9, loc="lower center", ncol=5, bbox_to_anchor=(0.5, -0.1))
    save(fig, "single-line")


def figure_periods(runs):
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.9), sharey=True)
    gaps = np.array(GAPS)
    shades = [VIOLET, BLUE, AQUA, YELLOW, ORANGE]
    for ax, lam in zip(axes, WAVELENGTHS):
        for period, colour in zip(PERIODS, shades):
            swings = [runs.scan(SlitCase(lam, "p", g, 50.0, period_nm=period)).swing for g in gaps]
            ax.plot(gaps, swings, marker="o", color=colour, linewidth=1.8, markersize=4.5,
                    label=f"Lines {period / 2:.0f} nm wide")
            ax.plot(gaps, simple_swing(period, 50.0, gaps, lam), color=colour, linewidth=1.0, linestyle="--")
        ax.set_yscale("log")
        ax.set_ylim(1e-5, 3)
        ax.set_title(COLOUR_NAME[lam].capitalize(), fontsize=10, loc="left")
        ax.set_xlabel("Gap between the lines and the film (nm)")
        tidy(ax)
    axes[0].set_ylabel("Swing of the reading as the lines pass\n(share of the mean reading)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, fontsize=9, loc="lower center", ncol=5, bbox_to_anchor=(0.5, -0.09))
    save(fig, "periods")


if __name__ == "__main__":
    if "--rerun" in sys.argv:
        rerun()
    runs = Runs()
    print(tables(runs))
    figure_layout()
    figure_swing(runs)
    figure_light(runs)
    figure_single_line(runs)
    figure_periods(runs)
    figure_field()
