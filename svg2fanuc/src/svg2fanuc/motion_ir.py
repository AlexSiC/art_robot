"""Vendor-neutral motion plan (sections 6.2, 7.6, 7.7).

``trajectory.json`` built from this is the single source for every emitter. No
FANUC-specific syntax appears here.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .geometry import Stroke, dist, turn_angle_deg
from .profile import Profile

KIND_LINEAR = "LINEAR"
KIND_CALL = "CALL"
KIND_SET_FRAME = "SET_FRAME"
KIND_SET_TOOL = "SET_TOOL"
KIND_COMMENT = "COMMENT"

PHASE_ENTRY = "ENTRY"
PHASE_TRAVEL = "TRAVEL"
PHASE_PLUNGE = "PLUNGE"
PHASE_DRAW = "DRAW"
PHASE_RETRACT = "RETRACT"
PHASE_EXIT = "EXIT"

_CONTACT_PHASES = {PHASE_PLUNGE, PHASE_DRAW}


@dataclass
class Motion:
    kind: str
    phase: str
    xyz_mm: list[float] | None = None
    wpr_deg: list[float] | None = None
    speed: float | str | None = None
    termination: str = "FINE"  # FINE | CNT
    cnt: int | None = None
    stroke_id: str | None = None
    target: str | None = None  # for CALL
    text: str | None = None  # for COMMENT

    def to_json(self) -> dict:
        d = asdict(self)
        return {k: v for k, v in d.items() if v is not None}


@dataclass
class Trajectory:
    motions: list[Motion]
    frame: dict
    stats: dict = field(default_factory=dict)

    def to_json(self) -> dict:
        return {
            "schema": "svg2fanuc/trajectory@1",
            "frame": self.frame,
            "stats": self.stats,
            "motions": [m.to_json() for m in self.motions],
        }


def build_trajectory(strokes: list[Stroke], profile: Profile) -> Trajectory:
    c = profile.canvas
    m = profile.motion
    wpr = list(profile.frames.orientation_wpr_deg)
    z_draw = c.z_draw_mm
    z_clear = c.z_clear_mm

    motions: list[Motion] = []
    motions.append(Motion(KIND_SET_FRAME, PHASE_ENTRY, target=str(profile.frames.uframe_num)))
    motions.append(Motion(KIND_SET_TOOL, PHASE_ENTRY, target=str(profile.frames.utool_num)))
    motions.append(Motion(KIND_CALL, PHASE_ENTRY, target=m.entry_program))

    draw_length = 0.0
    for stroke in strokes:
        pts = stroke.points
        sx, sy = pts[0]
        ex, ey = pts[-1]

        motions.append(Motion(
            KIND_LINEAR, PHASE_TRAVEL, [sx, sy, z_clear], wpr,
            speed=m.travel_speed_mm_s, termination="FINE", stroke_id=stroke.id,
        ))
        motions.append(Motion(
            KIND_LINEAR, PHASE_PLUNGE, [sx, sy, z_draw], wpr,
            speed=m.plunge_speed_mm_s, termination="FINE", stroke_id=stroke.id,
        ))

        for i in range(1, len(pts)):
            x, y = pts[i]
            is_last = i == len(pts) - 1
            if is_last:
                term, cnt = "FINE", None
            else:
                sharp = turn_angle_deg(pts[i - 1], pts[i], pts[i + 1]) > m.sharp_corner_deg
                if sharp:
                    term, cnt = "FINE", None
                else:
                    term, cnt = "CNT", m.cnt_draw
            motions.append(Motion(
                KIND_LINEAR, PHASE_DRAW, [x, y, z_draw], wpr,
                speed=m.draw_speed_mm_s, termination=term, cnt=cnt,
                stroke_id=stroke.id,
            ))
            draw_length += dist(pts[i - 1], pts[i])

        motions.append(Motion(
            KIND_LINEAR, PHASE_RETRACT, [ex, ey, z_clear], wpr,
            speed=m.retract_speed_mm_s, termination="FINE", stroke_id=stroke.id,
        ))

    motions.append(Motion(KIND_CALL, PHASE_EXIT, target=m.exit_program))

    travel_length = _travel_length(motions)
    linear = [x for x in motions if x.kind == KIND_LINEAR]
    est_time = _estimate_time(motions)

    return Trajectory(
        motions=motions,
        frame={
            "uframe_num": profile.frames.uframe_num,
            "utool_num": profile.frames.utool_num,
            "orientation_wpr_deg": wpr,
            "config": profile.robot.config,
            "z_draw_mm": z_draw,
            "z_clear_mm": z_clear,
        },
        stats={
            "motion_count": len(motions),
            "linear_moves": len(linear),
            "draw_length_mm": round(draw_length, 3),
            "travel_length_mm": round(travel_length, 3),
            "estimated_time_s": round(est_time, 1),
        },
    )


def _travel_length(motions: list[Motion]) -> float:
    total = 0.0
    prev = None
    for mo in motions:
        if mo.kind != KIND_LINEAR or mo.xyz_mm is None:
            continue
        if prev is not None and mo.phase in (PHASE_TRAVEL, PHASE_RETRACT):
            total += _d3(prev, mo.xyz_mm)
        prev = mo.xyz_mm
    return total


def _estimate_time(motions: list[Motion]) -> float:
    total = 0.0
    prev = None
    for mo in motions:
        if mo.kind != KIND_LINEAR or mo.xyz_mm is None:
            continue
        if prev is not None and isinstance(mo.speed, (int, float)) and mo.speed > 0:
            total += _d3(prev, mo.xyz_mm) / float(mo.speed)
        prev = mo.xyz_mm
    return total


def _d3(a: list[float], b: list[float]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5
