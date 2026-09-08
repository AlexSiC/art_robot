from __future__ import annotations

from collections import defaultdict, deque
from math import hypot
from typing import Iterable

import numpy as np

from .errors import VectorizationError
from .models import GraphEdge, Point, ProcessingStats, Stroke

Pixel = tuple[int, int]  # row, column


NEIGHBOR_OFFSETS: tuple[tuple[int, int], ...] = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)


def _pixel_neighbors(pixel: Pixel, pixels: set[Pixel]) -> list[Pixel]:
    y, x = pixel
    return sorted(
        (y + dy, x + dx)
        for dy, dx in NEIGHBOR_OFFSETS
        if (y + dy, x + dx) in pixels
    )


def _pair_key(a: Pixel, b: Pixel) -> tuple[Pixel, Pixel]:
    return (a, b) if a <= b else (b, a)


def _centroid(component: Iterable[Pixel]) -> Point:
    items = list(component)
    return (
        sum(pixel[1] for pixel in items) / len(items),
        sum(pixel[0] for pixel in items) / len(items),
    )


def _node_components(
    node_pixels: set[Pixel], pixels: set[Pixel]
) -> tuple[dict[Pixel, int], dict[int, Point], int]:
    mapping: dict[Pixel, int] = {}
    positions: dict[int, Point] = {}
    collapsed = 0
    remaining = set(node_pixels)
    node_id = 0
    while remaining:
        start = min(remaining)
        queue: deque[Pixel] = deque([start])
        remaining.remove(start)
        component: list[Pixel] = []
        while queue:
            pixel = queue.popleft()
            component.append(pixel)
            for neighbor in _pixel_neighbors(pixel, pixels):
                if neighbor in remaining and neighbor in node_pixels:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
        positions[node_id] = _centroid(component)
        for pixel in component:
            mapping[pixel] = node_id
        collapsed += max(0, len(component) - 1)
        node_id += 1
    return mapping, positions, collapsed


def skeleton_graph(
    skeleton: np.ndarray, stats: ProcessingStats
) -> tuple[dict[int, Point], list[GraphEdge]]:
    ys, xs = np.nonzero(skeleton)
    pixels: set[Pixel] = set(zip(ys.tolist(), xs.tolist()))
    if not pixels:
        raise VectorizationError("Пустой пиксельный граф", code="EMPTY_GRAPH")
    adjacency = {pixel: _pixel_neighbors(pixel, pixels) for pixel in pixels}
    node_pixels = {pixel for pixel, nearby in adjacency.items() if len(nearby) != 2}
    node_map, node_positions, collapsed = _node_components(node_pixels, pixels)
    stats.graph_node_pixels_collapsed = collapsed
    visited: set[tuple[Pixel, Pixel]] = set()

    # Connections inside a collapsed junction are not physical graph edges.
    for pixel in node_pixels:
        for neighbor in adjacency[pixel]:
            if neighbor in node_map and node_map[neighbor] == node_map[pixel]:
                visited.add(_pair_key(pixel, neighbor))

    edges: list[GraphEdge] = []

    def add_edge(start_node: int, end_node: int, points: list[Point]) -> None:
        compact: list[Point] = []
        for point in points:
            if not compact or point != compact[-1]:
                compact.append(point)
        if len(compact) >= 2:
            edges.append(GraphEdge(len(edges), start_node, end_node, compact))

    for node_pixel in sorted(node_pixels):
        start_node = node_map[node_pixel]
        for neighbor in adjacency[node_pixel]:
            key = _pair_key(node_pixel, neighbor)
            if key in visited:
                continue
            visited.add(key)
            points: list[Point] = [node_positions[start_node]]
            previous = node_pixel
            current = neighbor
            while True:
                if current in node_map:
                    end_node = node_map[current]
                    points.append(node_positions[end_node])
                    add_edge(start_node, end_node, points)
                    break
                points.append((float(current[1]), float(current[0])))
                candidates = [
                    item
                    for item in adjacency[current]
                    if item != previous and _pair_key(current, item) not in visited
                ]
                if not candidates:
                    # A previously traversed branch can end here; it is not a new edge.
                    break
                nxt = candidates[0]
                visited.add(_pair_key(current, nxt))
                previous, current = current, nxt

    # Remaining all-degree-2 components are closed cycles.
    for pixel in sorted(pixels):
        for neighbor in adjacency[pixel]:
            key = _pair_key(pixel, neighbor)
            if key in visited:
                continue
            loop_node = len(node_positions)
            node_positions[loop_node] = (float(pixel[1]), float(pixel[0]))
            points: list[Point] = [node_positions[loop_node]]
            start = pixel
            previous = pixel
            current = neighbor
            visited.add(key)
            guard = 0
            while True:
                guard += 1
                if guard > len(pixels) + 1:
                    raise VectorizationError(
                        "Не удалось замкнуть цикл скелета", code="GRAPH_LOOP"
                    )
                if current == start:
                    add_edge(loop_node, loop_node, points)
                    break
                points.append((float(current[1]), float(current[0])))
                candidates = [
                    item
                    for item in adjacency[current]
                    if item != previous and _pair_key(current, item) not in visited
                ]
                if not candidates:
                    break
                nxt = candidates[0]
                visited.add(_pair_key(current, nxt))
                previous, current = current, nxt

    stats.graph_nodes = len(node_positions)
    stats.graph_edges = len(edges)
    if not edges:
        raise VectorizationError(
            "Из скелета не удалось извлечь ребра", code="EMPTY_GRAPH_EDGES"
        )
    return node_positions, edges


