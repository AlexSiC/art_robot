from __future__ import annotations

from collections import defaultdict
from math import hypot
from typing import Iterable

from .models import Point, Stroke


def distance(a: Point, b: Point) -> float:
    return hypot(b[0] - a[0], b[1] - a[1])


def point_segment_distance(point: Point, start: Point, end: Point) -> float:
    dx, dy = end[0] - start[0], end[1] - start[1]
    denominator = dx * dx + dy * dy
    if denominator == 0:
        return distance(point, start)
    t = ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / denominator
    t = max(0.0, min(1.0, t))
    projection = (start[0] + t * dx, start[1] + t * dy)
    return distance(point, projection)


def dedupe_points(points: Iterable[Point], epsilon: float) -> list[Point]:
    output: list[Point] = []
    for point in points:
        if not output or distance(output[-1], point) > epsilon:
            output.append((float(point[0]), float(point[1])))
    return output


def _rdp_indices(points: list[Point], epsilon: float) -> list[int]:
    if len(points) <= 2 or epsilon <= 0:
        return list(range(len(points)))
    keep = {0, len(points) - 1}
    stack = [(0, len(points) - 1)]
    while stack:
        start_index, end_index = stack.pop()
        maximum = -1.0
        split_index = -1
        for index in range(start_index + 1, end_index):
            value = point_segment_distance(
                points[index], points[start_index], points[end_index]
            )
            if value > maximum:
                maximum = value
                split_index = index
        if maximum > epsilon and split_index > start_index:
            keep.add(split_index)
            stack.append((start_index, split_index))
            stack.append((split_index, end_index))
    return sorted(keep)


def _max_deviation_for_indices(points: list[Point], indices: list[int]) -> float:
    maximum = 0.0
    for first, second in zip(indices, indices[1:]):
        for index in range(first + 1, second):
            maximum = max(
                maximum,
                point_segment_distance(points[index], points[first], points[second]),
            )
    return maximum


def simplify_stroke(stroke: Stroke, tolerance: float) -> tuple[Stroke, float]:
    points = stroke.points
    if len(points) <= 2 or tolerance <= 0:
        return stroke.copy(), 0.0
    if not stroke.closed:
        indices = _rdp_indices(points, tolerance)
        deviation = _max_deviation_for_indices(points, indices)
        return Stroke([points[index] for index in indices], False, stroke.source_id), deviation

    # Split a ring into two open arcs using the vertex farthest from a stable start.
    start_index = min(range(len(points)), key=lambda index: (points[index][0], points[index][1], index))
    rotated = points[start_index:] + points[:start_index]
    opposite = max(range(1, len(rotated)), key=lambda index: distance(rotated[0], rotated[index]))
    first_arc = rotated[: opposite + 1]
    second_arc = rotated[opposite:] + [rotated[0]]
    first_indices = _rdp_indices(first_arc, tolerance)
    second_indices = _rdp_indices(second_arc, tolerance)
    simplified = [first_arc[index] for index in first_indices]
    simplified.extend(second_arc[index] for index in second_indices[1:-1])
    deviation = max(
        _max_deviation_for_indices(first_arc, first_indices),
        _max_deviation_for_indices(second_arc, second_indices),
    )
    if len(simplified) < 3:
        simplified = rotated[:3]
    return Stroke(simplified, True, stroke.source_id), deviation


def simplify_strokes(
    strokes: list[Stroke], tolerance: float, dedupe_epsilon: float
) -> tuple[list[Stroke], int, float, float]:
    output: list[Stroke] = []
    points_before = 0
    points_after = 0
    length_before = 0.0
    length_after = 0.0
    max_deviation = 0.0
    for stroke in strokes:
        cleaned = Stroke(dedupe_points(stroke.points, dedupe_epsilon), stroke.closed, stroke.source_id)
        if len(cleaned.points) < (3 if cleaned.closed else 2):
            continue
        points_before += len(cleaned.points)
        length_before += cleaned.length
        simplified, deviation = simplify_stroke(cleaned, tolerance)
        simplified.points = dedupe_points(simplified.points, dedupe_epsilon)
        if len(simplified.points) < (3 if simplified.closed else 2):
            continue
        output.append(simplified)
        points_after += len(simplified.points)
        length_after += simplified.length
        max_deviation = max(max_deviation, deviation)
    removed = points_before - points_after
    loss_ratio = (
        max(0.0, (length_before - length_after) / length_before)
        if length_before
        else 0.0
    )
    return output, removed, loss_ratio, max_deviation


def _merge_pair(first: Stroke, first_end: int, second: Stroke, second_end: int) -> Stroke:
    a = first if first_end == 1 else first.reversed()
    b = second if second_end == 0 else second.reversed()
    points = list(a.points)
    if points[-1] == b.points[0]:
        points.extend(b.points[1:])
    else:
        points.extend(b.points)
    return Stroke(points, closed=False)


