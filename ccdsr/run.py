"""Try one approach on one scene and see the result.

The quickest way to play with the simulator::

    python -m ccdsr.run approaches/least-squares.toml
    python -m ccdsr.run approaches/least-squares.toml --scene random_layout \\
        --set optics.gap_nm=1000 --set noise.full_e=200 --out try.png

``--set`` changes any setting of the approach for this run only: the parts
are ``optics``, ``scan``, ``noise`` and ``reconstruction``, and the settings
of each are listed by ``--list``. The scores are printed and a picture of the
true surface, the reconstruction and the raw readings is saved.
"""

from __future__ import annotations

import argparse
import dataclasses

import numpy as np

from . import approaches as ap
from . import compare as cp
from . import level1 as l1


def describe_settings():
    """Text listing every scene, reconstruction and setting with its default."""
    lines = ["Scenes: " + ", ".join(sorted(ap.SCENES)), "", "Reconstructions and their options:"]
    for name, recon in sorted(ap.RECONSTRUCTIONS.items()):
        import inspect
        options = list(inspect.signature(recon.fn).parameters.values())[2:]
        shown = ", ".join(f"{o.name}={o.default}" for o in options) or "no options"
        needs = f" (needs: {', '.join(sorted(recon.needs))})" if recon.needs else ""
        lines.append(f"  reconstruction.method={name}{needs}: {shown}")
    for part, cls in (("optics", l1.Optics1D), ("scan", l1.Scan1D), ("noise", l1.Noise1D)):
        lines += ["", f"Settings of {part} (with defaults):"]
        lines += [f"  {part}.{f.name}={f.default}" for f in dataclasses.fields(cls)]
    lines += ["", "Other: positions=known or positions=unknown; knowledge.materials=true or false"]
    return "\n".join(lines)


def run(approach: ap.Approach, scene_name="bars", seed=0):
    """Simulate, reconstruct and score. Returns ``(scene, frames, estimate, scores)``."""
    scene = ap.get_scene(scene_name)
    frames = ap.simulate(approach, scene, ap.Condition("as set"), seed)
    believed = ap.believed_frames(approach, frames).positions_nm
    estimate, positions = ap.reconstruct(approach, scene, frames)
    return scene, frames, estimate, cp.score(scene, frames, estimate, positions, believed)


def report(approach, scene, frames, scores):
    """The scores as a few lines of text."""
    lines = [f"{approach.name} on scene '{scene.name}': {frames.readings.size:,} readings, "
             f"gap {frames.optics.gap_nm:g} nm, {frames.scan.shift_px:g} pixel per frame, "
             f"{frames.noise.full_e:g} electrons at full brightness",
             f"  error against the true surface (rms, reflectance): {scores['rms_error']:.3f}"]
    if scene.groups:
        finest = scores["finest_period_nm"]
        lines.append("  finest bar period shown (nm): " + ("none" if finest is None else f"{finest:,.0f}"))
        shares = ", ".join(f"{g[0]:,.0f} nm: {s:.2f}" for g, s in zip(scene.groups, scores["contrast_share"]))
        lines.append(f"  share of each bar group's true strength shown: {shares}")
    if scores["wrong_material_percent"] is not None:
        lines.append(f"  surface assigned to the wrong material (%): {scores['wrong_material_percent']:.1f}")
    if approach.positions == "unknown":
        lines.append(f"  error of the frame positions used (nm, rms): {scores['position_error_nm']:.1f}")
    return "\n".join(lines)


def picture(approach, scene, frames, estimate, path):
    """Save the true surface, the reconstruction and the raw readings as one figure."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ink, paper = "#1f2430", "#fcfcfa"
    moved, _ = cp.align_to_truth(np.asarray(estimate, dtype=float), scene.surface,
                                 cp.ALIGN_PX * frames.optics.pitch_nm / scene.dx_nm)
    x = np.arange(scene.surface.size) * scene.dx_nm / 1e3
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(10, 6.2), facecolor=paper, height_ratios=[1.3, 1])
    top.plot(x, scene.surface, color=ink, lw=1.0, label="true surface")
    top.plot(x, moved, color="#2a78d6", lw=1.0, label=f"reconstruction ({approach.name})")
    top.set_ylabel("reflectance")
    top.set_xlabel("position on the surface (µm)")
    top.legend(frameon=False, fontsize=8.5, loc="upper right", ncols=2)
    top.set_ylim(-0.3, 1.6)
    image = bottom.imshow(frames.readings, aspect="auto", cmap="gray", interpolation="nearest")
    bottom.set_xlabel("pixel along the sensor")
    bottom.set_ylabel("frame number")
    bottom.set_title("raw readings: what the sensor recorded", loc="left", fontsize=9.5, color=ink)
    fig.colorbar(image, ax=bottom, label="electrons", fraction=0.03, pad=0.01)
    for ax in (top, bottom):
        ax.set_facecolor(paper)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("approach", nargs="?", help="approach file (TOML), for instance approaches/least-squares.toml")
    parser.add_argument("--scene", default="bars", help="test surface (default: bars)")
    parser.add_argument("--set", action="append", default=[], metavar="PART.SETTING=VALUE",
                        help="change one setting for this run; may be repeated")
    parser.add_argument("--seed", type=int, default=0, help="which random noise to use")
    parser.add_argument("--out", default="run.png", help="where to save the picture (default: run.png)")
    parser.add_argument("--list", action="store_true", help="list the scenes, methods and settings, and stop")
    args = parser.parse_args(argv)
    if args.list or not args.approach:
        print(describe_settings())
        return
    try:
        approach = ap.load_approach(args.approach, args.set)
        scene, frames, estimate, scores = run(approach, args.scene, args.seed)
    except (ap.InvalidApproach, ValueError, TypeError) as reason:
        raise SystemExit(f"cannot run: {reason}")
    print(report(approach, scene, frames, scores))
    picture(approach, scene, frames, estimate, args.out)
    print(f"picture saved to {args.out}")


if __name__ == "__main__":
    main()
