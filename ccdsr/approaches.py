"""Approaches as named configurations, and the parts they are built from.

An approach is a short text file (TOML) that names one implementation and its
settings for each part of the instrument and of the processing: optics, scan,
noise, what the instrument knows about its own positions, and the
reconstruction. Nothing about any one approach is built into the code. New
scenes and reconstructions are added with :func:`scene` and
:func:`reconstruction` and can then be named in any approach file.

This first version covers simulation level 1 in one dimension
(:mod:`ccdsr.level1`). See ``docs/comparison.md``.
"""

from __future__ import annotations

import dataclasses
import inspect
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from . import constrained
from . import level1 as l1

DX_NM = 20.0


# ------------------------------------------------------------------ scenes

@dataclass(frozen=True)
class Scene:
    """A test surface with what is needed to score a reconstruction of it."""

    name: str
    surface: np.ndarray
    dx_nm: float
    groups: tuple = ()                 # bar groups (period, start, stop), if any
    levels: tuple | None = None        # the two reflectances, if the scene has exactly two


SCENES = {}


def scene(name):
    """Register a function that builds a :class:`Scene`."""
    def add(fn):
        SCENES[name] = fn
        return fn
    return add


@scene("bars")
def _bars():
    surface, groups = l1.bar_groups([4000, 2000, 1200, 800, 480, 320], DX_NM)
    return Scene("bars", surface, DX_NM, tuple(groups), (0.2, 1.0))


@scene("random_layout")
def _random_layout():
    """Two materials in cells 240 nm wide, filled at random (fixed seed)."""
    rng = np.random.default_rng(20261114)
    cells = rng.integers(0, 2, 80)
    margin = np.full(150, 0.2)
    surface = np.concatenate([margin, np.repeat(np.where(cells == 1, 1.0, 0.2), 12), margin])
    return Scene("random_layout", surface, DX_NM, (), (0.2, 1.0))


@scene("isolated_lines")
def _isolated_lines():
    """Seven narrow bright lines, 200 nm wide, at uneven spacings on a dark surface."""
    surface = np.full(1400, 0.2)
    for at in (150, 330, 420, 700, 760, 1010, 1220):
        surface[at:at + 10] = 1.0
    return Scene("isolated_lines", surface, DX_NM, (), (0.2, 1.0))


@scene("soft_ramps")
def _soft_ramps():
    """A surface of many reflectances: smooth waves of three periods added together."""
    x = np.arange(1400) * DX_NM
    surface = 0.5 + 0.2 * np.sin(2 * np.pi * x / 5600) + 0.15 * np.sin(2 * np.pi * x / 1400 + 1.0) \
        + 0.1 * np.sin(2 * np.pi * x / 700 + 2.0)
    return Scene("soft_ramps", surface, DX_NM)


def get_scene(name) -> Scene:
    if name not in SCENES:
        raise ValueError(f"unknown scene {name!r}; known: {sorted(SCENES)}")
    return SCENES[name]()


# --------------------------------------------------------- reconstructions

@dataclass(frozen=True)
class Reconstruction:
    fn: object
    needs: frozenset
    solves_positions: bool


RECONSTRUCTIONS = {}


def reconstruction(name, needs=(), solves_positions=False):
    """Register a reconstruction.

    The function is called as ``fn(frames, levels, **options)`` and returns
    ``(surface, positions)``, with ``positions`` None if it does not estimate
    them. ``frames.positions_nm`` holds what the instrument believes, never
    the truth, and ``frames.truth`` is empty. ``needs`` lists what the
    approach must be told: ``"materials"`` (the scene's two reflectances,
    passed as ``levels``) or ``"positions"`` (true positions).
    """
    def add(fn):
        RECONSTRUCTIONS[name] = Reconstruction(fn, frozenset(needs), solves_positions)
        return fn
    return add


@reconstruction("shift_and_add")
def _shift_and_add(frames, levels):
    return l1.shift_and_add(frames)[0], None


@reconstruction("wiener")
def _wiener(frames, levels, noise_to_signal=1e-3):
    return l1.wiener(frames, noise_to_signal), None


