# Oversampling: what more readings of each point buy

Oversampling is reading every point of the surface many times, each time at
a different position under the pixels, and combining the readings. It is the
project's main lever, and how it trades against sharpness, noise and scan
time is to be shown throughout ([REQ-24](design.md#requirements)). This page
gives the tool that shows it, the first study made with it, and where the
number now appears in the rest of the project.

What the first study found, at simulation [level 1](level1.md) in one
dimension, in ordinary matt light, with the baseline pixel:

1. **More readings help slowly, and only where they land on new places.**
   At a gap of 300 nm, going from 44 to 11,292 readings of each point (256
   times more) takes the finest line recovered from about 340 nm to about
   245 nm. The same number of extra readings taken with the sensor held
   still leaves it at about 340 nm.
2. **The gap decides how much oversampling is worth.** With 11,292 readings
   of each point the finest line is about 150 nm at a gap of 100 nm, 245 nm
   at 300 nm and 560 nm at 1 µm. No number of readings in the range tried
   makes up for a wider gap.
3. **Splitting the same light over more frames costs almost nothing and
   gains nothing once every position is filled.** About 11 readings of each
   point, spread over different positions, already give the result that
   11,292 give when the total light is the same. So frame rate against
   exposure is a free choice, and what buys sharpness is total light, which
   means scan time or a brighter lamp.
4. **What is known about the surface can be worth more than any number of
   readings, when the detail is within reach.** On a surface of two
   materials in 240 nm cells, knowing the two materials recovers a period of
   253 nm from 182 readings of each point, where plain least squares needs
   11,651 readings to reach 414 nm. On 100 nm cells, which are far below
   what the blur lets through at this gap, the same knowledge does not help.
5. **A narrower pixel opening and oversampling work together.** An opening
   of 280 nm collects a quarter of the light, and with 176 readings of each
   point it already shows what the full pixel needs 11,292 for.

Every number on this page is Simulated unless labelled otherwise, and comes
from the stored runs in
[`results/oversampling/`](https://github.com/mithro/ccd-superres/tree/main/results/oversampling).
Terms are explained in the [glossary](glossary.md).

## 1. The number: readings of each point

The measure of oversampling used everywhere is the **readings of each
point**: how many readings were taken by a pixel that covered a given point
of the surface.

| How the instrument is run | What it does to the readings of each point | What it costs |
|---|---|---|
| Slower scan at the same frame rate | More, in proportion | Scan time, in proportion |
| Higher frame rate at the same speed | More, in proportion | Less light in each reading; more data to read out and store |
| Longer sensor along the scan | More, in proportion | A larger sensor |
| More passes over the same strip | More, in proportion | Scan time, in proportion |
| Sensor turned slightly, or motion that wanders | The same number, spread over more different positions | Nothing, if the positions are known or can be solved for |

*Table 1. What sets the readings of each point. In a single straight pass
the number is the pixels along the scan times the frames taken while the
sensor moves one pixel: 3,280 × 4, about 13,000, for the slow baseline scan
of the [design, section 5.2](design.md#52-scan). Derived here from the
geometry; the [scan calculator](calculator.md) computes it for any setting.*

Two more numbers go with it, because the same count of readings can be worth
very different amounts:

- **Different positions per pixel.** Readings that land on a place already
  read only average the noise. Readings on new places also say what happens
  between the pixel centres. The count is of occupied 20 nm steps, scaled to
  one pixel width, so it cannot exceed 56 here.
- **Light per reading.** A reading with little light is noisier, and each
  reading also carries the sensor's own read noise, which does not shrink
  when the light does.

## 2. The tool

```
python -m ccdsr.oversampling approaches/least-squares.toml --out results/try
```

The command takes one or more [approach files](comparison.md), runs each at
a series of numbers of frames, and writes a table, a figure and a record of
every level. `--scene` picks the test surface, `--set` changes any setting
as in [`python -m ccdsr.run`](getting-started.md), `--frames` sets the
series and `--ways` picks among three ways of taking more readings:

| Way | What changes | What it stands for |
|---|---|---|
| `more-time` | More frames, the same light in each | A slower scan or more passes: more readings and more total light |
| `same-time` | More frames, less light in each, the same total light | A higher frame rate with a shorter exposure in the same scan time |
| `repeat` | More frames with the sensor held still | Plain averaging: more light and no new positions |

*Table 2. The three ways of taking more readings. `same-time` gives every
level the total light of 64 full frames.*

The code is
[`ccdsr/oversampling.py`](https://github.com/mithro/ccd-superres/blob/main/ccdsr/oversampling.py),
with tests in
[`tests/test_oversampling.py`](https://github.com/mithro/ccd-superres/blob/main/tests/test_oversampling.py).
Three points of method matter for reading the results.

**The smoothing is chosen afresh at every level.** A reconstruction prefers
a smooth picture to some degree, and the right degree falls as the noise
falls. An approach file fixes one strength, which suits one number of
readings, and with a fixed strength the result hardly changes with more
readings. Here the strength is tried over powers of ten on three separate
runs and the one with the lowest error against the true surface is kept. The
truth is used for that choice, so each curve is the best its method can do.
A real instrument does not know the truth and needs another rule, which is
an open item (section 5). `--fixed` keeps the approach's own strength.

**The finest period recovered is a new, continuous measure.** The bar groups
of the [comparison](comparison.md) come in six sizes, too few to follow a
slow change. Here the reconstructions and the true surface are both split
into waves, and in each narrow band of periods the part of the
reconstructions that is in step with the truth is compared with the strength
of both. The finest period recovered is the short end of the last band,
going from coarse to fine, in which that agreement is at least a half. The
bands are 18 % wide, so the measure moves in steps of that size. A line
width is taken as half the period.

**The level 0 column is a rule of thumb for scale.** It applies the rule of
the [design, section 4.2](design.md#42-what-a-huge-number-of-samples-buys-and-what-it-does-not)
in one dimension: a period counts as recoverable when the wave that survives
the blur stands above the noise of the readings averaged over half a period.
It is Derived here, and it is a cross-check between two levels of the
[simulation chain](simulation-chain.md), not a prediction of what a
particular reconstruction shows.

## 3. The first study

| Setting | Value | Source |
|---|---|---|
| Test surface | Two materials (reflectance 0.2 and 1.0) in cells 100 nm wide, filled at random; 26 µm long, repeating end to end | New scene `fine_layout`; the cell is the feature size of [REQ-3](design.md#requirements) |
| Second test surface | The same in cells 240 nm wide | Scene `random_layout` of the [comparison](comparison.md) |
| Pixel | Spacing 1,120 nm, edges soft over 0.3 µm (full width at half height) | Baseline of the [design, section 4.11](design.md#411-no-special-lighting-what-ordinary-light-can-reach-and-where-the-work-goes); the softness is an Assumption there |
| Light | Ordinary, matt surface, 550 nm | Level 1 default |
| Sensor | 64 pixels along the scan, moving 0.37 pixel per frame | Level 1 default |
| Light per reading | 2,500 electrons at full brightness, read noise 2 electrons | Level 1 default |
| Frames | 1, 4, 16, 64, 256, 1,024 and 4,096, giving 3 to 11,292 readings of each point | Chosen to end near the 13,000 of the baseline scan |
| Positions | Told to the reconstruction exactly | So that only the number of readings varies |
| Runs | 5 per level with different noise, and 3 more to choose the smoothing | |

*Table 3. Settings of the first study.*

### 3.1 Three ways of taking more readings

![Finest line recovered and error against readings of each point for three ways of taking more readings](diagrams/oversampling-ways.svg)

*Figure 1. Left: the finest line width recovered against the readings of
each point, for least squares at a gap of 300 nm. Right: the error against
the true surface. Solid: a longer scan. Dashed: the same total light split
over more frames. Dotted: the sensor held still. Simulated, level 1.*

| Readings of each point | Longer scan: finest line (nm) | Longer scan: error | Same total light: finest line (nm) | Same total light: error | Sensor held still: finest line (nm) | Sensor held still: error |
|---:|---:|---:|---:|---:|---:|---:|
| 3 | 655 | 0.325 | 556 | 0.310 | 655 | 0.325 |
| 11 | 556 | 0.311 | 340 | 0.296 | 655 | 0.320 |
| 44 | 340 | 0.309 | 340 | 0.298 | 556 | 0.317 |
| 176 | 340 | 0.295 | 340 | 0.295 | 556 | 0.310 |
| 706 | 340 | 0.292 | 340 | 0.296 | 340 | 0.306 |
| 2,823 | 288 | 0.287 | 340 | 0.296 | 288 | 0.305 |
| 11,292 | 244 | 0.280 | 340 | 0.297 | 340 | 0.304 |

*Table 4. Least squares at a gap of 300 nm on the surface of 100 nm cells.
The finest line is half the finest period recovered. The error is the rms
difference from the true surface in reflectance; it stays near 0.3 in every
row because most of the surface's detail is 100 nm cells, which none of
these settings recover. Simulated, level 1; full tables in section 6.*

What the three columns say:

- **A longer scan gains slowly.** From 44 to 11,292 readings the finest line
  goes from 340 nm to 244 nm: 256 times the scan time for 1.4 times the
  sharpness. This is the slow law of the
  [design, section 4.2](design.md#42-what-a-huge-number-of-samples-buys-and-what-it-does-not),
  now seen in a reconstruction and not only in a formula.
- **The curve has flat stretches, and they sit where the pixel averages a
  pattern away.** A pattern repeating exactly every pixel width, or every
  half or third of it, fills each pixel with whole periods and leaves no
  trace in its reading. For this pixel those periods are 1,120 nm, 560 nm
  and 373 nm. Detail just finer than one of them is visible again but
  weakly. The recovered period waits at about 680 nm and 580 nm before it
  gets past 560 nm.
- **Splitting the same light over more frames changes nothing after the
  first few.** With the total light fixed, 11 readings of each point at
  different positions already give 340 nm, and 11,292 give the same. The
  error is flat too. The sensor's read noise of 2 electrons is too small to
  matter even at 39 electrons of light per reading.
- **Holding the sensor still wastes most of the gain.** The same light and
  the same number of readings as the longer scan, all on about 3 positions
  per pixel, leave the error at 0.304 against 0.280. The finest period in
  this column is unsteady from row to row: with positions about 400 nm
  apart the readings cannot fix a period finer than about 800 nm, and what
  the measure reports beyond that leans on the smoothing.

A sensor with more read noise shifts the third point. With 10 electrons
instead of 2, the error at the same total light rises from 0.296 at 176
readings to 0.307 at 11,292, where each reading has 39 electrons of light
(Table O9 in section 6). The finest line stays at 340 nm.

### 3.2 The gap, and the method

![Finest line recovered against readings of each point for three gaps and four approaches](diagrams/oversampling-gaps.svg)

*Figure 2. Left: least squares at three gaps. Right: four approaches at a
gap of 300 nm. All with readings added by scanning longer, on the surface of
100 nm cells. Simulated, level 1.*

| Readings of each point | Gap 100 nm | Gap 300 nm | Gap 1 µm | Gap 300 nm, Wiener filter | Gap 300 nm, two known materials | Gap 300 nm, opening narrowed to 280 nm |
|---:|---:|---:|---:|---:|---:|---:|
| 3 | 655 | 655 | 1,073 | 655 | 655 | 472 |
| 11 | 340 | 556 | 772 | 556 | 655 | 340 |
| 44 | 340 | 340 | 772 | 340 | 556 | 288 |
| 176 | 207 | 340 | 655 | 340 | 655 | 244 |
| 706 | 176 | 340 | 655 | 340 | 340 | 244 |
| 2,823 | 176 | 288 | 556 | 288 | 288 | 244 |
| 11,292 | 149 | 244 | 556 | 244 | 288 | 176 |

*Table 5. Finest line width recovered (nm), half the finest period, on the
surface of 100 nm cells with readings added by scanning longer. The first
three columns are least squares. Simulated, level 1.*

- **The gap sets the level, and oversampling moves along it.** At 11,292
  readings the finest line is 149 nm, 244 nm and 556 nm for gaps of 100 nm,
  300 nm and 1 µm. The best-case estimate of the
  [design, Table 4.11b](design.md#411-no-special-lighting-what-ordinary-light-can-reach-and-where-the-work-goes)
  for 13,000 readings in two dimensions is 161 nm, 219 nm and 439 nm. The
  two agree to within the 18 % step of the measure at the two smaller gaps;
  at 1 µm the simulated result is 27 % coarser.
- **At a small gap oversampling keeps paying; at a large gap it stops
  early.** At 100 nm the line width halves between 44 and 11,292 readings.
  At 1 µm it improves by 1.4 times over the same range and not at all over
  the last factor of four.
- **Least squares and the Wiener filter give the same curve** once each has
  its smoothing chosen. With exactly known positions they are two ways of
  doing the same thing.
- **A narrower opening changes the trade.** The opening of 280 nm has no
  blind periods above 280 nm and blurs less, so with 176 readings it
  already reaches 244 nm, and with 11,292 it reaches 176 nm, although every
  reading has a quarter of the light. Oversampling is what pays for the lost
  light.
- **Knowing the two materials does not help on this surface.** Its cells
  are far finer than what the blur passes at 300 nm, and forcing every
  point to one of two values then picks wrongly as often as rightly.

### 3.3 Detail within reach: what is known beats what is counted

| Readings of each point | Least squares: finest period (nm) | Least squares: error | Two known materials: finest period (nm) | Two known materials: error |
|---:|---:|---:|---:|---:|
| 3 | 1,310 | 0.293 | 1,310 | 0.305 |
| 11 | 800 | 0.281 | 1,310 | 0.296 |
| 46 | 679 | 0.255 | 679 | 0.289 |
| 182 | 576 | 0.232 | 253 | 0.223 |
| 728 | 576 | 0.215 | 253 | 0.190 |
| 2,913 | 576 | 0.199 | 253 | 0.193 |
| 11,651 | 414 | 0.194 | 253 | 0.190 |

*Table 6. The surface of 240 nm cells at a gap of 300 nm, readings added by
scanning longer. This surface has almost nothing finer than a period of
about 250 nm, so 253 nm is the finest the measure can report on it.
Simulated, level 1.*

On cells of 240 nm the knowledge that the surface is one of two materials
changes the picture from 182 readings of each point upward: the recovered
period drops to the finest the surface contains, where least squares is
still at 576 nm. Below 46 readings the knowledge does not help and the error
is higher. So this prior needs a minimum of oversampling to work, and then
replaces a very large amount of it.

This is one surface, one gap and one kind of knowledge. It is recorded here
as the first sign of where the effort of
[REQ-22](design.md#requirements) should look: the combination of moderate
oversampling with strong knowledge of the surface, more than extreme
oversampling by itself.

## 4. Where the number now appears

| Place | What was added |
|---|---|
| [Comparison runner](comparison.md) | Every run records its readings of each point, and the data table of every comparison lists them. The first comparison was rerun; its results are unchanged apart from the new column |
| [Interactive explorer](interactive-explorer.md) | A panel "More readings of each point: what they buy" reruns the ticked methods at 1 to 512 frames with every other setting as on the page, and draws the finest period recovered and the error against the readings of each point, for the three ways of Table 2 |
| Command line | `python -m ccdsr.oversampling`, section 2 |
| [Slot waves, Table 6](slot-waves.md) | The same trade for the two ways of lighting the chip, from the level 0 model (added earlier) |
| [Plan](plan.md#d-simulation-chain) | Item D1c, with what comes next |

*Table 7. Where oversampling is shown.*

![The explorer's oversampling panel: finest period recovered and error against readings of each point, three curves for least squares](diagrams/interactive-explorer-oversampling.png)

*Figure 3. The panel in the interactive explorer, here for least squares on
the surface of 100 nm cells with the default settings (sharp pixel edges,
gap 300 nm). Solid, dashed and dotted are the three ways of Table 2.
Simulated, level 1; three runs per point.*

## 5. Limits, and what comes next

| Limit | Why it matters | Where it is dealt with |
|---|---|---|
| One dimension, level 1, matt ordinary light | Sensor tilt and passes spread positions in two dimensions, which one dimension cannot show; below a few micrometres the blur model itself is unconfirmed | [Plan](plan.md#d-simulation-chain) items D1c and D5 |
| Positions told exactly | Solving for positions also needs readings, and may need more of them than the picture does | Item D1c |
| The smoothing is chosen with the truth known | Each curve is a best case for its method. A rule that uses only the readings (for instance the measured noise) has to be shown to come close | Item D1c |
| The surface repeats and is shorter than the sensor | The sensor laps the surface, so positions fill up sooner than in a real single pass | Longer surfaces, item D1a |
| The finest-period measure moves in 18 % steps and uses five runs | Single steps in the tables are not significant; differences of two steps are | More runs and a longer surface |
| One pixel model | Softer or sharper pixel edges move every curve ([design, section 4.11](design.md#411-no-special-lighting-what-ordinary-light-can-reach-and-where-the-work-goes)) | The uncertain pixel response sampled over its range, item D1a |
| Light from behind the chip is not in the study | It is the leading ordinary-light route and has its own model | Item D2f, which is to report against readings of each point from the start |
| Computing time is not a column | It is not a reason to prefer one level over another ([REQ-23](design.md#requirements)); the largest level here takes seconds | |

*Table 8. What this first study does not cover.*

## 6. Full results

To repeat the study and redraw the figures (about 15 minutes):

```
python docs/diagrams/make_oversampling_diagrams.py --rerun
```

```{include} ../results/oversampling/tables.md
```
