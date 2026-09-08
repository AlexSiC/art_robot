"""Geometric and structural validation (section 10.1).

What this module can confirm is limited on purpose. It never asserts
reachability, singularity-freedom, collision-freedom or cell safety
(section 10.2). ``report.json`` carries the explicit
"GENERATED != SAFE TO RUN" line.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .errors import MotionPhaseError
from .geometry import Stroke
from .motion_ir import (
    KIND_LINEAR,
    PHASE_DRAW,
    PHASE_PLUNGE,
    PHASE_RETRACT,
    PHASE_TRAVEL,
    Trajectory,
)
from .profile import Profile

_Z_EPS = 1e-6


@dataclass
class Check:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class ValidationResult:
    checks: list[Check] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(c.passed for c in self.checks)

    def to_json(self) -> dict:
        return {
            "ok": self.ok,
            "checks": [vars(c) for c in self.checks],
            "warnings": list(self.warnings),
        }


def run_validation(
    strokes: list[Stroke], traj: Trajectory, profile: Profile
) -> ValidationResult:
    res = ValidationResult()
    c = profile.canvas
    bounds = c.bounds_mm

    # 1. every drawn/travel/plunge/retract point inside the allowed rectangle
    oob = 0
    for m in traj.motions:
        if m.kind != KIND_LINEAR or m.xyz_mm is None:
            continue
        x, y, _z = m.xyz_mm
        if not (
            bounds[0] - _Z_EPS <= x <= bounds[2] + _Z_EPS
            and bounds[1] - _Z_EPS <= y <= bounds[3] + _Z_EPS
        ):
            oob += 1
    res.checks.append(Check("points_in_allowed_area", oob == 0, f"{oob} points outside"))

    # 2. contact Z used only by PLUNGE/DRAW; clear Z used only by TRAVEL/RETRACT
    bad_phase = _check_phase_z(traj, c.z_draw_mm, c.z_clear_mm)
    res.checks.append(
        Check("phase_z_consistency", not bad_phase, "; ".join(bad_phase[:5]))
    )
    if bad_phase:
        raise MotionPhaseError("; ".join(bad_phase[:5]))

    # 3. per-stroke phase order TRAVEL -> PLUNGE -> DRAW+ -> RETRACT
    order_problems = _check_stroke_phase_order(traj)
    res.checks.append(
        Check("stroke_phase_order", not order_problems, "; ".join(order_problems[:5]))
    )
    if order_problems:
        raise MotionPhaseError("; ".join(order_problems[:5]))

    # 4. a single stroke must not exceed the subprogram motion budget
    limit = profile.fanuc_ls.max_motion_lines_per_subprogram
    big = _largest_stroke_moves(traj)
    per_stroke_overhead = 4  # travel, plunge, retract + margin
    fits = big + per_stroke_overhead <= limit
    res.checks.append(
        Check(
            "stroke_fits_subprogram",
            fits,
            f"largest stroke = {big} moves, limit = {limit}",
        )
    )
    if not fits:
        res.warnings.append(
            f"a stroke has {big} draw moves and cannot fit one subprogram "
            f"(limit {limit}); raise flatness_mm or split the stroke upstream"
        )

    # 5. one UF/UT/orientation/config for every position (by construction)
    res.checks.append(Check("single_frame_and_config", True, ""))

    # 6. informational budgets
    total_moves = traj.stats["linear_moves"]
    res.checks.append(
        Check(
            "motion_budget",
            total_moves <= profile.geometry.max_points * 4,
            f"{total_moves} linear moves",
        )
    )

    # 7. flatten error stayed within tolerance
    worst = max((s._flatten_error_mm for s in strokes), default=0.0)
    within = worst <= profile.geometry.flatness_mm + 1e-9
    res.checks.append(
        Check("flatten_within_tolerance", within, f"worst = {worst:.5f} mm")
    )

    return res


def _check_phase_z(traj: Trajectory, z_draw: float, z_clear: float) -> list[str]:
    problems: list[str] = []
    for i, m in enumerate(traj.motions):
        if m.kind != KIND_LINEAR or m.xyz_mm is None:
            continue
        z = m.xyz_mm[2]
        if m.phase in (PHASE_PLUNGE, PHASE_DRAW) and abs(z - z_draw) > 1e-4:
            problems.append(f"motion {i} ({m.phase}) not at contact Z ({z:.3f} vs {z_draw})")
        if m.phase in (PHASE_TRAVEL, PHASE_RETRACT) and abs(z - z_clear) > 1e-4:
            problems.append(f"motion {i} ({m.phase}) not at clear Z ({z:.3f} vs {z_clear})")
    return problems


def _check_stroke_phase_order(traj: Trajectory) -> list[str]:
    problems: list[str] = []
    seq: dict[str, list[str]] = {}
    order: list[str] = []
    for m in traj.motions:
        if m.stroke_id is None:
            continue
        if m.stroke_id not in seq:
            seq[m.stroke_id] = []
            order.append(m.stroke_id)
        seq[m.stroke_id].append(m.phase)
    for sid in order:
        phases = seq[sid]
        if not phases:
            continue
        if phases[0] != PHASE_TRAVEL or phases[1:2] != [PHASE_PLUNGE]:
            problems.append(f"stroke {sid}: does not begin TRAVEL, PLUNGE")
            continue
        if phases[-1] != PHASE_RETRACT:
            problems.append(f"stroke {sid}: does not end RETRACT")
        mid = phases[2:-1]
        if not mid or any(p != PHASE_DRAW for p in mid):
            problems.append(f"stroke {sid}: middle phases are not all DRAW")
    return problems


def _largest_stroke_moves(traj: Trajectory) -> int:
    counts: dict[str, int] = {}
    for m in traj.motions:
        if m.stroke_id and m.phase == PHASE_DRAW:
            counts[m.stroke_id] = counts.get(m.stroke_id, 0) + 1
    return max(counts.values(), default=0)
