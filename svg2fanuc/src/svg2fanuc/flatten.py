"""Adaptive curve flattening in millimetres (section 7.4 of the specification).

Flattening runs *after* the mm scale is known: the caller passes ``to_mm`` and
all tolerances are physical. Straight ``Line`` segments are never subdivided.
Cubic/quadratic Bezier and elliptical arcs are recursively split until, at the
same time:

  * the maximum deviation from the chord is ``<= flatness_mm``;
  * the chord length is ``<= max_segment_mm``;
  * recursion depth is ``<= max_subdivision_depth``.

Hitting the depth limit before the tolerance rejects the job (GEOM_FLATTEN_LIMIT).
"""

from __future__ import annotations

from collections.abc import Callable

from svgelements import Arc, CubicBezier, Line, QuadraticBezier

from .errors import FlattenLimitError
from .geometry import Point2, dist, point_segment_distance

ToMm = Callable[[Point2], Point2]

_CURVE_TYPES = (CubicBezier, QuadraticBezier, Arc)


def _xy(pt) -> Point2:
    return (float(pt.x), float(pt.y))


class FlattenStats:
    def __init__(self) -> None:
        self.max_error_mm = 0.0
        self.segments = 0


def flatten_subpath(
    segments: list,
    to_mm: ToMm,
    *,
    flatness_mm: float,
    max_segment_mm: float,
    max_depth: int,
    element_id: str | None = None,
    stats: FlattenStats | None = None,
) -> list[Point2]:
    """Return the flattened polyline (mm) for one subpath's drawable segments."""
    stats = stats or FlattenStats()
    points: list[Point2] = []
    for seg in segments:
        p0 = _xy(seg.point(0.0))
        p1 = _xy(seg.point(1.0))
        m0 = to_mm(p0)
        m1 = to_mm(p1)
        if not points:
            points.append(m0)
        if isinstance(seg, Line) or not isinstance(seg, _CURVE_TYPES):
            points.append(m1)
            stats.segments += 1
            continue
        _recurse(
            seg, to_mm, 0.0, 1.0, m0, m1, 0,
            flatness_mm, max_segment_mm, max_depth, element_id, points, stats,
        )
    return points


def _recurse(
    seg,
    to_mm: ToMm,
    t0: float,
    t1: float,
    m0: Point2,
    m1: Point2,
    depth: int,
    flatness_mm: float,
    max_segment_mm: float,
    max_depth: int,
    element_id: str | None,
    out: list[Point2],
    stats: FlattenStats,
) -> None:
    tm = 0.5 * (t0 + t1)
    mm = to_mm(_xy(seg.point(tm)))
    deviation = point_segment_distance(mm, m0, m1)
    chord = dist(m0, m1)
    if deviation <= flatness_mm and chord <= max_segment_mm:
        out.append(m1)
        stats.segments += 1
        stats.max_error_mm = max(stats.max_error_mm, deviation)
        return
    if depth >= max_depth:
        raise FlattenLimitError(
            f"curve flattening hit depth {max_depth} before reaching "
            f"flatness {flatness_mm} mm (deviation {deviation:.4f} mm, "
            f"chord {chord:.3f} mm)",
            element_id=element_id,
        )
    _recurse(seg, to_mm, t0, tm, m0, mm, depth + 1, flatness_mm, max_segment_mm,
             max_depth, element_id, out, stats)
    _recurse(seg, to_mm, tm, t1, mm, m1, depth + 1, flatness_mm, max_segment_mm,
             max_depth, element_id, out, stats)
