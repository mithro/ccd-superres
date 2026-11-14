# ccd-superres

Simulation of a lensless image sensor that is moved at a constant rate over a
surface, with super-resolution reconstruction of the surface from the
continuously captured pixel data.

Status: design stage. The scan sampling calculator and the trade-off explorer
are implemented; the simulator and reconstruction are not written yet.

- [Design document](docs/design.md): problem statement, measurement model,
  resolution limits, reconstruction method, software layout and build stages.
- Scan sampling calculator: how many samples each surface point gets, the
  shift per frame, sub-pixel coverage and motion blur for a given speed and
  frame rate.

  ```
  pip install -e .
  python -m ccdsr.sampling --fraction-per-s 0.2 --fps 10
  ```

- Trade-off explorer: open [`explorer/index.html`](explorer/index.html) in a
  browser. Sliders for speed, frame rate, exposure, tilt, gap and noise, with
  the resulting figures and plots updating instantly. Nothing to install.
- Tests: `pip install -e .[test]` then `pytest`.
- [Diagram sources](docs/diagrams/make_diagrams.py): regenerate the figures
  with `python docs/diagrams/make_diagrams.py`.