def merge_strokes(strokes: list[Stroke], tolerance: float) -> tuple[list[Stroke], int]:
    if tolerance <= 0 or len(strokes) < 2:
        return [stroke.copy() for stroke in strokes], 0
    current = [stroke.copy() for stroke in strokes]
    total_merged = 0
    cell_size = tolerance
    while True:
        bins: defaultdict[tuple[int, int], list[tuple[int, int, Point]]] = defaultdict(list)
        for index, stroke in enumerate(current):
            if stroke.closed:
                continue
            for endpoint, point in ((0, stroke.start), (1, stroke.end)):
                cell = (int(point[0] // cell_size), int(point[1] // cell_size))
                bins[cell].append((index, endpoint, point))
        candidates: list[tuple[float, int, int, int, int]] = []
        seen: set[tuple[int, int, int, int]] = set()
        for cell, entries in bins.items():
            nearby: list[tuple[int, int, Point]] = []
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nearby.extend(bins.get((cell[0] + dx, cell[1] + dy), []))
            for first_index, first_end, first_point in entries:
                for second_index, second_end, second_point in nearby:
                    if first_index >= second_index:
                        continue
                    key = (first_index, first_end, second_index, second_end)
                    if key in seen:
                        continue
                    seen.add(key)
                    value = distance(first_point, second_point)
                    if value <= tolerance:
                        candidates.append(
                            (value, first_index, second_index, first_end, second_end)
                        )
        if not candidates:
            break
        used: set[int] = set()
        replacements: dict[int, Stroke] = {}
        removed: set[int] = set()
        for _, first_index, second_index, first_end, second_end in sorted(candidates):
            if first_index in used or second_index in used:
                continue
            replacements[first_index] = _merge_pair(
                current[first_index], first_end, current[second_index], second_end
            )
            removed.add(second_index)
            used.update((first_index, second_index))
            total_merged += 1
        if not removed:
            break
        current = [
            replacements.get(index, stroke)
            for index, stroke in enumerate(current)
            if index not in removed
        ]
    return current, total_merged


def filter_short_strokes(strokes: list[Stroke], minimum: float) -> tuple[list[Stroke], int]:
    kept = [stroke for stroke in strokes if stroke.length >= minimum]
    return kept, len(strokes) - len(kept)


def travel_length(strokes: list[Stroke], start: Point = (0.0, 0.0)) -> float:
    current = start
    total = 0.0
    for stroke in strokes:
        total += distance(current, stroke.start)
        current = stroke.end
    return total


def _reloop_nearest(stroke: Stroke, point: Point) -> Stroke:
    if not stroke.closed or not stroke.points:
        return stroke
    index = min(
        range(len(stroke.points)),
        key=lambda item: (distance(point, stroke.points[item]), item),
    )
    return Stroke(stroke.points[index:] + stroke.points[:index], True, stroke.source_id)


def _two_opt(strokes: list[Stroke]) -> list[Stroke]:
    """Improve an open route by deterministic 2-opt segment reversals."""
    route = [stroke.copy() for stroke in strokes]
    if len(route) < 3:
        return route
    tolerance = 1e-12
    while True:
        best: tuple[float, int, int] | None = None
        for start in range(len(route)):
            previous = (0.0, 0.0) if start == 0 else route[start - 1].end
            for end in range(start + 1, len(route)):
                old_cost = distance(previous, route[start].start)
                new_cost = distance(previous, route[end].end)
                if end + 1 < len(route):
                    following = route[end + 1].start
                    old_cost += distance(route[end].end, following)
                    new_cost += distance(route[start].start, following)
                gain = old_cost - new_cost
                candidate = (-gain, start, end)
                if gain > tolerance and (best is None or candidate < best):
                    best = candidate
        if best is None:
            return route
        _, start, end = best
        route[start : end + 1] = [
            stroke.reversed() for stroke in reversed(route[start : end + 1])
        ]


def sort_strokes(
    strokes: list[Stroke], *, reloop: bool = True, two_opt: bool = True
) -> list[Stroke]:
    """Deterministic nearest-neighbor route with optional 2-opt refinement."""
    if not strokes:
        return [stroke.copy() for stroke in strokes]
    baseline = travel_length(strokes)
    remaining = [stroke.copy() for stroke in strokes]
    output: list[Stroke] = []
    current: Point = (0.0, 0.0)

    # For the expected exhibition jobs a vectorized scan is both simple and fast.
    while remaining:
        best: tuple[float, int, int] | None = None
        for index, stroke in enumerate(remaining):
            starts = [(0, stroke.start)]
            if not stroke.closed:
                starts.append((1, stroke.end))
            for reverse, endpoint in starts:
                candidate = (distance(current, endpoint), index, reverse)
                if best is None or candidate < best:
                    best = candidate
        assert best is not None
        _, index, reverse = best
        chosen = remaining.pop(index)
        if reverse:
            chosen = chosen.reversed()
        elif reloop and chosen.closed:
            chosen = _reloop_nearest(chosen, current)
        output.append(chosen)
        current = chosen.end
    if two_opt:
        output = _two_opt(output)
    if reloop:
        current = (0.0, 0.0)
        relooped: list[Stroke] = []
        for stroke in output:
            chosen = _reloop_nearest(stroke, current)
            relooped.append(chosen)
            current = chosen.end
        output = relooped
    if travel_length(output) > baseline + 1e-12:
        return [stroke.copy() for stroke in strokes]
    return output


def bbox(strokes: list[Stroke]) -> list[float] | None:
    points = [point for stroke in strokes for point in stroke.points]
    if not points:
        return None
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return [min(xs), min(ys), max(xs), max(ys)]
