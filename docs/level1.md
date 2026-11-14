# Simulation level 1: blur and sample

## In plain words

Level 1 is the first simulator that produces sensor readings and turns them
back into a picture of the surface. It treats the surface as a flat strip of
bright and dark, blurs it the way the gap and the pixels would, reads it off
at the places the moving pixels visit, adds sensor noise, and then
reconstructs the strip from those readings.

This page covers the first part: one dimension, with the scan positions
known exactly. It shows three things.

1. Dense sampling by itself is not enough. Averaging the readings in place
   loses lines narrower than a pixel. Undoing the known blur brings them back.
2. The simulator agrees with the [level 0](calculator.md) formulas. The blur
   it applies matches the formula to better than half a percent, and the noise
   in a measured contrast matches the predicted noise within the scatter of
   the test.
3. What is lost is lost for a stated reason. Detail comes back wherever the
   blur leaves more of it than the noise, and nowhere else.

Level 1 is **not** a model of the 100 nm target. That target needs coherent
slanted light, which is level 3 in the [simulation chain](simulation-chain.md).
The example here uses coarse lines so that the method can be checked where
the answer is known.

Terms in *italics* are explained in the [glossary](glossary.md).

## What the simulator does

```{mermaid}
flowchart LR
    A["Surface<br/>strip of reflectance<br/>on a 20 nm grid"] --> B["Blur<br/>gap, pixel width,<br/>motion during exposure"]
    B --> C["Sample<br/>read the blurred strip<br/>at each pixel position<br/>in each frame"]
    C --> D["Noise<br/>photon noise,<br/>read noise,<br/>pixel gain"]
    D --> E["Raw frames"]
    E --> F["Reconstruction<br/>three methods"]
    F --> G["Score<br/>against the<br/>true surface"]
    A -.-> G
```

*Figure 1. The steps of level 1. Solid arrows are the simulated instrument
and the reconstruction. The dotted arrow is the true surface, which the
reconstruction never sees and which is used only for scoring.*