@reconstruction("least_squares")
def _least_squares(frames, levels, smoothness=1e-2):
    return l1.least_squares(frames, smoothness=smoothness, positions_nm=frames.positions_nm)[0], None


@reconstruction("least_squares_positions", solves_positions=True)
def _least_squares_positions(frames, levels, smoothness=1e-2, path_stiffness=0.0, rounds=40, max_step_px=3.0,
                             coarse_smoothness=1000.0):
    positions, _ = l1.estimate_positions(frames, frames.positions_nm, rounds=rounds,
                                         smoothness=(coarse_smoothness, smoothness), max_step_px=max_step_px,
                                         path_stiffness=path_stiffness)
    return l1.least_squares(frames, smoothness=smoothness, positions_nm=positions)[0], positions


@reconstruction("two_materials", needs=("materials",))
def _two_materials(frames, levels, smoothness=1e-3):
    return constrained.material_reconstruction(frames, levels, positions_nm=frames.positions_nm,
                                               smoothness=smoothness)[0], None


@reconstruction("two_materials_positions", needs=("materials",), solves_positions=True)
def _two_materials_positions(frames, levels, path_stiffness=10.0, rounds=40, max_step_px=3.0):
    estimate, _, positions = constrained.solve_surface_and_positions(
        frames, levels, start_positions_nm=frames.positions_nm, path_stiffness=path_stiffness, rounds=rounds,
        max_step_px=max_step_px)
    return estimate, positions


# ---------------------------------------------------------------- approach

_PARTS = {"optics": l1.Optics1D, "scan": l1.Scan1D, "noise": l1.Noise1D}
_TOP = {"name", "description", "hardware", "level", "positions", "optics", "scan", "noise", "reconstruction",
        "knowledge"}


class InvalidApproach(ValueError):
    """An approach file, or a combination of approach, scene and condition, that cannot be run."""


# Allowed range of each numeric setting: (lowest, whether the lowest itself is allowed).
_LIMITS = {
    "gap_nm": (0.0, True), "pitch_nm": (0.0, False), "aperture_nm": (0.0, False), "edge_sigma_nm": (0.0, True),
    "wavelength_nm": (0.0, False), "n_pixels": (1, True), "n_frames": (1, True), "exposure_fraction": (0.0, True),
    "jitter_px": (0.0, True), "wander_px": (0.0, True), "wander_frames": (0.0, False), "full_e": (0.0, False),
    "read_e": (0.0, True), "gain_sigma": (0.0, True),
}
_WHOLE = {"n_pixels", "n_frames"}
_CHOICES = {"gap_model": ("diffuse", "collimated")}


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and np.isfinite(value)


def check_settings(who, part, settings):
    """Raise :class:`InvalidApproach` unless every setting of one part has a known name and a usable value."""
    if not isinstance(settings, dict):
        raise InvalidApproach(f"{who}: {part} must be a group of settings, such as {part}.name=value")
    cls = _PARTS[part]
    fields = {f.name: f for f in dataclasses.fields(cls)}
    extra = set(settings) - set(fields)
    if extra:
        raise InvalidApproach(f"{who}: unknown {part} setting(s) {sorted(extra)}; known: {sorted(fields)}")
    for name, value in settings.items():
        label = f"{who}: {part}.{name}"
        default = fields[name].default
        if name == "code":
            if value is None:
                continue
            ok = isinstance(value, (list, tuple)) and len(value) > 0 and all(v in (0, 1) for v in value) and any(value)
            if not ok:
                raise InvalidApproach(f"{label} must be a list of 0 and 1 with at least one 1, not {value!r}")
        elif name in _CHOICES:
            if value not in _CHOICES[name]:
                raise InvalidApproach(f"{label} must be one of {list(_CHOICES[name])}, not {value!r}")
        elif isinstance(default, bool):
            if not isinstance(value, bool):
                raise InvalidApproach(f"{label} must be true or false, not {value!r}")
        else:
            if not _is_number(value):
                raise InvalidApproach(f"{label} must be a number, not {value!r}")
            if name in _WHOLE and int(value) != value:
                raise InvalidApproach(f"{label} must be a whole number, not {value!r}")
            if name in _LIMITS:
                low, allowed = _LIMITS[name]
                if value < low or (value == low and not allowed):
                    raise InvalidApproach(f"{label} must be {'at least' if allowed else 'more than'} {low:g}, "
                                          f"not {value!r}")
            if name == "exposure_fraction" and value > 1:
                raise InvalidApproach(f"{label} is a share of a frame and cannot be more than 1, not {value!r}")
            if name == "shift_px" and value == 0:
                raise InvalidApproach(f"{label} must not be 0: the sensor has to move between frames")


