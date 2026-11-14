# Scanning lensless sensor super-resolution

A simulation of an image sensor with its lenses removed, moved at a constant
rate parallel to a surface. Every pixel captures continuously, and the many
slightly offset samples of each surface point are combined to reconstruct the
surface at a scale finer than the pixel pitch.

The project is at the design stage. The scan calculator and the trade-off
explorer work today. The simulators are planned as a chain of five levels of
increasing accuracy that are checked against each other.

| Page | What it covers | State |
|---|---|---|
| [Project plan](plan.md) | Every item of work in order, with deep research ahead of the build stages, and the state of each | Kept current |
| [Design](design.md) | The problem, the measurement model, what limits resolution, noise, the sensor, reconstruction | Draft for review |
| [Simulation chain](simulation-chain.md) | The five simulation levels, where each is valid, the shared scene description, the cross-checks, build order | Plan for review |
| [Filters, gratings and other optical elements](optical-elements.md) | What can be added in the light, in the gap or on the sensor face, the limits for 100 nm features on silicon, the use of randomness, and the optical reasoning behind the staged plan | Exploration for review |
| [Reconstruction methods](reconstruction-methods.md) | Survey of methods from radar, astronomy, ptychography and other fields, what each could reach, a ranked shortlist and a staged reconstruction plan | Survey for review |
| [Scan calculator](calculator.md) | Samples per point, shift per frame, sub-pixel coverage, motion blur and resolution estimates from scan settings | Implemented |
| [Trade-off explorer](explorer.md) | The same model as an interactive page | Implemented |
| [Diagrams](diagrams.md) | How the figures are generated | Implemented |
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
calculator
explorer
diagrams
api
```
