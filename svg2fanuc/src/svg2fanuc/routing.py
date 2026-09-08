"""Stroke ordering (section 7.5).

Routing may reorder strokes and reverse open strokes; it must never change a
stroke's internal geometry, split it, or merge it. ``preserve`` keeps document
order. ``nearest`` does a greedy nearest-endpoint pass plus a bounded 2-opt on
the inter-stroke gaps only.
"""

from __future__ import annotations

from dataclasses import dataclass

from .geometry import Point2, Stroke, dist
from .profile import RoutingSpec


@dataclass
class RoutingResult:
    strokes: list[Stroke]
    travel_before_mm: float
    travel_after_mm: float
    mode: str
    reversed_count: int


def _travel_length(strokes: list[Stroke], start: Point2) -> float:
    total = 0.0
    cursor = start
    for s in strokes:
        total += dist(cursor, s.start)
        cursor = s.end
    return total


def route(strokes: list[Stroke], spec: RoutingSpec) -> RoutingResult:
    start = spec.travel_start_xy_mm
    before = _travel_length(strokes, start)

    if spec.mode == "preserve" or len(strokes) < 2:
        return RoutingResult(strokes, before, before, spec.mode, 0)

    ordered, reversed_count = _greedy_nearest(strokes, start)
    ordered = _two_opt(ordered, start, spec.two_opt_max_iterations)
    after = _travel_length(ordered, start)
    # Never make things worse than document order.
    if after > before:
        return RoutingResult(strokes, before, before, spec.mode, 0)
    return RoutingResult(ordered, before, after, spec.mode, reversed_count)


def _greedy_nearest(strokes: list[Stroke], start: Point2) -> tuple[list[Stroke], int]:
    remaining = list(strokes)
    ordered: list[Stroke] = []
    cursor = start
    reversed_count = 0
    while remaining:
        best_i = 0
        best_d = float("inf")
        best_rev = False
        for i, s in enumerate(remaining):
            d_start = dist(cursor, s.start)
            if d_start < best_d:
                best_d, best_i, best_rev = d_start, i, False
            if s.reversible and not s.closed:
                d_end = dist(cursor, s.end)
                if d_end < best_d:
                    best_d, best_i, best_rev = d_end, i, True
        chosen = remaining.pop(best_i)
        if chosen.closed:
            chosen = _rotate_closed_to_nearest(chosen, cursor)
        elif best_rev:
            chosen = chosen.reversed_copy()
            reversed_count += 1
        ordered.append(chosen)
        cursor = chosen.end
    return ordered, reversed_count


def _rotate_closed_to_nearest(stroke: Stroke, cursor: Point2) -> Stroke:
    pts = stroke.points[:-1] if stroke.points[0] == stroke.points[-1] else stroke.points
    best_i = min(range(len(pts)), key=lambda i: dist(cursor, pts[i]))
    return stroke.rotated_to(best_i)


def _two_opt(strokes: list[Stroke], start: Point2, max_iter: int) -> list[Stroke]:
    if len(strokes) < 3:
        return strokes
    best = list(strokes)
    best_len = _travel_length(best, start)
    it = 0
    improved = True
    while improved and it < max_iter:
        improved = False
        for i in range(len(best) - 1):
            for j in range(i + 1, len(best)):
                cand = best[:i] + [
                    _maybe_reverse(s) for s in reversed(best[i : j + 1])
                ] + best[j + 1 :]
                cand_len = _travel_length(cand, start)
                if cand_len + 1e-9 < best_len:
                    best, best_len = cand, cand_len
                    improved = True
                it += 1
                if it >= max_iter:
                    return best
    return best


def _maybe_reverse(s: Stroke) -> Stroke:
    if s.reversible and not s.closed:
        return s.reversed_copy()
    return s
