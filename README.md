# ccd-superres

[![Documentation Status](https://readthedocs.org/projects/ccd-superres/badge/?version=latest)](https://ccd-superres.readthedocs.io/en/latest/)

Read the documentation online at <https://ccd-superres.readthedocs.io/en/latest/>.

Simulation of a lensless image sensor that is moved at a constant rate over a
surface, with super-resolution reconstruction of the surface from the
continuously captured pixel data.

The goal is to find features of about 100 nm on silicon chips, spending
computation rather than hardware wherever possible.

Status: design stage. The scan sampling calculator and the trade-off explorer
are implemented; the simulator and reconstruction are not written yet.

- [Project plan](docs/plan.md): every item of work in order and its state,
  with deep research ahead of the build stages.
- [Design document](docs/design.md): problem statement, measurement model,
  resolution limits, reconstruction method, software layout and build stages.
- [Simulation chain](docs/simulation-chain.md): the five simulation levels,
  from the analytic calculator to a full electromagnetic solver, where each
  is valid, and how neighbouring levels are cross-checked.
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

## Documentation site

The `docs/` folder is a Sphinx site published on Read the Docs at
<https://ccd-superres.readthedocs.io/en/latest/>. Read the Docs rebuilds it on
every push to `main` and on every pull request, using `.readthedocs.yaml`. To
build it locally:

```
pip install -r docs/requirements.txt -e .
python -m sphinx -b html docs docs/_build/html
```