_WORDS = {"true": True, "yes": True, "on": True, "false": False, "no": False, "off": False}


@dataclass(frozen=True)
class Approach:
    """One named choice of implementation and settings for each part."""

    name: str
    description: str
    hardware: tuple
    positions: str                       # "known": told the true positions; "unknown": told only the plan
    method: str
    options: dict = field(default_factory=dict)
    optics: dict = field(default_factory=dict)
    scan: dict = field(default_factory=dict)
    noise: dict = field(default_factory=dict)
    knows_materials: bool = False
    level: str = "1"
    source: str = ""                     # the text of the file, kept with the results

    def check(self, scene: Scene | None = None):
        """Raise :class:`InvalidApproach`, with the reason, if this cannot be run."""
        if self.level != "1":
            raise InvalidApproach(f"{self.name}: only level 1 exists so far, not level {self.level!r}")
        if self.positions not in ("known", "unknown"):
            raise InvalidApproach(f"{self.name}: positions must be 'known' or 'unknown', not {self.positions!r}")
        if self.method not in RECONSTRUCTIONS:
            raise InvalidApproach(f"{self.name}: unknown reconstruction {self.method!r}; "
                                  f"known: {sorted(RECONSTRUCTIONS)}")
        needs = RECONSTRUCTIONS[self.method].needs
        accepted = set(list(inspect.signature(RECONSTRUCTIONS[self.method].fn).parameters)[2:])
        extra = set(self.options) - accepted
        if extra:
            raise InvalidApproach(f"{self.name}: reconstruction {self.method!r} has no option(s) {sorted(extra)}; "
                                  f"it accepts: {sorted(accepted)}")
        if "materials" in needs and not self.knows_materials:
            raise InvalidApproach(f"{self.name}: reconstruction {self.method!r} needs the materials; "
                                  "set materials = true under [knowledge]")
        if "materials" in needs and scene is not None and scene.levels is None:
            raise InvalidApproach(f"{self.name}: reconstruction {self.method!r} needs a surface of two "
                                  f"materials, and scene {scene.name!r} is not one")
        for name, value in self.options.items():
            if not _is_number(value) or value < 0:
                raise InvalidApproach(f"{self.name}: reconstruction.{name} must be a number that is not negative, "
                                      f"not {value!r}")
        for part in _PARTS:
            check_settings(self.name, part, getattr(self, part))


