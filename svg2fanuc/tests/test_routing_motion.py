from __future__ import annotations

from svg2fanuc.geometry import Stroke
from svg2fanuc.motion_ir import (
    KIND_LINEAR,
    PHASE_DRAW,
    PHASE_PLUNGE,
    PHASE_RETRACT,
    PHASE_TRAVEL,
    build_trajectory,
)
from svg2fanuc.profile import RoutingSpec
from svg2fanuc.routing import route


def _strokes():
    return [
        Stroke("s0001", [(10.0, 10.0), (10.0, 20.0)]),
        Stroke("s0002", [(90.0, 90.0), (90.0, 80.0)]),
        Stroke("s0003", [(12.0, 20.0), (12.0, 30.0)]),
    ]


def test_preserve_keeps_order():
    r = route(_strokes(), RoutingSpec("preserve", (0.0, 0.0), 100))
    assert [s.id for s in r.strokes] == ["s0001", "s0002", "s0003"]
    assert r.travel_after_mm == r.travel_before_mm


def test_nearest_reduces_travel():
    r = route(_strokes(), RoutingSpec("nearest", (0.0, 0.0), 200))
    assert r.travel_after_mm <= r.travel_before_mm + 1e-9
    # s0003 is next to s0001, so it should not be visited last after the far s0002
    assert [s.id for s in r.strokes][:2] == ["s0001", "s0003"]


def test_nearest_never_worse_than_preserve():
    strokes = _strokes()
    pres = route(strokes, RoutingSpec("preserve", (0.0, 0.0), 100))
    near = route(strokes, RoutingSpec("nearest", (0.0, 0.0), 200))
    assert near.travel_after_mm <= pres.travel_after_mm + 1e-9


def test_trajectory_phase_sequence(profile):
    strokes = [Stroke("s0001", [(20.0, 20.0), (40.0, 20.0), (40.0, 40.0)])]
    traj = build_trajectory(strokes, profile)
    phases = [m.phase for m in traj.motions if m.stroke_id == "s0001"]
    assert phases[0] == PHASE_TRAVEL
    assert phases[1] == PHASE_PLUNGE
    assert phases[-1] == PHASE_RETRACT
    assert set(phases[2:-1]) == {PHASE_DRAW}


def test_travel_and_retract_use_clear_z(profile):
    strokes = [Stroke("s0001", [(20.0, 20.0), (40.0, 20.0)])]
    traj = build_trajectory(strokes, profile)
    for m in traj.motions:
        if m.kind != KIND_LINEAR:
            continue
        z = m.xyz_mm[2]
        if m.phase in (PHASE_TRAVEL, PHASE_RETRACT):
            assert z == profile.canvas.z_clear_mm
        if m.phase in (PHASE_PLUNGE, PHASE_DRAW):
            assert z == profile.canvas.z_draw_mm


def test_sharp_corner_forces_fine(profile):
    # 90-degree corner in the middle -> that vertex must be FINE
    strokes = [Stroke("s0001", [(20.0, 20.0), (60.0, 20.0), (60.0, 60.0)])]
    traj = build_trajectory(strokes, profile)
    draws = [m for m in traj.motions if m.phase == PHASE_DRAW]
    assert draws[0].termination == "FINE"  # the corner point