Each step is a separate, replaceable piece of code, in line with the
[approach-neutral design](design.md#71-approaches-as-named-configurations).

| Step | What it models | Settings | Source |
|---|---|---|---|
| Surface | *Reflectance* along one line of the surface | Groups of bars, or a single sinusoid | Assumption: test patterns chosen for this page |
| Gap blur | Light spreading as it crosses the gap | Gap; matt surface, or mirror-like surface with a wavelength | [Design 4.1](design.md#41-the-gap-dominates); [Goodman] |
| Pixel blur | Each pixel adds up the light over its width | *Pixel pitch*, light-sensitive width, softness of the pixel edge | [Design 4.3](design.md#43-the-pixel-area) |
| Motion blur | The sensor moves while a reading collects light | Share of the frame time the shutter is open; optional open and shut code | [Design 4.8](design.md#48-motion-blur-cause-model-and-reversal); [Raskar2006] |
| Sampling | Where each pixel is in each frame | Pixels, frames, shift per frame, random position error | Derived here: `ccdsr/level1.py` |
| Noise | *Photon noise*, *read noise*, fixed gain differences between pixels | Electrons at full brightness, read noise, gain spread | [Janesick] |

## The measurement in one line

Level 1 uses the *forward model* from the
[design](design.md#3-measurement-model):

```
readings = sample( blur( surface ) ) + noise
```

- `surface` is the reflectance on a fine grid, 20 nm per step in the examples
  here.
- `blur` multiplies each size of detail by the share of its contrast that
  survives, called the *transfer*. Coarse detail has a transfer near 1. Fine
  detail has a transfer near 0.
- `sample` reads the blurred strip at the centre of every pixel in every
  frame. Between grid points it takes a straight-line average of the two
  neighbours.
- `noise` is drawn at random for every reading.

The grid wraps round: detail leaving one end of the strip re-enters at the
other. This makes the blur exact and fast to compute. It is a convenience of
the simulator, not a property of the instrument, and the bar patterns have
empty margins so that it does not affect the scores.

## Worked example: bars from 4 µm down to 0.5 µm

The example scans five groups of bars. Each group has six bright bars with a
repeat distance (*period*) of 4, 2, 1.2, 0.8 and 0.5 µm. The pixels are
1.12 µm wide, so the last three groups are finer than one pixel.

| Setting | Value | Unit |
|---|---:|---|
| Pixel pitch | 1.12 | µm |
| Gap, matt surface | 0.30 | µm |
| Pixels in the row | 64 | |
| Frames | 160 | |
| Shift between frames | 0.37 | pixels |
| Readings in total | 10,240 | |
| Electrons at full brightness | 2,500 | e⁻ |
| Read noise | 2.0 | e⁻ |
| Exposure | short pulse, no motion blur | |
| Grid step | 20 | nm |

*Table 1. Settings of the worked example. The gap is far smaller than a real
first instrument would manage; it is chosen so that the gap and the pixel
matter about equally.*

![Five stacked plots: the true bars, one raw frame, and three reconstructions](diagrams/level1-reconstruction.svg)

*Figure 2. Top: the true surface. Second: one raw frame of 64 readings, in
which only the coarsest bars can be made out. Third: all 160 frames averaged
in place, which loses every group finer than 2 µm. Fourth and fifth: the two
methods that undo the blur bring back the 1.2 µm and 0.8 µm groups. The
0.5 µm group stays lost, because the blur leaves less than 1% of its
contrast.*

### The three reconstruction methods

| Method | What it does | Cost | Source |
|---|---|---|---|
| *Shift and add* | Puts every reading on the fine grid at its known position and averages | One pass over the readings | Standard method; see [reconstruction methods](reconstruction-methods.md) |
| *Wiener filter* | Shift and add, then divides out the known blur, holding back where the noise would be amplified | One extra Fourier transform | Standard method; see [reconstruction methods](reconstruction-methods.md) |
| Regularised *least squares* | Searches for the surface whose predicted readings best match the recorded ones, with a mild preference for smoothness (*regularisation*) | Iterative; 7 steps here | Solver: conjugate gradients [HestenesStiefel] |

### How much contrast each method recovers

Contrast here is the strength of a bar group's basic repeat divided by its
average brightness. A perfect reconstruction would match the first row.

| | 4 µm | 2 µm | 1.2 µm | 0.8 µm | 0.5 µm | Overall error (rms) |
|---|---:|---:|---:|---:|---:|---:|
| True surface | 0.85 | 0.85 | 0.85 | 0.85 | 0.87 | 0.000 |
| Shift and add | 0.63 | 0.30 | 0.02 | 0.04 | 0.01 | 0.251 |
| Wiener filter | 0.85 | 0.84 | 0.37 | 0.55 | 0.02 | 0.163 |
| Regularised least squares | 0.85 | 0.85 | 0.65 | 0.78 | 0.04 | 0.148 |
| Share of contrast the blur lets through | 0.74 | 0.35 | 0.028 | 0.045 | 0.006 | |

*Table 2. Contrast of each bar group in each reconstruction, and the rms
difference from the true surface over the whole strip, in units of
reflectance. Last row: the transfer at each period. Derived here: computed by
`docs/diagrams/make_diagrams.py` with the settings of table 1 and random
seed 1.*

Three points about reading this table.

- **The 1.2 µm group is harder than the 0.8 µm group.** A pattern that
  repeats once per pixel width averages out to nothing inside the pixel.
  1.2 µm is close to the 1.12 µm pixel, so it passes only 2.8% of its
  contrast, while 0.8 µm passes 4.5%. The same effect makes a second blind
  spot at half the pixel width, 0.56 µm, which is why the 0.5 µm group is
  lost.
- **The gap between the Wiener filter and least squares is mostly tuning.**
  Each method has one knob that sets how hard it pushes against the noise.
  The table uses each method's default. With the Wiener knob turned down by
  ten, its figures for the 1.2 and 0.8 µm groups rise to 0.63 and 0.81 and
  its overall error falls to 0.156. With evenly spread, exactly known
  positions the two methods solve nearly the same problem. Least squares is
  kept because it extends to uneven sampling, unknown positions and extra
  unknowns, which the Wiener filter does not. Judgement.
- **The overall error is dominated by the sharp bar edges.** No method here
  recovers detail finer than about 0.6 µm, and a sharp edge is made of such
  detail. The ripples beside each bar in figure 2 are the missing detail,
  not noise.

## Cross-check against level 0

The [simulation chain](simulation-chain.md#cross-checks-between-neighbouring-levels) requires each level
to agree with the one below it where both are valid. Two checks are done
here, on a single sinusoid at ten periods from 0.5 to 16 µm with the optics
of table 1.

![Two plots comparing level 1 with the level 0 formulas: blur on the left, noise on the right](diagrams/level1-crosscheck.svg)

*Figure 3. Left: the share of contrast that survives the blur. The dots are
measured on level 1 output, the solid line is the exact formula, and the
dashed line is the smooth upper limit that the level 0 calculator uses. The
dips are the blind spots at one and at one half of the pixel width. Right:
the error in a contrast measured from 6,400 noisy readings. The dots are the
scatter over 60 simulated runs and the line is the prediction. Above the
dotted line the error is as large as the pattern itself.*

| Period (µm) | Transfer, formula | Transfer, level 1 | Contrast error, predicted | Contrast error, measured | Measured ÷ predicted |
|---:|---:|---:|---:|---:|---:|
| 0.50 | 0.0060 | 0.0059 | 0.08398 | 0.08767 | 1.04 |
| 0.64 | 0.0162 | 0.0162 | 0.03083 | 0.03304 | 1.07 |
| 0.80 | 0.0451 | 0.0451 | 0.01111 | 0.01083 | 0.98 |
| 1.00 | 0.0321 | 0.0321 | 0.01559 | 0.01421 | 0.91 |
| 1.60 | 0.1950 | 0.1950 | 0.00257 | 0.00230 | 0.89 |
| 2.00 | 0.3498 | 0.3498 | 0.00143 | 0.00143 | 1.00 |
| 3.20 | 0.6376 | 0.6376 | 0.00079 | 0.00073 | 0.93 |
| 5.00 | 0.8128 | 0.8128 | 0.00062 | 0.00062 | 1.01 |
| 8.00 | 0.9121 | 0.9121 | 0.00055 | 0.00043 | 0.78 |
| 16.00 | 0.9730 | 0.9730 | 0.00051 | 0.00054 | 1.04 |

*Table 3. Level 1 against the formulas. Contrast errors are rms, for a
pattern of contrast 0.5, from 64 pixels and 100 frames. Derived here:
computed by `docs/diagrams/make_diagrams.py`.*

| Check | Result | Pass mark | Verdict |
|---|---|---|---|
| Blur against the exact transfer formula | Agrees to better than 0.001% at nine periods. At 0.5 µm the figure reads 0.4% low because the peak is read off a grid with 25 points per period. | 2% of the predicted contrast, down to a contrast of 1/1000 ([simulation chain](simulation-chain.md#cross-checks-between-neighbouring-levels)) | Pass |
| Level 0 upper limit against the exact transfer | The exact transfer never exceeds the level 0 limit | Never exceeds | Pass |
| Noise in a measured contrast against the prediction | Ratio between 0.78 and 1.07 over 60 runs per period. With 60 runs, a scatter of about ±9% (one standard deviation) is expected, so the 0.78 at 8 µm is an outlier; repeated with 400 runs that ratio is 0.94. The automated test uses 300 runs and requires agreement within 12%. | Agreement within the scatter of the test | Pass |

*Table 4. Verdicts of the cross-checks. The automated versions are in
`tests/test_level1.py` and run on every change.*

The noise prediction is the one-dimensional form of the rule the level 0
calculator uses. With `M` readings, each with noise `σ` as a share of full
brightness, a pattern with transfer `T` on an average brightness `m` has its
contrast measured with an error of

```
error = σ × √(2 ÷ M) ÷ (T × m)
```

More readings shrink the error by the square root of their number. A small
transfer multiplies it up. Derived here: `predicted_contrast_noise` in
`ccdsr/level1.py`; the noise model per reading follows [Janesick].

## What this version leaves out

| Limit | Why it matters | Where it is dealt with |
|---|---|---|
| One dimension | The real sensor is a tilted two-dimensional array, which gives finer sampling across the scan as well | Next step of [plan item D2](plan.md#d-simulation-chain) |
| Positions known exactly in the reconstruction | The real scan speed and position wander. The simulator can already add position error; the reconstruction does not yet estimate it. | Motion estimation at level 1, a later step of plan item D2 |
| The same blur model simulates and reconstructs | A reconstruction always looks best when it knows the blur perfectly. Real pixels will differ from the model. | Uncertain pixel response as a swept setting ([design 4.9](design.md#49-simulation-first-the-unknown-pixel-response-and-the-gate-before-hardware)); cross-checks against levels 2 to 4 |
| Pixel gain differences are simulated but not corrected | Uncorrected gain differences leave stripes | [Calibration and test methods](calibration-and-test.md) |
| Matt or mirror-like surface, no interference | The 100 nm target relies on interference of coherent light | Level 3 |
| Grid wraps round | Harmless with margins; would mix the two ends of a real strip | Removed when two dimensions are added |

*Table 5. Known limits of this version.*

## Running it

```python
from ccdsr import level1 as l1

dx = 20.0                                             # grid step in nm
surface, groups = l1.bar_groups([4000, 2000, 1200, 800, 500], dx)
scan = l1.Scan1D(n_pixels=64, n_frames=160, shift_px=0.37)
frames = l1.simulate(surface, dx, l1.Optics1D(gap_nm=300), scan, l1.Noise1D(), seed=1)

estimate, steps = l1.least_squares(frames)
for group in groups:
    print(group[0], l1.bar_contrast(estimate, group, dx))
```

The functions are listed in the [Python reference](api.md#simulation-level-1).

[Goodman]: references.md#textbooks-and-standard-methods
[Janesick]: references.md#textbooks-and-standard-methods
[Raskar2006]: references.md#textbooks-and-standard-methods
[HestenesStiefel]: references.md#textbooks-and-standard-methods
