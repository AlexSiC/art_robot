from __future__ import annotations

from collections import defaultdict, deque
from math import acos, degrees, floor, hypot
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


def merge_nearby_junction_nodes(
    positions: dict[int, Point], edges: list[GraphEdge], threshold: float
) -> tuple[dict[int, Point], list[GraphEdge], int]:
    """Collapse clusters of nearby graph junctions without merging endpoints."""
    if threshold <= 0 or len(positions) < 2:
        return positions, edges, 0
    degree: defaultdict[int, int] = defaultdict(int)
    for edge in edges:
        if edge.start_node == edge.end_node:
            degree[edge.start_node] += 2
        else:
            degree[edge.start_node] += 1
            degree[edge.end_node] += 1
    junctions = sorted(node for node in positions if degree[node] >= 3)
    if len(junctions) < 2:
        return positions, edges, 0

    parent = {node: node for node in positions}
    members = {node: {node} for node in positions}

    def find(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(first: int, second: int) -> None:
        first_root, second_root = find(first), find(second)
        if first_root == second_root:
            return
        low, high = sorted((first_root, second_root))
        if any(
            hypot(
                positions[left][0] - positions[right][0],
                positions[left][1] - positions[right][1],
            )
            > threshold
            for left in members[low]
            for right in members[high]
        ):
            return
        parent[high] = low
        members[low].update(members.pop(high))

    bins: defaultdict[tuple[int, int], list[int]] = defaultdict(list)
    for node in junctions:
        x, y = positions[node]
        cell = (floor(x / threshold), floor(y / threshold))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for other in bins.get((cell[0] + dx, cell[1] + dy), []):
                    if hypot(x - positions[other][0], y - positions[other][1]) <= threshold:
                        union(node, other)
        bins[cell].append(node)

    groups: defaultdict[int, list[int]] = defaultdict(list)
    for node in sorted(positions):
        groups[find(node)].append(node)
    merged_count = sum(len(group) - 1 for group in groups.values())
    if merged_count == 0:
        return positions, edges, 0

    node_mapping: dict[int, int] = {}
    merged_positions: dict[int, Point] = {}
    for new_node, (_, members) in enumerate(sorted(groups.items())):
        merged_positions[new_node] = (
            sum(positions[node][0] for node in members) / len(members),
            sum(positions[node][1] for node in members) / len(members),
        )
        for node in members:
            node_mapping[node] = new_node

    merged_edges: list[GraphEdge] = []
    for edge in edges:
        start = node_mapping[edge.start_node]
        end = node_mapping[edge.end_node]
        # A connector internal to a merged junction is not a drawable loop.
        if start == end and edge.start_node != edge.end_node:
            continue
        points = list(edge.points)
        points[0] = merged_positions[start]
        points[-1] = merged_positions[end]
        while (
            len(points) > 2
            and hypot(
                points[1][0] - merged_positions[start][0],
                points[1][1] - merged_positions[start][1],
            )
            <= threshold
        ):
            points.pop(1)
        while (
            len(points) > 2
            and hypot(
                points[-2][0] - merged_positions[end][0],
                points[-2][1] - merged_positions[end][1],
            )
            <= threshold
        ):
            points.pop(-2)
        merged_edges.append(
            GraphEdge(len(merged_edges), start, end, points, edge.active)
        )
    return merged_positions, merged_edges, merged_count


def remove_collinear_points(points: list[Point], max_angle_deg: float) -> list[Point]:
    """Remove interior points whose local direction change is negligible."""
    if max_angle_deg <= 0 or len(points) <= 2:
        return list(points)
    output: list[Point] = []
    for point in points:
        output.append(point)
        while len(output) >= 3:
            first, middle, last = output[-3:]
            a = (middle[0] - first[0], middle[1] - first[1])
            b = (last[0] - middle[0], last[1] - middle[1])
            lengths = hypot(*a) * hypot(*b)
            if lengths == 0:
                output.pop(-2)
                continue
            cosine = max(-1.0, min(1.0, (a[0] * b[0] + a[1] * b[1]) / lengths))
            if degrees(acos(cosine)) > max_angle_deg:
                break
            output.pop(-2)
    return output


def _outward_vector(edge: GraphEdge, node: int) -> Point:
    if edge.start_node == node:
        points = edge.points
    else:
        points = list(reversed(edge.points))
    a = points[0]
    b = points[-1]
    for candidate in points[1:]:
        if hypot(candidate[0] - a[0], candidate[1] - a[1]) >= 64.0:
            b = candidate
            break
    return (b[0] - a[0], b[1] - a[1])


def _opposition_score(a: Point, b: Point) -> float:
    la, lb = hypot(*a), hypot(*b)
    if la == 0 or lb == 0:
        return 2.0
    # Opposite vectors have cosine -1 and score 0.
    return 1.0 + (a[0] * b[0] + a[1] * b[1]) / (la * lb)


def _opposition_deviation_deg(first: Point, second: Point) -> float:
    first_len, second_len = hypot(*first), hypot(*second)
    if first_len == 0 or second_len == 0:
        return 180.0
    cosine = max(
        -1.0,
        min(1.0, (first[0] * second[0] + first[1] * second[1]) / (first_len * second_len)),
    )
    return degrees(acos(-cosine))


def edges_to_strokes(
    edges: list[GraphEdge], *, junction_collinear_deg: float = 180.0
) -> list[Stroke]:
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
        if len(remaining) == 2:
            first, second = remaining
            pair[(first, node)] = second
            pair[(second, node)] = first
            continue
        candidates: list[tuple[float, int, int]] = []
        for index, first in enumerate(remaining):
            for second in remaining[index + 1 :]:
                first_vector = _outward_vector(by_id[first], node)
                second_vector = _outward_vector(by_id[second], node)
                if (
                    _opposition_deviation_deg(first_vector, second_vector)
                    > junction_collinear_deg
                ):
                    continue
                candidates.append(
                    (
                        _opposition_score(first_vector, second_vector),
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

    def walk(initial: GraphEdge, start_node: int) -> None:
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

    # Open trails must start at an unpaired half-edge. Starting in the middle of
    # such a trail would consume one side first and incorrectly split a line.
    seeds: list[tuple[int, int]] = []
    for edge in nonloops:
        for node in (edge.start_node, edge.end_node):
            if (edge.edge_id, node) not in pair:
                seeds.append((edge.edge_id, node))
    for edge_id, node in sorted(seeds):
        if edge_id not in used:
            walk(by_id[edge_id], node)

    # What remains consists of fully paired cycles.
    for initial in sorted(nonloops, key=lambda item: item.edge_id):
        if initial.edge_id not in used:
            walk(initial, initial.start_node)
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
    node_merge_dist_px: float = 0.0,
    collinear_deg: float = 0.0,
) -> list[Stroke]:
    positions, edges = skeleton_graph(skeleton, stats)
    positions, edges, stats.graph_nodes_merged = merge_nearby_junction_nodes(
        positions, edges, node_merge_dist_px
    )
    stats.graph_nodes = len(positions)
    stats.graph_edges = len(edges)
    stats.spurs_pruned = prune_spurs(edges, spur_len_px)
    if collinear_deg > 0:
        for edge in edges:
            edge.points = remove_collinear_points(edge.points, collinear_deg)
    strokes = edges_to_strokes(edges, junction_collinear_deg=collinear_deg)
    if smooth_iterations:
        strokes = [chaikin(stroke, smooth_iterations) for stroke in strokes]
    if not strokes:
        raise VectorizationError(
            "После чистки графа не осталось штрихов", code="EMPTY_AFTER_GRAPH_CLEAN"
        )
    return strokes