def prune_spurs(edges: list[GraphEdge], threshold: float) -> int:
    if threshold <= 0:
        return 0
    removed = 0
    while True:
        degree: defaultdict[int, int] = defaultdict(int)
        for edge in edges:
            if not edge.active:
                continue
            if edge.start_node == edge.end_node:
                degree[edge.start_node] += 2
            else:
                degree[edge.start_node] += 1
                degree[edge.end_node] += 1
        candidates = [
            edge
            for edge in edges
            if edge.active
            and edge.start_node != edge.end_node
            and edge.length < threshold
            and (degree[edge.start_node] == 1 or degree[edge.end_node] == 1)
        ]
        if not candidates:
            return removed
        for edge in candidates:
            edge.active = False
            removed += 1


def _outward_vector(edge: GraphEdge, node: int) -> Point:
    if edge.start_node == node:
        a, b = edge.points[0], edge.points[min(1, len(edge.points) - 1)]
    else:
        a, b = edge.points[-1], edge.points[max(0, len(edge.points) - 2)]
    return (b[0] - a[0], b[1] - a[1])


def _opposition_score(a: Point, b: Point) -> float:
    la, lb = hypot(*a), hypot(*b)
    if la == 0 or lb == 0:
        return 2.0
    # Opposite vectors have cosine -1 and score 0.
    return 1.0 + (a[0] * b[0] + a[1] * b[1]) / (la * lb)


def edges_to_strokes(edges: list[GraphEdge]) -> list[Stroke]:
    active = [edge for edge in edges if edge.active]
    by_id = {edge.edge_id: edge for edge in active}
    strokes: list[Stroke] = []
    nonloops = [edge for edge in active if edge.start_node != edge.end_node]
    for edge in active:
        if edge.start_node == edge.end_node:
            points = list(edge.points)
            if len(points) > 1 and points[-1] == points[0]:
                points.pop()
            if len(points) >= 3:
                strokes.append(Stroke(points, closed=True))

    incident: defaultdict[int, list[int]] = defaultdict(list)
    for edge in nonloops:
        incident[edge.start_node].append(edge.edge_id)
        incident[edge.end_node].append(edge.edge_id)

    pair: dict[tuple[int, int], int] = {}
    for node, edge_ids in incident.items():
        remaining = sorted(edge_ids)
        candidates: list[tuple[float, int, int]] = []
        for index, first in enumerate(remaining):
            for second in remaining[index + 1 :]:
                candidates.append(
                    (
                        _opposition_score(
                            _outward_vector(by_id[first], node),
                            _outward_vector(by_id[second], node),
                        ),
                        first,
                        second,
                    )
                )
        used_at_node: set[int] = set()
        for _, first, second in sorted(candidates):
            if first in used_at_node or second in used_at_node:
                continue
            pair[(first, node)] = second
            pair[(second, node)] = first
            used_at_node.update((first, second))

    used: set[int] = set()
    for initial in sorted(nonloops, key=lambda item: item.edge_id):
        if initial.edge_id in used:
            continue
        if (initial.edge_id, initial.start_node) not in pair:
            start_node = initial.start_node
        elif (initial.edge_id, initial.end_node) not in pair:
            start_node = initial.end_node
        else:
            start_node = initial.start_node
        current = initial
        current_node = start_node
        trail: list[Point] = []
        while current.edge_id not in used:
            if current.start_node == current_node:
                oriented = current.points
                next_node = current.end_node
            else:
                oriented = list(reversed(current.points))
                next_node = current.start_node
            if not trail:
                trail.extend(oriented)
            else:
                trail.extend(oriented[1:] if trail[-1] == oriented[0] else oriented)
            used.add(current.edge_id)
            next_edge_id = pair.get((current.edge_id, next_node))
            if next_edge_id is None or next_edge_id in used:
                break
            current = by_id[next_edge_id]
            current_node = next_node
        if len(trail) >= 2:
            closed = len(trail) >= 4 and trail[0] == trail[-1]
            if closed:
                trail.pop()
            strokes.append(Stroke(trail, closed=closed))
    return strokes


def chaikin(stroke: Stroke, iterations: int) -> Stroke:
    result = stroke.copy()
    for _ in range(max(0, iterations)):
        points = result.points
        if len(points) < 3:
            break
        output: list[Point] = [] if result.closed else [points[0]]
        pairs = list(zip(points, points[1:]))
        if result.closed:
            pairs.append((points[-1], points[0]))
        for first, second in pairs:
            output.append((0.75 * first[0] + 0.25 * second[0], 0.75 * first[1] + 0.25 * second[1]))
            output.append((0.25 * first[0] + 0.75 * second[0], 0.25 * first[1] + 0.75 * second[1]))
        if not result.closed:
            output.append(points[-1])
        result = Stroke(output, result.closed, result.source_id)
    return result


def vectorize_skeleton(
    skeleton: np.ndarray,
    *,
    spur_len_px: float,
    smooth_iterations: int,
    stats: ProcessingStats,
) -> list[Stroke]:
    _, edges = skeleton_graph(skeleton, stats)
    stats.spurs_pruned = prune_spurs(edges, spur_len_px)
    strokes = edges_to_strokes(edges)
    if smooth_iterations:
        strokes = [chaikin(stroke, smooth_iterations) for stroke in strokes]
    if not strokes:
        raise VectorizationError(
            "После чистки графа не осталось штрихов", code="EMPTY_AFTER_GRAPH_CLEAN"
        )
    return strokes

