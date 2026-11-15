# How much ordinary light gets under the sensor

The sensor lies face down over the chip it is looking at, so it shades the
very area it is trying to see. Ordinary light can only come in from the
side, through the slot between the two. This page is a first, rough
estimate of how much light arrives that way, from which direction, and what
that does to the sharpness of the picture. It is item 1 in the order of
work of the
[design, section 4.11](design.md#411-no-special-lighting-what-ordinary-light-can-reach-and-where-the-work-goes),
and it applies requirement [REQ-6](design.md#requirements): special
lighting is not assumed.

The answers:

- **At the gaps the design wants, side light does not reach the middle of
  the sensor.** Light squeezed into a slot cannot travel flatter than a
  certain angle, and below about 5 µm of gap that angle is steep enough
  for the light to be absorbed on the way in. At a gap of 1 µm almost
  nothing is left 60 µm in from the edge, and the middle is 1,380 µm in.
- **At gaps of 5 µm and more, a little light arrives, skimming.** A pixel
  in the middle gets a few hundred-thousandths of what it would get
  uncovered, and the light meets it at 82° to 87° from straight on.
- **That light did not come from the patch of chip under the pixel.** It
  last touched the chip 90 µm to 200 µm away, so in this model the picture
  is that coarse. The best case of design Table 4.11b, a blur about as
  wide as the gap, is not reached with light from the side onto a flat
  chip at any gap.
- **Side light is therefore not a workable baseline as it stands.** The
  options are in section 5. One effect the model leaves out, light knocked
  upwards by the edges of the chip's own features, might help near the lit
  side and needs a wave calculation.

Everything on this page is an Estimate from a simple model, written for
this page in
[`ccdsr/light_entry.py`](https://github.com/mithro/ccd-superres/blob/main/ccdsr/light_entry.py)
and tested in
[`tests/test_light_entry.py`](https://github.com/mithro/ccd-superres/blob/main/tests/test_light_entry.py).
The numbers show the scale of the problem and are not predictions. Nothing
here has been measured.

## 1. The model

![Side view of a sensor above a chip with a ray of light entering from the left and bouncing between the two](diagrams/light-entry-slot.svg)

*Figure 1. The slot seen from the side, not to scale. A ray entering from
the side bounces between chip and sensor. Drawn by
[`make_light_entry_diagrams.py`](https://github.com/mithro/ccd-superres/blob/main/docs/diagrams/make_light_entry_diagrams.py).*

A ray that makes a shallow angle with the two surfaces (its grazing angle)
touches them alternately as it travels inwards. Three things follow from
the geometry.

| Quantity | Formula | Meaning |
|---|---|---|
| Touches on each surface | distance × tan(grazing angle) ÷ (2 × gap) | Steep rays touch often, skimming rays rarely |
| Share of the ray left | (reflectance of chip × reflectance of sensor) raised to that number | A little is absorbed at every touch |
| One hop | 2 × gap ÷ tan(grazing angle) | The distance along the chip from one touch to the next |

*Table 1. The geometry of one ray. Derived here from straight rays between
two flat, parallel surfaces.*

The share reflected at each touch comes from the Fresnel formulas, the
standard formulas for how much light a flat surface reflects at each angle
[BornWolf]. They need the refractive index of the material, and they give
a different answer for each of the two polarisations of light: the
electric field lying along the surface, or across it. Both are followed
and averaged. The light at the open edge is taken to come evenly from all
directions.

A pixel's reading is what the sensor absorbs at the ray's touches on it,
given as a share of what an uncovered pixel would absorb in the same
light. It is worked out as follows (Derived here).

| Step | Quantity | Value |
|--:|---|---|
| 1 | Light entering the slot per unit width, for brightness E on an opening of height h | E × h |
| 2 | Share of it at grazing angle φ, for light arriving evenly from all directions | cos φ, which adds up to 1 over 0° to 90° |
| 3 | Share of a ray left after distance x | T(φ), from Table 1 |
| 4 | Touches on the sensor per unit length | tan φ ÷ (2 h) |
| 5 | Share absorbed at each touch | 1 − reflectance of the sensor |
| 6 | Reading at distance x, as a share of E | steps 1 to 5 multiplied and added over all angles. The height h cancels, so only x ÷ h matters |

*Table 1a. How the reading is worked out. The uncovered pixel is taken to
absorb everything that falls on it. Bare silicon reflects 37 % straight
on, so the readings on this page are low by a factor of up to 1.6 on that
account, which changes none of the conclusions.*

**Where rays stop being valid.** Light is a wave, and a wave squeezed into
a slot has to fit at least half a wavelength across it. That sets the
flattest angle it can travel at: the angle whose sine is the wavelength
divided by twice the gap (the textbook result for a wave between two
mirrors; Derived here, and real surfaces change the details and not the
scale). At a gap of 1 µm and green light that is 16°. The rays that survive
to the middle in the ray model are flatter than that, so at small gaps
they do not exist. For those gaps the page gives a second number: what is
left of a ray at the flattest angle a wave can take.

| Setting | Value | Status |
|---|--:|---|
| Distance from the open edge to the middle of the sensor | 1.38 mm | Half the short side of the light-sensitive area, 2.76 mm ([design, section 5.1](design.md#51-sensor)) |
| Wavelength | 550 nm | Green light. Assumption |
| Refractive index of silicon | 4.08 + 0.03i | [Green2008] gives 4.077 + 0.028i at 550 nm, as tabulated in the refractiveindex.info database ([`ccdsr/data/silicon_green2008.csv`](https://github.com/mithro/ccd-superres/blob/main/ccdsr/data/silicon_green2008.csv)) |
| Refractive index of aluminium | 0.96 + 6.7i | Unverified, as above; tabulated in [Rakic1995] |
| Refractive index of glass (silicon dioxide) | 1.46 | Unverified, as above; tabulated in [Malitson1965] |
| Chip surface and sensor surface | Bare silicon, flat | Assumption. Real chips carry oxide, metal and steps; real pixels carry layers |

*Table 2. Settings of the estimate. Table 4 shows that the conclusions
hardly depend on the three refractive indices.*

## 2. What it gives

| Gap (µm) | Flattest angle a wave can take (°) | Typical ray in the ray model (°) | Ray model usable? | Share of the flattest wave left at the middle | Distance in at which that wave is down to 1 % (µm) |
|--:|--:|--:|---|--:|--:|
| 0.3 | 66 | 0.8 | No | none | under 1 |
| 1 | 16 | 1.4 | No | under 10⁻⁴⁰ | 58 |
| 3 | 5.3 | 2.5 | No | 0.02 | 1,600 |
| 5 | 3.2 | 3.2 | Borderline | 0.43 | 7,500 |
| 10 | 1.6 | 4.6 | Yes | 0.90 | over 10,000 |
| 30 | 0.5 | 7.9 | Yes | 1.0 | over 10,000 |

*Table 3. Where the ray model can be used, for the middle of the sensor,
1.38 mm in from the edge. Angles are measured from the surface. The last
two columns are for the polarisation that survives best (field along the
surface); the other is absorbed 5 to 20 times sooner. Estimate: the loss
per touch of the ray model applied to a ray at the flattest angle a wave
can take. Below a gap of about 0.28 µm, half a wavelength, no travelling
wave of this kind fits at all.*

So for gaps under about 5 µm the answer is that side light is absorbed
before it reaches the middle, and the ray model's readings would be far
too high. For gaps of 5 µm and more the ray model can be used:

| Gap (µm) | Distance ÷ gap | Reading, share of an uncovered pixel's | Exposure needed, times longer | Angle of arrival from straight on (°) | Distance to where the light last touched the chip (µm) |
|--:|--:|--:|--:|--:|--:|
| 5 | 276 | 0.000 028 | 36,000 | 86.8 | 88 |
| 10 | 138 | 0.000 078 | 13,000 | 85.4 | 125 |
| 30 | 46 | 0.000 38 | 2,600 | 82.1 | 215 |

*Table 3c. Light at the middle of the sensor in the ray model. Estimate,
with the settings of Table 2. The angle and the last column are for the
typical ray: half the absorbed light arrives more steeply and half less.
The last column is half a hop. The model treats the loss as smooth, which
needs many touches, so it is used only beyond about 30 gaps from the edge;
an independent check with rays followed one by one agreed within 12 % for
these rows.*

![Two charts against distance from the open edge for three gaps: the reading falls steeply and the distance to the last touch grows](diagrams/light-entry-curves.svg)

*Figure 2. Left: the reading against distance in from the edge. Right: how
far away the light last touched the chip, with the gap itself dotted for
comparison. Estimate from the ray model, for the gaps where it can be
used.*

Two simple rules summarise the curves:

| Quantity | Rule | Example: gap 10 µm, 1.38 mm in |
|---|---|--:|
| Reading, as a share of an uncovered pixel's | 0.137 × (gap ÷ distance) to the power 1.5 | 0.000 085 |
| Distance to where the light last touched the chip | 1.1 × square root of (gap × distance) | 129 µm |

*Table 3a. Rules of thumb. The first is Derived here by doing the sum over
angles by hand for small angles, and is checked against the code in the
tests; it is within 10 % beyond about 100 gaps from the edge. The second
is fitted to the model's output.*

| Chip surface | Sensor surface | Reading, share of an uncovered pixel's | Distance to the last touch (µm) |
|---|---|--:|--:|
| Silicon, 4.08 + 0.03i | Silicon | 0.000 002 6 | 40 |
| Silicon, 3.9 + 0.02i | The same | 0.000 002 6 | 41 |
| Silicon, 4.3 + 0.07i | The same | 0.000 002 7 | 38 |
| Aluminium | Silicon | 0.000 006 3 | 28 |
| Glass | Silicon | 0.000 001 4 | 91 |

*Table 4. The ray model at a distance of 1,380 gaps with other materials,
to show how little the material matters. Estimate. (At a gap of 1 µm,
where this distance is the middle of the sensor, the ray model is not
usable; the comparison between materials still holds.) The glass row
treats the chip as solid glass. A real chip has a few micrometres of glass
over metal and silicon, which reflects more than this.*

## 3. What this means

**Only skimming light survives, and a narrow slot does not allow skimming
light.** A ray at a steep angle touches the surfaces thousands of times on
its way to the middle and is absorbed long before it gets there. A
skimming ray touches rarely, and at shallow angles every material reflects
almost completely, so it survives. But the narrower the slot, the steeper
the flattest wave that fits in it (Table 3). Below about 5 µm of gap the
two requirements cannot both be met, and the light dies out near the edge.

**Where light does arrive, the pixel is reading the wrong place.** In the
best case of the [design, Table 4.11b](design.md#411-no-special-lighting-what-ordinary-light-can-reach-and-where-the-work-goes),
light leaves each point of the chip in all directions and the pixel
straight above collects it, so the blur is about as wide as the gap. A
skimming ray instead carries the mark of a point on the chip sideways by
half a hop before a pixel absorbs it, and rays at slightly different angles
carry it different distances. The blur is of the order of that distance:
about 90 µm to 200 µm in the middle of the sensor (Judgement, from the last
column of Table 3c; the model does not compute a picture).

**The reading is a running total.** Every touch on the chip removes a
little light from the ray for good, so a pixel's reading carries the mark
of every place its light has touched since the edge. A feature on the chip
shows up as a slightly darker streak behind it, seen from the lit side,
and has to be found by comparing neighbouring readings (Derived here from
the model).

**The contrast is diluted.** Two things weaken the mark a feature leaves.
The materials reflect more alike at skimming angles than straight on
(Table 3b). And a feature is touched only by the rays whose hop happens to
land on it. For an aluminium line 1 µm wide on silicon, under a gap of
10 µm, about one ray in 250 touches the line and the reading behind it
changes by about one part in a thousand (Estimate, from the hop and the
reflectances of the typical ray).

| Material | Straight on (%) | At 1.5° from the surface, field along the surface (%) | At 1.5°, field across the surface (%) |
|---|--:|--:|--:|
| Silicon | 37 | 97 | 64 |
| Aluminium | 92 | 99.8 | 91 |
| Glass | 3.5 | 91 | 81 |

*Table 3b. Share of light reflected by a flat surface. Derived from the
Fresnel formulas with the values of Table 2, for the two polarisations of
the light.*

**A larger gap lets light in and loses the picture another way.** Table
3c shows more light at larger gaps, landing further from where it touched
the chip. The best-case blur also grows with the gap: at 10 µm it is
already lines of about 3 µm (design Table 4.11b).

**Nearer the open edge it is better.** Both the amount of light and the
sideways carry improve towards the edge (Figure 2). The light-sensitive
area of a real sensor does not start at the edge of its silicon, and bond
wires and the package stand around it
([design, section 5.3](design.md#53-the-sensor-stack-and-what-removing-the-lenses-leaves)),
which also shade the opening. How close the nearest pixels are to an open
edge is Unverified for the baseline sensor.

## 4. What the model leaves out

| Left out | Likely effect | How to find out |
|---|---|---|
| **Light scattered upwards by the chip's features.** A real chip is not flat: lines have edges and steps. An edge struck by skimming light throws some of it in all directions, and the pixel straight above collects part of that | It might give a picture of edges, bright on a dark background, near the lit side. Three things limit it. A step blocks a share of the skimming light of about its height divided by the gap, so the first features shade those further in. Scattered light bounces again between chip and sensor and makes a halo. And only edges lying across the direction of the light scatter strongly. How bright the result is, is not known | A wave calculation on a small patch (level 4 of the [simulation chain](simulation-chain.md)). Unverified until then |
| Waves, beyond the simple limit used in Table 3 | With silicon on both sides there is no wave that is guided without loss; the loss grows quickly as the gap shrinks. A metal surface can carry a wave along itself at any gap, but it too dies out within tens of micrometres (Unverified; from general knowledge of light between absorbing surfaces) | The same wave calculation |
| The third dimension. Light also enters from the other three sides and at angles across the slot. A feature's mark is a wedge-shaped shadow, not a streak | A few times more light. No improvement to the blur | Not needed yet |
| The layers on a real pixel: microlenses, colour filter, wiring | A pixel as sold accepts little light at 85° from straight on, so the reading would be lower still (Unverified; [plan](plan.md#data-collection), item R3) | Data item R3, then level 4 |
| The layers on a real chip: a few micrometres of glass over metal | Changes the reflectances. It also adds to the distance between the features and the pixel | Level 4 |
| The opening at the edge being evenly lit | A lamp aimed along the slot puts more of its light at shallow angles: about 7 times more reading at a gap of 5 µm and about 4 times at 10 µm, for a lamp aimed within 1° of the surface. The flatter light is carried further sideways, so the blur gets worse (Estimate from the same model) | Not needed yet |

*Table 5. What the estimate leaves out, most important first.*

## 5. Other ways to get ordinary light in

Each of these is a candidate to look at, and none has been checked.
Whether they count as special lighting is a question for
[design, section 11](design.md#11-build-stages-and-open-questions), item 12.

| Way in | What it would give | Difficulty | Status |
|---|---|---|---|
| Through the chip from behind, with plain near-infrared light (light just beyond red, which the eye cannot see and which silicon partly lets through). First estimate: [backlight](backlight.md) | Light arriving straight on, as the best case assumes. The picture would be a shadow picture of the chip's metal, which blocks the light. About ten times more light than from the side at a gap of 10 µm ([backlight](backlight.md), Table 4) | An ordinary sensor responds only weakly to light that silicon lets through; the wavelength is about 1 µm, twice that of green light, so the finest detail is coarser; the chip may need thinning | The leading candidate. First estimate done; its open points are in [backlight](backlight.md), Table 8 |
| From the side, relying on the chip's edges to scatter light upwards. Since worked out with waves: [slot waves](slot-waves.md) | No direct picture: a feature marks the readings over tens of micrometres | Works only at gaps of several micrometres, where the best case is already coarse; first features shade the rest (Table 5) | Worked out: see [slot waves](slot-waves.md) |
| From the side, using only the pixels nearest an open edge and scanning the chip past them | More light and a shorter sideways carry | The sensor's border and bond wires keep pixels away from the edge; most of the sensor is unused | Unverified |
| Through the sensor from behind | Light arriving straight on | The baseline sensor is lit from its back face, which here faces the chip, so the light would have to come through its wiring and the wafer it is mounted on. It would also pass the light-sensitive layer on the way in, so each pixel would mostly read the lamp. A change to the sensor, so hardware work | Unverified |
| A light source in the gap or on the sensor's face | Light where it is needed | A purpose-built part. Probably special lighting | Recorded only |

*Table 6. Ways to light the chip under the sensor. Judgement.*

## 6. What changes in the plan

| Change | Where |
|---|---|
| Side light does not reach the middle of the sensor at gaps under about 5 µm, and at larger gaps does not give the best case of design Table 4.11b. The design now says so and points here | [Design, section 4.11](design.md#411-no-special-lighting-what-ordinary-light-can-reach-and-where-the-work-goes) |
| How the chip is lit becomes the first question to settle. A wave calculation of light entry and of scattering by edges, and a first estimate for near-infrared light from behind the chip, move to the front of the order of work | Design Table 4.11d; [plan](plan.md#d-simulation-chain), items D5 and D2e |
| Simulation level 1 needs a second light model beside "matt": a reading that is a running total along the direction of the light, with a sideways carry | [Plan](plan.md#d-simulation-chain), item D2d |
| The light budget is to enter the scan calculator: exposures thousands of times longer than for an uncovered sensor in the same light | [Plan](plan.md#c-fold-the-research-into-the-design), item C1a |
| Ray tracing (level 2) is not the tool for the slot at these gaps | [Plan](plan.md#d-simulation-chain), item D3 |

*Table 7. What this estimate changes.*

## 7. How to repeat it

```
python docs/diagrams/make_light_entry_diagrams.py
python -m pytest -q tests/test_light_entry.py
```

The first command redraws the two figures and prints the rows of Tables 3
and 3c.
From Python:

```python
from ccdsr.light_entry import light_under_sensor
print(light_under_sensor(gap_nm=10000))
```

## Sources

| Key | Source | Used for |
|---|---|---|
| BornWolf | M. Born and E. Wolf, *Principles of Optics*. In the [shared reference list](references.md) | The Fresnel formulas for reflection at a flat surface |
| Green2008 | M. A. Green, "Self-consistent optical parameters of intrinsic silicon at 300 K including temperature coefficients", *Solar Energy Materials and Solar Cells* 92, 1305 (2008). [doi:10.1016/j.solmat.2008.06.009](https://doi.org/10.1016/j.solmat.2008.06.009). Existence checked against a bibliographic database. The value was taken from the refractiveindex.info database's copy of the paper's table, not from the paper itself | Refractive index of silicon |
| Rakic1995 | A. D. Rakić, "Algorithm for the determination of intrinsic optical constants of metal films: application to aluminum", *Applied Optics* 34, 4755 (1995). [doi:10.1364/AO.34.004755](https://doi.org/10.1364/AO.34.004755). Existence checked; the text was not read | Where the refractive index of aluminium is tabulated |
| Malitson1965 | I. H. Malitson, "Interspecimen comparison of the refractive index of fused silica", *Journal of the Optical Society of America* 55, 1205 (1965). [doi:10.1364/JOSA.55.001205](https://doi.org/10.1364/JOSA.55.001205). Existence checked; the text was not read | Where the refractive index of silicon dioxide is tabulated |

*Table 8. Sources.*
