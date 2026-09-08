"""Build validated :class:`Stroke` objects (pipeline stages C-F).

Flatten each raw subpath in mm, drop numerical duplicates, discard sub-minimal
strokes, enforce the allowed rectangle and the point/stroke budgets.
"""

from __future__ import annotations

from dataclasses import dataclass

from .errors import BudgetError, SvgEmptyError
from .flatten import FlattenStats, flatten_subpath
from .geometry import Stroke, dedupe_consecutive
from .profile import Profile
from .svg_reader import ReadResult
from .transform import Placement


@dataclass
class StrokeBuildResult:
    strokes: list[Stroke]
    stats: dict


def build_strokes(
    read: ReadResult, placement: Placement, profile: Profile
) -> StrokeBuildResult:
    g = profile.geometry
    bounds = profile.canvas.bounds_mm

    strokes: list[Stroke] = []
    dropped_short = 0
    dropped_degenerate = 0
    max_flatten_error = 0.0
    fstats = FlattenStats()

    idx = 0
    for sp in read.subpaths:
        pts = flatten_subpath(
            sp.segments,
            placement.to_mm,
            flatness_mm=g.flatness_mm,
            max_segment_mm=g.max_segment_mm,
            max_depth=g.max_subdivision_depth,
            element_id=sp.source_element_id,
            stats=fstats,
        )
        pts = dedupe_consecutive(pts, g.dedupe_epsilon_mm)
        if sp.closed and len(pts) >= 3 and pts[0] != pts[-1]:
            pts.append(pts[0])
        if len(pts) < 2 or len({(round(x, 9), round(y, 9)) for x, y in pts}) < 2:
            dropped_degenerate += 1
            continue

        idx += 1
        stroke = Stroke(
            id=f"s{idx:04d}",
            points=pts,
            closed=sp.closed,
            reversible=True,
            source_element_id=sp.source_element_id,
            order_group=sp.order_group,
            _flatten_error_mm=fstats.max_error_mm,
        )
        if stroke.length() < g.min_stroke_length_mm:
            dropped_short += 1
            idx -= 1
            continue

        stroke.validate(bounds)
        strokes.append(stroke)
        max_flatten_error = max(max_flatten_error, fstats.max_error_mm)

    if not strokes:
        raise SvgEmptyError("no strokes remain after cleaning (all degenerate/too short)")

    if len(strokes) > g.max_strokes:
        raise BudgetError(
            f"stroke budget exceeded: {len(strokes)} > {g.max_strokes}",
            detail={"strokes": len(strokes), "limit": g.max_strokes},
        )
    total_points = sum(len(s.points) for s in strokes)
    if total_points > g.max_points:
        raise BudgetError(
            f"point budget exceeded: {total_points} > {g.max_points}",
            detail={"points": total_points, "limit": g.max_points},
        )
    total_draw = sum(s.length() for s in strokes)
    if total_draw > g.max_draw_length_mm:
        raise BudgetError(
            f"draw-length budget exceeded: {total_draw:.1f} mm > {g.max_draw_length_mm} mm",
            detail={"draw_length_mm": total_draw, "limit": g.max_draw_length_mm},
        )

    return StrokeBuildResult(
        strokes=strokes,
        stats={
            "strokes": len(strokes),
            "points": total_points,
            "draw_length_mm": round(total_draw, 3),
            "max_flatten_error_mm": round(max_flatten_error, 5),
            "dropped_short_strokes": dropped_short,
            "dropped_degenerate_strokes": dropped_degenerate,
        },
    )
