# Trade-off explorer

The explorer is the [scan calculator](calculator.md) as an interactive page.
Move a slider and every figure and plot updates at once. It runs no
simulation, only the analytic model, which is why it is instant.

<p><a href="explorer/index.html">Open the explorer in its own window</a></p>

<iframe src="explorer/index.html" title="Scan trade-off explorer"
        style="width: 100%; height: 1500px; border: 1px solid #8884; border-radius: 8px;"></iframe>

## What it shows

- **Smallest recoverable feature period**, and whether the gap, the pixel
  area, motion blur or the sampling pattern is what limits it.
- **Samples per surface point, shift per frame, motion blur**, and how many
  distinct sub-pixel positions the samples reach.
- **Where the samples of one point fall inside a pixel.**
- **Contrast against feature size** for the gap, the pixel area and motion
  blur, with the level needed to beat the noise.
- **A sweep** of the recoverable feature size against any one setting, with
  everything else held fixed.
- **The 100 nm target.** A preset for 100 nm features on silicon, a choice
  between a matt surface and a mirror-like one under a directed beam, the
  wavelength, and a mask opening on each pixel. The 200 nm period of the
  target is marked on the plots.

## Using it without the documentation

The page is `explorer/index.html` in the repository and opens directly in a
browser. It needs no installation and no server.

## How it stays correct

The formulas live in `explorer/model.js`. The same formulas exist in Python in
`ccdsr/sampling.py` and `ccdsr/resolution.py`, and
`tests/test_explorer_parity.py` runs the JavaScript against the Python on a
set of cases, so the two cannot drift apart unnoticed.
