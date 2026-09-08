from __future__ import annotations

from dataclasses import dataclass, field
from math import hypot, isfinite
from typing import Any

Point = tuple[float, float]


@dataclass(slots=True)
class Stroke:
    points: list[Point]
    closed: bool = False
    source_id: str | None = None

    def copy(self) -> "Stroke":
        return Stroke(list(self.points), self.closed, self.source_id)

    @property
    def start(self) -> Point:
        return self.points[0]

    @property
    def end(self) -> Point:
        return self.points[0] if self.closed else self.points[-1]

    @property
    def length(self) -> float:
        total = sum(
            hypot(b[0] - a[0], b[1] - a[1])
            for a, b in zip(self.points, self.points[1:])
        )
        if self.closed and len(self.points) > 2:
            a, b = self.points[-1], self.points[0]
            total += hypot(b[0] - a[0], b[1] - a[1])
        return total

    def reversed(self) -> "Stroke":
        return Stroke(list(reversed(self.points)), self.closed, self.source_id)

    def finite(self) -> bool:
        return all(isfinite(x) and isfinite(y) for x, y in self.points)


@dataclass(slots=True)
class GraphEdge:
    edge_id: int
    start_node: int
    end_node: int
    points: list[Point]
    active: bool = True

    @property
    def length(self) -> float:
        return sum(
            hypot(b[0] - a[0], b[1] - a[1])
            for a, b in zip(self.points, self.points[1:])
        )


@dataclass(slots=True)
class ProcessingStats:
    source_image_size: list[int] = field(default_factory=list)
    working_image_size: list[int] = field(default_factory=list)
    upscale_factor: float = 1.0
    threshold: float | None = None
    foreground_pixels: int = 0
    skeleton_pixels: int = 0
    connected_components: int = 0
    graph_nodes: int = 0
    graph_edges: int = 0
    graph_node_pixels_collapsed: int = 0
    graph_nodes_merged: int = 0
    estimated_stroke_width_px: float = 0.0
    node_merge_distance_used_px: float = 0.0
    spurs_pruned: int = 0
    strokes_merged: int = 0
    dropped_short_strokes: int = 0
    points_before_simplify: int = 0
    points_removed_by_simplify: int = 0
    simplify_tolerance_vb: float = 0.0
    max_simplify_deviation_vb: float = 0.0
    length_loss_ratio: float = 0.0
    travel_length_before: float = 0.0
    travel_length_after: float = 0.0
    strokes: int = 0
    points: int = 0
    open_strokes: int = 0
    closed_strokes: int = 0
    total_length_vb: float = 0.0
    bbox_vb: list[float] | None = None
    viewbox: list[float] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)

    def warn(self, code: str, message: str) -> None:
        self.warnings.append({"code": code, "message": message})

    def as_dict(self) -> dict[str, Any]:
        return {
            name: getattr(self, name)
            for name in self.__dataclass_fields__
        }
