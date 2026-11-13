# ccd-superres

Simulation of a lensless image sensor that is moved at a constant rate over a
surface, with super-resolution reconstruction of the surface from the
continuously captured pixel data.

Status: design stage. No simulator code has been written yet.

- [Design document](docs/design.md): problem statement, measurement model,
  resolution limits, reconstruction method, software layout and build stages.
- [Diagram sources](docs/diagrams/make_diagrams.py): regenerate the figures
  with `python docs/diagrams/make_diagrams.py` (needs `numpy`, `scipy` and
  `matplotlib`).
