# Scanning lensless sensor super-resolution

A simulation of an image sensor with its lenses removed, moved at a constant
rate parallel to a surface. Every pixel captures continuously, and the many
slightly offset samples of each surface point are combined to reconstruct the
surface at a scale finer than the pixel pitch.

The scan calculator, the trade-off explorer and the first simulator (level 1,
in one and two dimensions) work today. The simulators are a chain of five levels of
increasing accuracy that are checked against each other; the rest are planned.

| Page | What it covers | State |
|---|---|---|
| [Project plan](plan.md) | Every item of work in order, with deep research ahead of the build stages, and the state of each | Kept current |
| [Design](design.md) | The problem, the measurement model, what limits resolution, noise, the sensor, reconstruction | Draft for review |
| [Simulation chain](simulation-chain.md) | The five simulation levels, where each is valid, the shared scene description, the cross-checks, build order | Plan for review |
| [Filters, gratings and other optical elements](optical-elements.md) | What can be added in the light, in the gap or on the sensor face, the limits for 100 nm features on silicon, the use of randomness, and the optical reasoning behind the staged plan | Exploration for review |
| [Reconstruction methods](reconstruction-methods.md) | Survey of methods from radar, astronomy, ptychography and other fields, what each could reach, a ranked shortlist and a staged reconstruction plan | Survey for review |
| [Calibration and test methods](calibration-and-test.md) | What must be known about the instrument and how well, what is solved from the scan and what needs an outside measurement, how resolution is measured, the tests against invented detail, and the common benchmark for every approach | Plan for review |
| [Scan calculator](calculator.md) | Samples per point, shift per frame, sub-pixel coverage, motion blur and resolution estimates from scan settings | Implemented |
| [Trade-off explorer](explorer.md) | The same model as an interactive page | Implemented |
| [Simulation level 1](level1.md) | The first simulator: blur, sample, add noise, reconstruct. Worked example and cross-checks against the formulas | One and two dimensions and position estimation implemented |
| [Diagrams](diagrams.md) | How the figures are generated | Implemented |
| [Glossary](glossary.md) | Plain-language meanings of the terms used across the documentation | Kept current |
| [References](references.md) | The shared list of sources, and how claims are labelled as sourced, derived, estimated or assumed | Kept current |
| [Python reference](api.md) | Functions and classes of the `ccdsr` package | Implemented parts only |

Each simulation level will get its own page as it is built, with its method,
its assumptions, worked examples, and the results of its cross-checks.

```{toctree}
:maxdepth: 2
:hidden:

plan
design
simulation-chain
optical-elements
reconstruction-methods
calibration-and-test
calculator
explorer
level1
diagrams
glossary
references
api
```
