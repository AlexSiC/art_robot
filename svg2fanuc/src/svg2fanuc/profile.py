"""Cell profile (section 9 of the specification).

The profile is the configuration of one physical robot cell. It is versioned and
its SHA-256 goes into every job manifest. Fields marked ``TBD`` forbid
``generate --production`` but are allowed for ``inspect``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .errors import ProfileError, ProfileNotQualifiedError

_TBD = "TBD"

_CONFIG_RE_HINT = "e.g. 'N U T, 0, 0, 0'"


def _req(d: dict, key: str, path: str) -> Any:
    if key not in d:
        raise ProfileError(f"profile: missing required key '{path}{key}'")
    return d[key]


def _num(v: Any, path: str) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ProfileError(f"profile: '{path}' must be a number, got {v!r}")
    return float(v)


def _pos(v: Any, path: str) -> float:
    f = _num(v, path)
    if f <= 0:
        raise ProfileError(f"profile: '{path}' must be > 0, got {f}")
    return f


def _int(v: Any, path: str) -> int:
    if isinstance(v, bool) or not isinstance(v, int):
        raise ProfileError(f"profile: '{path}' must be an integer, got {v!r}")
    return v


@dataclass(frozen=True)
class RobotSpec:
    vendor: str
    model: str
    controller: str
    controller_software: str
    config: str

    @property
    def has_tbd(self) -> bool:
        return _TBD in (
            self.model,
            self.controller,
            self.controller_software,
            self.config,
        )


@dataclass(frozen=True)
class FramesSpec:
    uframe_num: int
    utool_num: int
    orientation_wpr_deg: tuple[float, float, float]


@dataclass(frozen=True)
class CanvasSpec:
    width_mm: float
    height_mm: float
    margin_mm: float
    fit: str  # contain | actual | stretch
    align: str  # center | top_left | offset
    z_draw_mm: float
    z_clear_mm: float
    align_offset_mm: tuple[float, float] = (0.0, 0.0)
    svg_units_per_mm: float = 1.0

    @property
    def area_width_mm(self) -> float:
        return self.width_mm - 2.0 * self.margin_mm

    @property
    def area_height_mm(self) -> float:
        return self.height_mm - 2.0 * self.margin_mm

    @property
    def bounds_mm(self) -> tuple[float, float, float, float]:
        """(xmin, ymin, xmax, ymax) of the allowed drawing rectangle."""
        return (
            self.margin_mm,
            self.margin_mm,
            self.width_mm - self.margin_mm,
            self.height_mm - self.margin_mm,
        )


@dataclass(frozen=True)
class GeometrySpec:
    flatness_mm: float
    max_segment_mm: float
    dedupe_epsilon_mm: float
    min_stroke_length_mm: float
    max_subdivision_depth: int
    max_strokes: int
    max_points: int
    max_draw_length_mm: float


@dataclass(frozen=True)
class RoutingSpec:
    mode: str  # preserve | nearest
    travel_start_xy_mm: tuple[float, float]
    two_opt_max_iterations: int


@dataclass(frozen=True)
class MotionSpec:
    draw_speed_mm_s: float
    plunge_speed_mm_s: float
    retract_speed_mm_s: float
    travel_speed_mm_s: float
    cnt_draw: int
    sharp_corner_deg: float
    entry_program: str
    exit_program: str


@dataclass(frozen=True)
class FanucLsSpec:
    program_name_prefix: str
    program_name_max_chars: int
    max_motion_lines_per_subprogram: int
    encoding: str
    decimal_places_mm: int
    decimal_places_deg: int


@dataclass(frozen=True)
class CompileSpec:
    enabled: bool
    maketp_exe: str | None
    robot_ini: str | None


@dataclass(frozen=True)
class SecuritySpec:
    max_input_bytes: int
    max_xml_depth: int
    max_elements: int
    max_attribute_chars: int


@dataclass(frozen=True)
class Profile:
    schema_version: int
    cell_id: str
    robot: RobotSpec
    frames: FramesSpec
    canvas: CanvasSpec
    geometry: GeometrySpec
    routing: RoutingSpec
    motion: MotionSpec
    fanuc_ls: FanucLsSpec
    compile: CompileSpec
    security: SecuritySpec
    raw_bytes: bytes = field(repr=False, default=b"")
    source_path: str | None = None

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.raw_bytes).hexdigest()

    def qualified_for_production(self) -> tuple[bool, list[str]]:
        problems: list[str] = []
        if self.robot.has_tbd:
            problems.append("robot.* contains TBD")
        if self.fit_needs_units() and self.canvas.svg_units_per_mm <= 0:
            problems.append("canvas.fit=actual requires positive svg_units_per_mm")
        return (not problems, problems)

    def fit_needs_units(self) -> bool:
        return self.canvas.fit == "actual"

    def ensure_production_ready(self) -> None:
        ok, problems = self.qualified_for_production()
        if not ok:
            raise ProfileNotQualifiedError(
                "profile is not qualified for production generation: "
                + "; ".join(problems)
            )


def _tuple2(v: Any, path: str) -> tuple[float, float]:
    if not isinstance(v, (list, tuple)) or len(v) != 2:
        raise ProfileError(f"profile: '{path}' must be a list of 2 numbers")
    return (_num(v[0], path), _num(v[1], path))


def _tuple3(v: Any, path: str) -> tuple[float, float, float]:
    if not isinstance(v, (list, tuple)) or len(v) != 3:
        raise ProfileError(f"profile: '{path}' must be a list of 3 numbers")
    return (_num(v[0], path), _num(v[1], path), _num(v[2], path))


def load_profile(path: str | Path) -> Profile:
    p = Path(path)
    try:
        raw = p.read_bytes()
    except OSError as exc:  # pragma: no cover - trivial
        raise ProfileError(f"cannot read profile: {exc}") from exc
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ProfileError(f"profile is not valid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ProfileError("profile root must be a mapping")

    return parse_profile(data, raw_bytes=raw, source_path=str(p))


def parse_profile(
    data: dict, *, raw_bytes: bytes = b"", source_path: str | None = None
) -> Profile:
    schema_version = _int(_req(data, "schema_version", ""), "schema_version")
    if schema_version != 1:
        raise ProfileError(f"unsupported profile schema_version {schema_version}")

    cell_id = str(_req(data, "cell_id", ""))

    r = _req(data, "robot", "")
    robot = RobotSpec(
        vendor=str(r.get("vendor", "FANUC")),
        model=str(_req(r, "model", "robot.")),
        controller=str(_req(r, "controller", "robot.")),
        controller_software=str(r.get("controller_software", _TBD)),
        config=str(_req(r, "config", "robot.")),
    )
    if robot.vendor.upper() != "FANUC":
        raise ProfileError(
            f"robot.vendor must be FANUC for this module, got {robot.vendor!r}"
        )
    if robot.config != _TBD:
        _validate_config_string(robot.config)

    fr = _req(data, "frames", "")
    frames = FramesSpec(
        uframe_num=_int(_req(fr, "uframe_num", "frames."), "frames.uframe_num"),
        utool_num=_int(_req(fr, "utool_num", "frames."), "frames.utool_num"),
        orientation_wpr_deg=_tuple3(
            _req(fr, "orientation_wpr_deg", "frames."), "frames.orientation_wpr_deg"
        ),
    )

    c = _req(data, "canvas", "")
    fit = str(c.get("fit", "contain"))
    if fit not in ("contain", "actual", "stretch"):
        raise ProfileError(f"canvas.fit must be contain|actual|stretch, got {fit!r}")
    align = str(c.get("align", "center"))
    if align not in ("center", "top_left", "offset"):
        raise ProfileError(
            f"canvas.align must be center|top_left|offset, got {align!r}"
        )
    canvas = CanvasSpec(
        width_mm=_pos(_req(c, "width_mm", "canvas."), "canvas.width_mm"),
        height_mm=_pos(_req(c, "height_mm", "canvas."), "canvas.height_mm"),
        margin_mm=_num(c.get("margin_mm", 0.0), "canvas.margin_mm"),
        fit=fit,
        align=align,
        z_draw_mm=_num(_req(c, "z_draw_mm", "canvas."), "canvas.z_draw_mm"),
        z_clear_mm=_num(_req(c, "z_clear_mm", "canvas."), "canvas.z_clear_mm"),
        align_offset_mm=_tuple2(
            c.get("align_offset_mm", [0.0, 0.0]), "canvas.align_offset_mm"
        ),
        svg_units_per_mm=_num(
            c.get("svg_units_per_mm", 1.0), "canvas.svg_units_per_mm"
        ),
    )
    if canvas.margin_mm < 0:
        raise ProfileError("canvas.margin_mm must be >= 0")
    if canvas.area_width_mm <= 0 or canvas.area_height_mm <= 0:
        raise ProfileError("canvas margin leaves no drawable area")
    if canvas.z_clear_mm <= canvas.z_draw_mm:
        raise ProfileError("canvas.z_clear_mm must be greater than z_draw_mm")

    g = _req(data, "geometry", "")
    geometry = GeometrySpec(
        flatness_mm=_pos(_req(g, "flatness_mm", "geometry."), "geometry.flatness_mm"),
        max_segment_mm=_pos(
            _req(g, "max_segment_mm", "geometry."), "geometry.max_segment_mm"
        ),
        dedupe_epsilon_mm=_pos(
            _req(g, "dedupe_epsilon_mm", "geometry."), "geometry.dedupe_epsilon_mm"
        ),
        min_stroke_length_mm=_num(
            g.get("min_stroke_length_mm", 0.0), "geometry.min_stroke_length_mm"
        ),
        max_subdivision_depth=_int(
            _req(g, "max_subdivision_depth", "geometry."),
            "geometry.max_subdivision_depth",
        ),
        max_strokes=_int(_req(g, "max_strokes", "geometry."), "geometry.max_strokes"),
        max_points=_int(_req(g, "max_points", "geometry."), "geometry.max_points"),
        max_draw_length_mm=_pos(
            _req(g, "max_draw_length_mm", "geometry."), "geometry.max_draw_length_mm"
        ),
    )
    if geometry.max_segment_mm <= geometry.flatness_mm:
        raise ProfileError("geometry.max_segment_mm must exceed flatness_mm")

    rt = _req(data, "routing", "")
    mode = str(rt.get("mode", "preserve"))
    if mode not in ("preserve", "nearest"):
        raise ProfileError(f"routing.mode must be preserve|nearest, got {mode!r}")
    routing = RoutingSpec(
        mode=mode,
        travel_start_xy_mm=_tuple2(
            rt.get("travel_start_xy_mm", [0.0, 0.0]), "routing.travel_start_xy_mm"
        ),
        two_opt_max_iterations=_int(
            rt.get("two_opt_max_iterations", 100), "routing.two_opt_max_iterations"
        ),
    )

    m = _req(data, "motion", "")
    motion = MotionSpec(
        draw_speed_mm_s=_pos(_req(m, "draw_speed_mm_s", "motion."), "motion.draw_speed_mm_s"),
        plunge_speed_mm_s=_pos(
            _req(m, "plunge_speed_mm_s", "motion."), "motion.plunge_speed_mm_s"
        ),
        retract_speed_mm_s=_pos(
            _req(m, "retract_speed_mm_s", "motion."), "motion.retract_speed_mm_s"
        ),
        travel_speed_mm_s=_pos(
            _req(m, "travel_speed_mm_s", "motion."), "motion.travel_speed_mm_s"
        ),
        cnt_draw=_int(_req(m, "cnt_draw", "motion."), "motion.cnt_draw"),
        sharp_corner_deg=_num(m.get("sharp_corner_deg", 55.0), "motion.sharp_corner_deg"),
        entry_program=str(m.get("entry_program", "CELL_IN")),
        exit_program=str(m.get("exit_program", "CELL_OUT")),
    )
    if not 0 <= motion.cnt_draw <= 100:
        raise ProfileError("motion.cnt_draw must be within 0..100")

    fl = _req(data, "fanuc_ls", "")
    fanuc_ls = FanucLsSpec(
        program_name_prefix=str(fl.get("program_name_prefix", "ART")),
        program_name_max_chars=_int(
            fl.get("program_name_max_chars", 8), "fanuc_ls.program_name_max_chars"
        ),
        max_motion_lines_per_subprogram=_int(
            _req(fl, "max_motion_lines_per_subprogram", "fanuc_ls."),
            "fanuc_ls.max_motion_lines_per_subprogram",
        ),
        encoding=str(fl.get("encoding", "ascii")),
        decimal_places_mm=_int(
            fl.get("decimal_places_mm", 3), "fanuc_ls.decimal_places_mm"
        ),
        decimal_places_deg=_int(
            fl.get("decimal_places_deg", 3), "fanuc_ls.decimal_places_deg"
        ),
    )
    _validate_program_name_prefix(fanuc_ls)
    if fanuc_ls.max_motion_lines_per_subprogram < 20:
        raise ProfileError(
            "fanuc_ls.max_motion_lines_per_subprogram is implausibly small"
        )

    cp = data.get("compile", {}) or {}
    compile_spec = CompileSpec(
        enabled=bool(cp.get("enabled", False)),
        maketp_exe=(str(cp["maketp_exe"]) if cp.get("maketp_exe") else None),
        robot_ini=(str(cp["robot_ini"]) if cp.get("robot_ini") else None),
    )
    if compile_spec.enabled and not (compile_spec.maketp_exe and compile_spec.robot_ini):
        raise ProfileError(
            "compile.enabled requires both maketp_exe and robot_ini"
        )

    sec = data.get("security", {}) or {}
    security = SecuritySpec(
        max_input_bytes=_int(sec.get("max_input_bytes", 10 * 1024 * 1024), "security.max_input_bytes"),
        max_xml_depth=_int(sec.get("max_xml_depth", 32), "security.max_xml_depth"),
        max_elements=_int(sec.get("max_elements", 20000), "security.max_elements"),
        max_attribute_chars=_int(
            sec.get("max_attribute_chars", 1_000_000), "security.max_attribute_chars"
        ),
    )

    return Profile(
        schema_version=schema_version,
        cell_id=cell_id,
        robot=robot,
        frames=frames,
        canvas=canvas,
        geometry=geometry,
        routing=routing,
        motion=motion,
        fanuc_ls=fanuc_ls,
        compile=compile_spec,
        security=security,
        raw_bytes=raw_bytes,
        source_path=source_path,
    )


def _validate_config_string(config: str) -> None:
    """Very light check of a FANUC CONFIG string like 'N U T, 0, 0, 0'."""
    parts = [p.strip() for p in config.split(",")]
    if len(parts) != 4:
        raise ProfileError(
            f"robot.config must look like {_CONFIG_RE_HINT}, got {config!r}"
        )
    flags = parts[0].split()
    if len(flags) != 3 or any(f not in ("N", "F", "U", "D", "T", "B") for f in flags):
        raise ProfileError(
            f"robot.config flags must be 3 of N/F, U/D, T/B ({_CONFIG_RE_HINT})"
        )
    for turn in parts[1:]:
        try:
            int(turn)
        except ValueError as exc:
            raise ProfileError(
                f"robot.config turn numbers must be integers, got {turn!r}"
            ) from exc


def _validate_program_name_prefix(fl: FanucLsSpec) -> None:
    if not fl.program_name_prefix:
        raise ProfileError("fanuc_ls.program_name_prefix must not be empty")
    if not fl.program_name_prefix.isascii() or not fl.program_name_prefix.isalnum():
        raise ProfileError("fanuc_ls.program_name_prefix must be ASCII alphanumeric")
    if fl.program_name_prefix[0].isdigit():
        raise ProfileError("fanuc_ls.program_name_prefix must start with a letter")
    if len(fl.program_name_prefix) + 5 > fl.program_name_max_chars:
        raise ProfileError(
            "fanuc_ls.program_name_prefix leaves no room for a 5-digit job number "
            f"within program_name_max_chars={fl.program_name_max_chars}"
        )