def parse_approach(text, source_name="<text>", changes=()) -> Approach:
    """Read an approach from TOML text.

    ``changes`` is a list of ``"section.setting=value"`` strings applied on
    top of the file, for trying a setting without editing it:
    ``"optics.gap_nm=500"``, ``"reconstruction.smoothness=1e-3"``,
    ``"positions=unknown"``.
    """
    data = tomllib.loads(text)
    for change in changes:
        key, sep, value = change.partition("=")
        if not sep:
            raise InvalidApproach(f"{source_name}: a change is written section.setting=value, not {change!r}")
        key, value = key.strip(), value.strip()
        if not key or not value or not all(key.split(".")):
            raise InvalidApproach(f"{source_name}: a change is written section.setting=value, not {change!r}")
        if value.lower() in _WORDS:
            parsed = _WORDS[value.lower()]            # true, False, yes, off and so on
        else:
            try:
                parsed = tomllib.loads(f"v = {value}")["v"]
            except tomllib.TOMLDecodeError:
                parsed = value                        # a bare word, such as unknown
        *sections, name = key.split(".")
        target, path = data, []
        for section in sections:
            path.append(section)
            target = target.setdefault(section, {})
            if not isinstance(target, dict):
                raise InvalidApproach(f"{source_name}: {'.'.join(path)} is a single setting, not a group, "
                                      f"so {key!r} cannot be set")
        if isinstance(target.get(name), dict):
            raise InvalidApproach(f"{source_name}: {key} is a group of settings; name one, such as "
                                  f"{key}.{next(iter(target[name]), 'setting')}=value")
        target[name] = parsed
    extra = set(data) - _TOP
    if extra:
        raise InvalidApproach(f"{source_name}: unknown entries {sorted(extra)}")
    for key in ("name", "description", "reconstruction"):
        if key not in data:
            raise InvalidApproach(f"{source_name}: missing {key!r}")
    for group in ("reconstruction", "optics", "scan", "noise", "knowledge"):
        if not isinstance(data.get(group, {}), dict):
            raise InvalidApproach(f"{source_name}: {group} is a group of settings, written {group}.setting=value")
    materials = data.get("knowledge", {}).get("materials", False)
    if not isinstance(materials, bool):
        raise InvalidApproach(f"{source_name}: knowledge.materials must be true or false, not {materials!r}")
    recon = dict(data["reconstruction"])
    if "method" not in recon:
        raise InvalidApproach(f"{source_name}: [reconstruction] needs a method")
    scan = dict(data.get("scan", {}))
    if "code" in scan:
        scan["code"] = tuple(scan["code"])
    approach = Approach(
        name=data["name"], description=data["description"], hardware=tuple(data.get("hardware", ())),
        positions=data.get("positions", "known"), method=recon.pop("method"), options=recon,
        optics=dict(data.get("optics", {})), scan=scan, noise=dict(data.get("noise", {})),
        knows_materials=bool(data.get("knowledge", {}).get("materials", False)),
        level=str(data.get("level", "1")), source=text)
    approach.check()
    return approach


def load_approach(path, changes=()) -> Approach:
    path = Path(path)
    return parse_approach(path.read_text(), path.name, changes)


# ----------------------------------------------------------------- running

@dataclass(frozen=True)
class Condition:
    """Circumstances outside the approach's control, applied alike to every approach.

    Each of ``optics``, ``scan`` and ``noise`` holds settings that replace the
    defaults: light level, motion errors, pixel edge softness and so on.
    """

    name: str
    description: str = ""
    optics: dict = field(default_factory=dict)
    scan: dict = field(default_factory=dict)
    noise: dict = field(default_factory=dict)


def _build(approach: Approach, condition: Condition):
    parts = {}
    for part, cls in _PARTS.items():
        mine, theirs = getattr(approach, part), getattr(condition, part)
        both = set(mine) & set(theirs)
        if both:
            raise InvalidApproach(f"{approach.name} and condition {condition.name!r} both set {part} "
                                  f"{sorted(both)}; a condition may not override an approach's own choice")
        check_settings(f"condition {condition.name!r}", part, theirs)
        parts[part] = cls(**{**theirs, **mine})
    return parts["optics"], parts["scan"], parts["noise"]


def simulate(approach: Approach, scene: Scene, condition: Condition, seed=0) -> l1.Frames1D:
    """The readings this approach's instrument would record of the scene."""
    approach.check(scene)
    optics, scan, noise = _build(approach, condition)
    return l1.simulate(scene.surface, scene.dx_nm, optics, scan, noise, seed=seed)


def believed_frames(approach: Approach, frames: l1.Frames1D) -> l1.Frames1D:
    """The readings as the reconstruction receives them: no truth attached.

    Positions are the true ones if the approach is told them, and otherwise
    the plan: constant speed from the planned start.
    """
    positions = frames.positions_nm if approach.positions == "known" else l1.nominal_positions(frames)
    return dataclasses.replace(frames, positions_nm=np.array(positions, dtype=float), truth={})


def reconstruct(approach: Approach, scene: Scene, frames: l1.Frames1D):
    """Run the approach's reconstruction. Returns ``(surface, positions or None)``."""
    recon = RECONSTRUCTIONS[approach.method]
    levels = scene.levels if approach.knows_materials else None
    return recon.fn(believed_frames(approach, frames), levels, **approach.options)
