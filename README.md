# ccd-superres

Simulation of a lensless image sensor that is moved at a constant rate over a
surface, with super-resolution reconstruction of the surface from the
continuously captured pixel data.

Status: design stage. The scan sampling calculator is implemented; the
simulator and reconstruction are not written yet.

- [Design document](docs/design.md): problem statement, measurement model,
  resolution limits, reconstruction method, software layout and build stages.
- Scan sampling calculator: how many samples each surface point gets, the
  shift per frame, sub-pixel coverage and motion blur for a given speed and
  frame rate.

  ```
  pip install -e .
  python -m ccdsr.sampling --fraction-per-s 0.2 --fps 10
  ```

- Tests: `pip install -e .[test]` then `pytest`.
- [Diagram sources](docs/diagrams/make_diagrams.py): regenerate the figures
  with `python docs/diagrams/make_diagrams.py`.
