"""Scan sampling calculator.

Answers questions of the form: "if the sensor moves 20% of its own length per
second and is read at 10 frames per second, how many samples does each point
on the surface get, and how well do those samples cover the sub-pixel
positions?"

All lengths are in pixels unless a name ends in ``_um``. The sensor frame has
``x`` along the sensor's long axis and ``y`` across it. The scan direction
makes an angle ``tilt`` with the sensor's ``x`` axis.

Run as a script for a quick report::

    python -m ccdsr.sampling --fraction-per-s 0.2 --fps 10
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, field

import numpy as np
from scipy.spatial import QhullError, Voronoi, cKDTree


@dataclass(frozen=True)
class Sensor:
    """Pixel array. Defaults are the Raspberry Pi Camera Module 2 (IMX219)."""

    n_along: int = 3280        # pixels along the scan-facing axis
    n_across: int = 2464       # pixels across it
    pitch_um: float = 1.12

    @property
    def length_um(self) -> float:
        return self.n_along * self.pitch_um

    @property
    def width_um(self) -> float:
        return self.n_across * self.pitch_um


@dataclass(frozen=True)
class Scan:
    """Scan settings.

    Give the speed either as ``fraction_per_s`` (fraction of the sensor length
    travelled per second) or as ``speed_um_per_s``.
    """

    fps: float
    fraction_per_s: float | None = None
    speed_um_per_s: float | None = None
    exposure_s: float | None = None     # None means continuous: the full frame period
    tilt_tan: float = 0.0               # tangent of the tilt between scan and sensor x
    readout_s: float | None = None      # rolling-shutter time from first to last row
    jitter_px: float = 0.0              # rms random position error per frame, each axis

    def speed(self, sensor: Sensor) -> float:
        """Speed in micrometres per second."""
        if (self.fraction_per_s is None) == (self.speed_um_per_s is None):
            raise ValueError("give exactly one of fraction_per_s and speed_um_per_s")
        if self.speed_um_per_s is not None:
            return self.speed_um_per_s
        return self.fraction_per_s * sensor.length_um


@dataclass(frozen=True)
class Coverage:
    """How well a set of sub-pixel phases covers one pixel."""

    n_samples: int
    distinct_phases: int
    largest_gap_along_px: float     # widest unsampled interval along x, in pixels
    largest_gap_across_px: float    # widest unsampled interval along y, in pixels
    largest_hole_px: float          # radius of the largest empty circle in the pixel
    ideal_hole_px: float            # the same for a perfect grid of n_samples points

    @property
    def efficiency(self) -> float:
        """1.0 means as good as a perfect grid with the same number of samples."""
        return self.ideal_hole_px / self.largest_hole_px if self.largest_hole_px else 1.0


@dataclass(frozen=True)
class Budget:
    """Result of :func:`scan_budget`."""

    speed_um_per_s: float
    shift_px: float                 # movement between frames, in pixels
    shift_x_px: float               # its component along the sensor x axis
    shift_y_px: float               # its component along the sensor y axis
    samples_per_point: float        # frames in which a surface point is under the sensor
    time_under_sensor_s: float
    blur_px: float                  # smear during one exposure
    exposure_s: float
    exposure_for_quarter_px_s: float
    rolling_skew_px: float | None   # shift between first and last row of one frame
    samples_per_s: float            # pixel samples recorded per second
    area_um2_per_s: float           # new surface area covered per second
    coverage: Coverage
    notes: list[str] = field(default_factory=list)


def _largest_gap(phases: np.ndarray) -> float:
    """Widest empty interval on a circle of circumference 1."""
    p = np.sort(np.mod(phases, 1.0))
    if p.size == 0:
        return 1.0
    return float(np.max(np.diff(np.concatenate([p, [p[0] + 1.0]]))))


def _largest_hole(p: np.ndarray, grid: int = 256) -> float:
    """Radius of the largest empty circle among points on the unit torus."""
    pts = np.unique(np.round(p, 9) % 1.0, axis=0)
    offsets = np.array([(i, j) for i in (-1, 0, 1) for j in (-1, 0, 1)], dtype=float)
    tiled = (pts[None, :, :] + offsets[:, None, :]).reshape(-1, 2)
    tree = cKDTree(tiled)
    try:
        # Exact: the largest hole is centred on a vertex of the Voronoi diagram.
        v = Voronoi(tiled).vertices
        v = v[np.all((v >= 0) & (v <= 1), axis=1)]
        if len(v):
            return float(tree.query(v)[0].max())
    except QhullError:
        pass
    g = (np.arange(grid) + 0.5) / grid
    probe = np.stack(np.meshgrid(g, g, indexing="ij"), axis=-1).reshape(-1, 2)
    return float(tree.query(probe)[0].max())


def phase_coverage(phases: np.ndarray) -> Coverage:
    """Measure how well ``phases`` (N by 2, in pixels) cover the unit pixel.

    Positions are taken modulo one pixel, so the pixel is treated as a torus.
    """
    p = np.mod(np.asarray(phases, dtype=float), 1.0)
    n = len(p)
    distinct = len(np.unique(np.round(p, 6) % 1.0, axis=0))
    return Coverage(
        n_samples=n,
        distinct_phases=distinct,
        largest_gap_along_px=_largest_gap(p[:, 0]),
        largest_gap_across_px=_largest_gap(p[:, 1]),
        largest_hole_px=_largest_hole(p),
        ideal_hole_px=math.sqrt(0.5 / n) if n else math.inf,
    )


def sample_phases(sensor: Sensor, scan: Scan, seed: int | None = 0) -> np.ndarray:
    """Sub-pixel positions (N by 2, pixels) at which one surface point is sampled.

    One row per frame in which the point is under the sensor. Jitter, when
    set, is added as an independent random error per frame.
    """
    shift = scan.speed(sensor) / scan.fps / sensor.pitch_um
    cos = 1.0 / math.hypot(1.0, scan.tilt_tan)
    sin = scan.tilt_tan * cos
    n = max(int(math.floor(sensor.n_along / (shift * cos))), 1) if shift > 0 else 1
    k = np.arange(n)[:, None]
    pos = k * np.array([[shift * cos, shift * sin]])
    if scan.jitter_px > 0:
        pos = pos + np.random.default_rng(seed).normal(0.0, scan.jitter_px, pos.shape)
    return pos


def scan_budget(sensor: Sensor, scan: Scan, seed: int | None = 0) -> Budget:
    """Work out the sampling figures for a sensor and scan setting."""
    speed = scan.speed(sensor)
    shift = speed / scan.fps / sensor.pitch_um
    cos = 1.0 / math.hypot(1.0, scan.tilt_tan)
    sin = scan.tilt_tan * cos
    frame_s = 1.0 / scan.fps
    exposure = frame_s if scan.exposure_s is None else scan.exposure_s
    if exposure > frame_s * (1 + 1e-9):
        raise ValueError("exposure cannot be longer than the frame period")
    blur = speed * exposure / sensor.pitch_um
    time_under = sensor.length_um / (speed * cos) if speed > 0 else math.inf
    phases = sample_phases(sensor, scan, seed)
    cov = phase_coverage(phases)

    notes = []
    if blur > 1.0:
        notes.append(
            f"Motion blur is {blur:.1f} pixels. For sub-pixel work the exposure "
            f"(or a light pulse) must be about {0.25 / shift * frame_s * 1e3:.3g} ms "
            "or shorter."
        )
    if scan.tilt_tan == 0 and scan.jitter_px == 0:
        notes.append(
            "No tilt and no jitter: every sample of a point lands at the same "
            "position across the scan, so there is no sub-pixel sampling in that "
            "direction."
        )
    if cov.distinct_phases < cov.n_samples:
        notes.append(
            f"Only {cov.distinct_phases} distinct sub-pixel positions among "
            f"{cov.n_samples} samples: the shift per frame repeats exactly. A "
            "slightly different speed, or natural jitter, breaks the repeat."
        )
    return Budget(
        speed_um_per_s=speed,
        shift_px=shift,
        shift_x_px=shift * cos,
        shift_y_px=shift * sin,
        samples_per_point=sensor.n_along / (shift * cos) if shift > 0 else math.inf,
        time_under_sensor_s=time_under,
        blur_px=blur,
        exposure_s=exposure,
        exposure_for_quarter_px_s=0.25 / shift * frame_s if shift > 0 else frame_s,
        rolling_skew_px=None if scan.readout_s is None
        else speed * scan.readout_s / sensor.pitch_um,
        samples_per_s=sensor.n_along * sensor.n_across * scan.fps,
        area_um2_per_s=speed * cos * sensor.width_um,
        coverage=cov,
        notes=notes,
    )


def format_budget(sensor: Sensor, scan: Scan, b: Budget) -> str:
    c = b.coverage
    lines = [
        f"Sensor            {sensor.n_along} x {sensor.n_across} pixels, "
        f"{sensor.pitch_um} um pitch ({sensor.length_um / 1e3:.2f} x "
        f"{sensor.width_um / 1e3:.2f} mm)",
        f"Speed             {b.speed_um_per_s:.4g} um/s",
        f"Frame rate        {scan.fps:g} frames/s",
        f"Shift per frame   {b.shift_px:.4g} px "
        f"({b.shift_x_px:.4g} along, {b.shift_y_px:.4g} across)",
        f"Samples per point {b.samples_per_point:.4g} "
        f"(a point stays under the sensor for {b.time_under_sensor_s:.3g} s)",
        f"Exposure          {b.exposure_s * 1e3:.4g} ms, motion blur {b.blur_px:.4g} px",
        f"                  exposure for a quarter-pixel blur: "
        f"{b.exposure_for_quarter_px_s * 1e3:.3g} ms",
    ]
    if b.rolling_skew_px is not None:
        lines.append(f"Rolling shutter   {b.rolling_skew_px:.4g} px skew, first to last row")
    lines += [
        f"Sub-pixel cover   {c.distinct_phases} distinct positions from "
        f"{c.n_samples} samples",
        f"                  widest gap {c.largest_gap_along_px:.3g} px along, "
        f"{c.largest_gap_across_px:.3g} px across",
        f"                  largest hole {c.largest_hole_px:.3g} px radius "
        f"(perfect grid: {c.ideal_hole_px:.3g}, efficiency {c.efficiency:.0%})",
        f"Data rate         {b.samples_per_s / 1e6:.4g} million samples/s",
        f"Area rate         {b.area_um2_per_s / 1e6:.4g} mm^2/s",
    ]
    lines += [f"Note: {n}" for n in b.notes]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--fps", type=float, required=True)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--fraction-per-s", type=float,
                   help="fraction of the sensor length travelled per second")
    g.add_argument("--speed-um-per-s", type=float)
    p.add_argument("--exposure-ms", type=float, help="default: the full frame period")
    p.add_argument("--tilt-tan", type=float, default=0.0)
    p.add_argument("--readout-ms", type=float, help="rolling-shutter readout time")
    p.add_argument("--jitter-px", type=float, default=0.0)
    p.add_argument("--n-along", type=int, default=Sensor.n_along)
    p.add_argument("--n-across", type=int, default=Sensor.n_across)
    p.add_argument("--pitch-um", type=float, default=Sensor.pitch_um)
    a = p.parse_args(argv)
    sensor = Sensor(a.n_along, a.n_across, a.pitch_um)
    scan = Scan(
        fps=a.fps,
        fraction_per_s=a.fraction_per_s,
        speed_um_per_s=a.speed_um_per_s,
        exposure_s=None if a.exposure_ms is None else a.exposure_ms / 1e3,
        tilt_tan=a.tilt_tan,
        readout_s=None if a.readout_ms is None else a.readout_ms / 1e3,
        jitter_px=a.jitter_px,
    )
    print(format_budget(sensor, scan, scan_budget(sensor, scan)))


if __name__ == "__main__":
    main()
