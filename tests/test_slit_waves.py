import math
from dataclasses import replace

import numpy as np
import pytest

from ccdsr.fdfd import solve_periodic
from ccdsr.light_entry import fresnel_reflectance
from ccdsr.slit_waves import (GLASS, SlitCase, balance, default_shifts, fade_length_nm, fitted_fade_length_nm,
                              layout, metal_index, reading, scan, silicon_index)


def _through(index, angle_deg, polarisation, wavelength=550.0, h=5.0, nx=8, nz=400, pml=60):
    """Share of a plane wave in air that enters a flat material, from the wave solver."""
    k0 = 2 * np.pi / wavelength
    kx = k0 * np.sin(np.radians(angle_deg))
    source = np.zeros((nx, nz), dtype=complex)
    source[:, pml + 20] = np.exp(1j * kx * np.arange(nx) * h)
    flows = []
    for n in (1.0, index):
        eps = np.ones((nx, nz), dtype=complex)
        eps[:, nz // 2:] = n**2
        field = solve_periodic(eps, source, wavelength, h, pml, polarisation, kx * nx * h)
        flows.append(np.mean(field.flow_z(nz // 2 + 3)))
    return flows[1] / flows[0]


@pytest.mark.parametrize("polarisation", ["s", "p"])
@pytest.mark.parametrize("angle", [0.0, 30.0, 60.0])
def test_flat_glass_matches_the_textbook_reflection(polarisation, angle):
    rs, rp = fresnel_reflectance(1.46, math.radians(90 - angle))
    expected = 1 - float(rs if polarisation == "s" else rp)
    assert _through(1.46, angle, polarisation) == pytest.approx(expected, abs=2e-3)


def test_nothing_reflects_at_brewsters_angle_in_p_only():
    angle = math.degrees(math.atan(1.46))
    assert _through(1.46, angle, "p") == pytest.approx(1.0, abs=2e-3)
    assert _through(1.46, angle, "s") < 0.9


@pytest.mark.parametrize("polarisation", ["s", "p"])
def test_flat_silicon_matches_the_textbook_reflection(polarisation):
    rs, rp = fresnel_reflectance(4.08 + 0.03j, math.radians(60.0))
    expected = 1 - float(rs if polarisation == "s" else rp)
    assert _through(4.08 + 0.03j, 30.0, polarisation, h=2.5, nz=600) == pytest.approx(expected, abs=6e-3)


def test_polarisation_must_be_s_or_p():
    with pytest.raises(ValueError):
        solve_periodic(np.ones((4, 100)), np.zeros((4, 100)), 500.0, 5.0, polarisation="x")


@pytest.mark.parametrize("polarisation", ["s", "p"])
def test_fine_detail_fades_at_the_textbook_rate(polarisation):
    # A thin glass grating finer than the wavelength: above it, the part of
    # the field that repeats with the grating fades as exp(-kappa z).
    wavelength, period, h, pml = 600.0, 200.0, 2.5, 40
    nx, nz = int(period / h), 400
    eps = np.ones((nx, nz), dtype=complex)
    eps[: nx // 2, 150:158] = 1.5**2
    source = np.zeros((nx, nz), dtype=complex)
    source[:, pml + 10] = 1.0
    field = solve_periodic(eps, source, wavelength, h, pml, polarisation)
    wave = np.exp(-2j * np.pi * np.arange(nx) / nx)
    strength = np.abs(np.mean(field.e * wave[:, None], axis=0))
    kappa = 2 * np.pi * math.sqrt(1 / period**2 - 1 / wavelength**2)
    for first, second in ((165, 185), (185, 215)):
        assert strength[second] / strength[first] == pytest.approx(math.exp(-kappa * (second - first) * h), rel=0.02)
    assert fade_length_nm(period, wavelength) == pytest.approx(1 / kappa)


def _slit_array(polarisation, thickness_nm, wavelength=600.0, period=300.0, slit=50.0, h=2.5, metal=-1e4):
    """Share of light passed by a row of slits in a near-perfect metal film in air."""
    nx, pml, n_film = int(period / h), 40, int(thickness_nm / h)
    nz = 2 * pml + 160 + n_film
    z0 = pml + 80
    x = (np.arange(nx) + 0.5) * h - period / 2
    source = np.zeros((nx, nz), dtype=complex)
    source[:, pml + 10] = 1.0
    empty = np.ones((nx, nz), dtype=complex)
    eps = empty.copy()
    eps[:, z0:z0 + n_film] = metal
    eps[np.abs(x) < slit / 2, z0:z0 + n_film] = 1.0
    flows = [np.mean(solve_periodic(e, source, wavelength, h, pml, polarisation).flow_z(nz - pml - 20))
             for e in (empty, eps)]
    return flows[1] / flows[0]


def test_field_along_a_narrow_slit_is_choked():
    # With the electric field along the slit, a slit narrower than half a
    # wavelength carries no wave; the light falls as exp(-2 kappa t) with
    # kappa = sqrt((pi / width)^2 - k0^2).
    width, wavelength = 100.0, 600.0
    kappa = math.sqrt((math.pi / width) ** 2 - (2 * math.pi / wavelength) ** 2)
    thin, thick = _slit_array("s", 100.0, slit=width), _slit_array("s", 150.0, slit=width)
    # the stepped grid makes the slit's width uncertain by about one cell
    assert thick / thin == pytest.approx(math.exp(-2 * kappa * 50.0), rel=0.25)
    assert thin < 0.01


def test_field_across_a_narrow_slit_passes_and_resonates():
    # With the electric field across the slit, a perfect metal film passes
    # nearly all the light at the thicknesses where the slit resonates
    # (a little under half a wavelength), far more than the open share.
    through = {t: _slit_array("p", t) for t in (100.0, 175.0, 200.0, 225.0, 250.0, 275.0)}
    assert max(through.values()) > 0.85
    assert min(through.values()) < 0.5
    assert all(-1e-6 < v < 1 + 1e-3 for v in through.values())
    assert through[100.0] > 20 * _slit_array("s", 100.0)


@pytest.mark.parametrize("polarisation", ["s", "p"])
def test_energy_is_conserved_without_absorption(polarisation):
    # A structure of clear materials: what goes in below comes out above.
    h, pml, nx, nz = 5.0, 40, 80, 300
    eps = np.ones((nx, nz), dtype=complex)
    eps[:, :120] = 1.46**2
    eps[:25, 120:140] = 2.0**2
    eps[10:50, 150:170] = 3.0**2
    eps[:, 200:] = 1.8**2
    source = np.zeros((nx, nz), dtype=complex)
    source[:, pml + 8] = 1.0
    field = solve_periodic(eps, source, 500.0, h, pml, polarisation)
    below, above = np.mean(field.flow_z(pml + 30)), np.mean(field.flow_z(nz - pml - 20))
    assert above > 0.3 * abs(below)
    assert above == pytest.approx(below, rel=5e-3)


def test_metal_tables_give_the_published_values():
    assert metal_index("aluminium", 442.8) == pytest.approx(0.6079 + 5.3676j, rel=1e-4)
    assert metal_index("copper", 1088.0) == pytest.approx(0.36 + 7.217j, rel=1e-4)
    assert metal_index("aluminium", 1050.0) == pytest.approx(1.39 + 10.08j, rel=5e-3)
    assert silicon_index(1050.0).real == pytest.approx(3.56, abs=0.02)
    with pytest.raises(ValueError):
        metal_index("gold", 500.0)
    with pytest.raises(ValueError):
        metal_index("copper", 200.0)


def test_layout_puts_the_parts_where_the_case_says():
    case = SlitCase(spacing_nm=5.0, gap_nm=50.0, slit_nm=100.0, film_nm=50.0, shift_nm=0.0)
    lay = layout(case)
    assert lay.eps.shape[0] == 240
    np.testing.assert_allclose(lay.eps, lay.eps[::-1])                 # mirror image about the slit
    z_film, z_silicon = lay.film_rows
    assert z_silicon - z_film == 10 and z_film - lay.surface_row == 10
    film = lay.eps[:, z_film]
    assert np.sum(film == 1.0) == 20                                    # slit 100 nm wide
    assert abs(lay.x_nm[film == 1.0]).max() < 50
    lines = lay.eps[:, lay.surface_row - 1]
    metal = np.isclose(lines, metal_index("copper", 1050.0) ** 2)
    assert metal.sum() == 120 and metal[119] and metal[120]            # a line under the slit, half the cell covered
    moved = layout(replace(case, shift_nm=100.0)).eps[:, lay.surface_row - 1]
    assert not np.isclose(moved[120], lines[120])                       # now a space under the slit
    one = layout(replace(case, single_line=True)).eps[:, lay.surface_row - 1]
    assert np.isclose(one, metal_index("copper", 1050.0) ** 2).sum() == 20
    with pytest.raises(ValueError):
        layout(replace(case, gap_nm=52.0))
    with pytest.raises(ValueError):
        layout(replace(case, period_nm=250.0))


def _stack_through(n1, n2, n3, thickness, wavelength):
    """Textbook share of light passing from medium 1 through a layer of medium 2 into medium 3, straight on."""
    r12, r23 = (n1 - n2) / (n1 + n2), (n2 - n3) / (n2 + n3)
    t12, t23 = 2 * n1 / (n1 + n2), 2 * n2 / (n2 + n3)
    beta = 2 * math.pi * n2 * thickness / wavelength
    t = t12 * t23 * np.exp(1j * beta) / (1 + r12 * r23 * np.exp(2j * beta))
    return (n3.real / n1) * abs(t) ** 2


@pytest.mark.parametrize("polarisation", ["s", "p"])
@pytest.mark.parametrize("gap", [50.0, 300.0])
def test_open_pixel_matches_the_textbook_layer_formula(polarisation, gap):
    case = SlitCase(wavelength_nm=650.0, polarisation=polarisation, gap_nm=gap, film_nm=0.0, slit_nm=0.0,
                    period_nm=None, spacing_nm=2.5, cell_nm=20.0)
    # the light is counted 7.5 nm inside the silicon, which absorbs a few parts in a thousand on the way
    expected = _stack_through(1.46, 1.0, silicon_index(650.0), gap, 650.0)
    assert reading(case) == pytest.approx(expected, rel=0.01)


def test_shares_of_the_light_add_up():
    b = balance(SlitCase(spacing_nm=5.0))
    assert b["reflected"] + b["into_silicon"] + b["absorbed"] == pytest.approx(1.0)
    assert 0 < b["into_silicon"] < 0.2 and b["reflected"] > 0.5 and b["absorbed"] > 0


def test_slit_passes_the_field_across_it_and_blocks_the_field_along_it():
    case = SlitCase(wavelength_nm=1050.0, spacing_nm=5.0, period_nm=None)
    across, along = reading(case), reading(replace(case, polarisation="s"))
    film_only = reading(replace(case, slit_nm=0.0))
    assert across > 5 * along
    assert across > 20 * film_only
    assert across > 0.5 * 100.0 / 1200.0            # at least the slit's share of the area


def test_scan_over_half_a_period_equals_the_whole():
    case = SlitCase(wavelength_nm=650.0, spacing_nm=5.0, gap_nm=50.0, slit_nm=50.0)
    half, whole = scan(case), scan(case, np.arange(8) * 25.0)
    assert len(half.readings) == 5
    assert whole.mean == pytest.approx(half.mean, rel=1e-6)
    assert whole.swing == pytest.approx(half.swing, rel=1e-6)
    assert half.brightest_over == whole.brightest_over
    with pytest.raises(ValueError):
        scan(replace(case, period_nm=None))


def test_lines_fade_from_the_readings_at_about_the_simple_rate():
    gaps = [20.0, 50.0, 100.0, 150.0]
    case = SlitCase(wavelength_nm=1050.0, spacing_nm=5.0, slit_nm=50.0)
    swings = [scan(replace(case, gap_nm=g)).swing for g in gaps]
    assert all(a > b for a, b in zip(swings, swings[1:]))
    assert swings[0] > 0.2 and swings[-1] < 0.02
    simple = fade_length_nm(200.0, 1050.0)
    assert simple == pytest.approx(32.5, abs=0.1)
    assert fitted_fade_length_nm(gaps, swings) == pytest.approx(simple, rel=0.25)


def _layers_through(indices, thicknesses, wavelength, angle_deg, polarisation):
    """Textbook share of light passing a stack of flat layers (characteristic matrices, Born and Wolf).

    ``indices`` runs from the medium the light arrives in to the medium it
    leaves in; ``thicknesses`` are those of the layers between. The angle is
    in the first medium.
    """
    k0 = 2 * np.pi / wavelength
    kx = k0 * indices[0] * np.sin(np.radians(angle_deg))
    kz = [np.sqrt((k0 * n) ** 2 - kx**2 + 0j) for n in indices]
    # admittance of each medium: kz for the field along, kz / n^2 for the field across
    y = [k if polarisation == "s" else k / n**2 for k, n in zip(kz, indices)]
    m = np.eye(2, dtype=complex)
    for k, eta, t in zip(kz[1:-1], y[1:-1], thicknesses):
        c, sn = np.cos(k * t), np.sin(k * t)
        m = m @ np.array([[c, -1j * sn / eta], [-1j * eta * sn, c]])
    b, c = m @ np.array([1.0, y[-1]])
    return float(4 * y[0].real * y[-1].real / abs(y[0] * b + c) ** 2)


@pytest.mark.parametrize("polarisation", ["s", "p"])
@pytest.mark.parametrize("angle", [0.0, 30.0])
def test_unbroken_metal_film_matches_the_textbook_layer_formula(polarisation, angle):
    # Glass, 50 nm of air, 50 nm of aluminium, silicon: metal boundaries, slanted light in the glass,
    # and a cell wide enough for the phase step across it to matter.
    case = SlitCase(wavelength_nm=650.0, polarisation=polarisation, gap_nm=50.0, slit_nm=0.0, film_nm=50.0,
                    period_nm=None, cell_nm=400.0, spacing_nm=2.5, angle_deg=angle)
    expected = _layers_through([GLASS, 1.0, metal_index("aluminium", 650.0), silicon_index(650.0)],
                               [50.0, 50.0], 650.0, angle, polarisation)
    assert 1e-4 < expected < 1e-3
    assert reading(case) == pytest.approx(expected, rel=0.03)


def test_slanted_light_on_one_repeat_equals_two_repeats():
    one = SlitCase(wavelength_nm=650.0, spacing_nm=5.0, cell_nm=600.0, angle_deg=20.0, shift_nm=50.0)
    # the same picture drawn twice in a cell of double width: two slits, so build it by hand
    from ccdsr.fdfd import solve_periodic
    from ccdsr.slit_waves import _arriving_for, _source
    lay = layout(one)
    eps = np.concatenate([lay.eps, lay.eps])
    source, phase = _source(one, eps.shape, lay.source_row)
    field = solve_periodic(eps, source, 650.0, 5.0, one.pml_cells, "p", phase)
    twice = float(np.mean(field.flow_z(lay.reading_row))) / _arriving_for(one)
    assert twice == pytest.approx(reading(one), rel=1e-6)


def test_metal_corners_settle_as_the_grid_is_made_finer():
    # With the wrong average of the materials between grid points this differs by half.
    coarse = SlitCase(wavelength_nm=1050.0, gap_nm=20.0, slit_nm=50.0, spacing_nm=5.0, cell_nm=400.0)
    fine = replace(coarse, spacing_nm=2.5)
    assert reading(coarse) == pytest.approx(reading(fine), rel=0.08)


def test_brightest_position_is_reported_the_right_way_round():
    result = scan(SlitCase(wavelength_nm=1050.0, spacing_nm=5.0, gap_nm=50.0, slit_nm=50.0))
    assert result.readings[0] > result.readings[-1]          # first position: a line under the slit
    assert result.brightest_over == "line"
    flipped = type(result)(result.case, result.shifts_nm, result.readings[::-1].copy())
    assert flipped.brightest_over == "space"
    assert flipped.swing == pytest.approx(result.swing)


def test_line_positions_stay_on_the_grid():
    assert len(default_shifts(200.0)) == 5
    for period in (120.0, 150.0, 300.0, 400.0):
        steps = np.diff(default_shifts(period))
        assert np.allclose(steps / 2.5, np.round(steps / 2.5)) and len(steps) >= 4
    with pytest.raises(ValueError):
        layout(SlitCase(shift_nm=18.75))
    widths = {int(np.isclose(layout(SlitCase(period_nm=150.0, shift_nm=s)).eps[:, 170],
                             metal_index("copper", 1050.0) ** 2).sum()) for s in default_shifts(150.0)}
    assert widths == {240}                                    # 8 lines of 30 cells at every position


def test_roomy_case_agrees_with_the_default_on_the_standard_cell():
    case = SlitCase(wavelength_nm=650.0, spacing_nm=5.0, gap_nm=50.0, slit_nm=50.0)
    assert case.roomy().pml_cells == 40 and case.roomy().above_nm == 600.0
    assert reading(case.roomy()) == pytest.approx(reading(case), rel=0.01)
