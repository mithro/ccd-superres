# Scanning lensless sensor super-resolution

A simulation of an image sensor with its lenses removed, moved at a constant
rate parallel to a surface. Every pixel captures continuously, and the many
slightly offset samples of each surface point are combined to reconstruct the
surface at a scale finer than the pixel pitch.

The scan calculator, the trade-off explorer and the first simulator (level 1,
in one and two dimensions) work today. The simulators are a chain of five levels of
increasing accuracy that are checked against each other; the rest are planned.

The pages are grouped into the same sections as the sidebar.

## Start here

The quickest way to see what exists and try it.

| Page | What it covers | State |
|---|---|---|
| [Getting started](getting-started.md) | Diagrams of the current configuration, and how to try the explorer, the simulator and the comparison yourself | Kept current |

## Plan and design

What the project has to achieve, the work in order, and how the instrument and its simulators are meant to work.

| Page | What it covers | State |
|---|---|---|
| [Project plan](plan.md) | Every item of work in order, with deep research ahead of the build stages, and the state of each | Kept current |
| [Design and requirements](design.md) | The requirements, the problem, the measurement model, what limits resolution, what ordinary light can reach, noise, the sensor, reconstruction | Draft for review |
| [Simulation chain](simulation-chain.md) | The five simulation levels, where each is valid, the shared scene description, the cross-checks, build order | Plan for review |

## Simulator and tools

The calculator, the explorers and the simulator that run today, and how to use them.

| Page | What it covers | State |
|---|---|---|
| [Scan calculator](calculator.md) | Samples per point, shift per frame, sub-pixel coverage, motion blur and resolution estimates from scan settings | Implemented |
| [Trade-off explorer](explorer.md) | The same model as an interactive page | Implemented |
| [Interactive explorer](interactive-explorer.md) | A page with a control for every setting that reruns the real simulator: setup, raw readings, reconstructions of several methods side by side, and scores. Started with `python -m ccdsr.gui` | First version, level 1 in one and two dimensions |
| [Simulation level 1](level1.md) | The first simulator: blur, sample, add noise, reconstruct. Worked example and cross-checks against the formulas | One and two dimensions and position estimation implemented |
| [Reconstruction by elimination](constrained-reconstruction.md) | Using the simulator to test candidate surfaces and positions and rule out the physically impossible: material limits, layout rules and a smooth sensor path | First version in one dimension |
| [Comparing approaches](comparison.md) | How an approach is written as one short file, and the first comparison: 13 approaches on 4 surfaces under 6 conditions, 10 runs each | First version, level 1 in one dimension |

## Lighting and optics

How light reaches the sensor, how much of it, and what can be placed in its way.

| Page | What it covers | State |
|---|---|---|
| [Side light: first estimate](light-entry.md) | A rough estimate of how much ordinary light gets under the sensor from the side, and what that does to the picture | First estimate: straight rays with a simple wave limit |
| [Side light with waves](slot-waves.md) | Side light worked out with waves, what a feature on the chip does to it, and the two ways of lighting compared, including how more readings trade against sharpness | Simulated, two dimensions |
| [Near-infrared backlight](backlight.md) | A rough estimate for lighting the chip from behind with plain near-infrared light: how much light is detected and how sharp the shadow of the metal can be | First estimate, flat layers only |
| [Filters, gratings and optical elements](optical-elements.md) | What can be added in the light, in the gap or on the sensor face, the limits for 100 nm features on silicon, the use of randomness, and the optical reasoning behind the staged plan | Exploration for review |

## Research studies

What other imaging fields already know, and what carries over to this instrument.

| Page | What it covers | State |
|---|---|---|
| [Reconstruction methods survey](reconstruction-methods.md) | Survey of methods from radar, astronomy, ptychography and other fields, what each could reach, a ranked shortlist and a staged reconstruction plan | Survey for review |
| [Radar and synthetic aperture](research/synthetic-aperture-radar.md) | Deep study B1: how radar builds a sharp picture from an uncertain path, which autofocus methods work on brightness-only data, how radar modes map onto the instrument, radar's limits on resolution and noise, and the new ideas it suggests | Study for review |
| [Beamforming and array processing](research/beamforming.md) | Deep research study B2: what treating the pixels as an array of receivers gives, which sharper array methods work on brightness-only readings, how beam directions should be chosen, and how far self-calibration carries over to pixel gains and pixel response | Study for review |
| [Multi-frame imaging in astronomy](research/multi-frame-reconstruction.md) | Deep research study B3: how scanning cameras handle motion smear, how many shifted frames are combined and at what noise cost, how well shifts are measured, how pictures are recovered without measured positions, and twelve ideas new to the project | Study for review |
| [Ptychography and lensless imaging](research/ptychography.md) | Deep research item B4: the finest detail anyone has shown without a lens, how coarse pixels have been got round, what the reconstruction needs from the data, and what stage 2 needs | Research study for review |
| [Routes to 100 nm with ordinary light](research/ordinary-light-routes.md) | Scouting study: every route found that could picture features of about 100 nm without special lighting, what more readings buy on each, what each costs, and a ranked shortlist for the simulator | Study for review |

## Calibration and testing

How the instrument is calibrated and how results are tested.

| Page | What it covers | State |
|---|---|---|
| [Calibration and test methods](calibration-and-test.md) | What must be known about the instrument and how well, what is solved from the scan and what needs an outside measurement, how resolution is measured, the tests against invented detail, and the common benchmark for every approach | Plan for review |

## Reference

Look-up pages and project records used by all the others.

| Page | What it covers | State |
|---|---|---|
| [Glossary](glossary.md) | Plain-language meanings of the terms used across the documentation | Kept current |
| [References](references.md) | The shared list of sources, and how claims are labelled as sourced, derived, estimated or assumed | Kept current |
| [Review record](review.md) | Which pages, scripts and figures have been independently checked, what was checked, what was found and what is still unchecked | Kept current |
| [Diagrams](diagrams.md) | How the figures are generated | Implemented |
| [Python reference](api.md) | Functions and classes of the `ccdsr` package | Implemented parts only |

Each simulation level will get its own page as it is built, with its method,
its assumptions, worked examples, and the results of its cross-checks.

```{toctree}
:caption: Start here
:maxdepth: 1
:hidden:

getting-started
```

```{toctree}
:caption: Plan and design
:maxdepth: 1
:hidden:

plan
Design and requirements <design>
Simulation chain <simulation-chain>
```

```{toctree}
:caption: Simulator and tools
:maxdepth: 1
:hidden:

calculator
explorer
interactive-explorer
Simulation level 1 <level1>
constrained-reconstruction
comparison
```

```{toctree}
:caption: Lighting and optics
:maxdepth: 1
:hidden:

Side light: first estimate <light-entry>
Side light with waves <slot-waves>
Near-infrared backlight <backlight>
Filters, gratings and optical elements <optical-elements>
```

```{toctree}
:caption: Research studies
:maxdepth: 1
:hidden:

Reconstruction methods survey <reconstruction-methods>
Radar and synthetic aperture <research/synthetic-aperture-radar>
Beamforming and array processing <research/beamforming>
Multi-frame imaging in astronomy <research/multi-frame-reconstruction>
Ptychography and lensless imaging <research/ptychography>
Routes to 100 nm with ordinary light <research/ordinary-light-routes>
```

```{toctree}
:caption: Calibration and testing
:maxdepth: 1
:hidden:

calibration-and-test
```

```{toctree}
:caption: Reference
:maxdepth: 1
:hidden:

glossary
references
review
diagrams
api
```
