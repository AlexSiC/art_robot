"""Geometry primitives and invariants (section 6.1 of the specification)."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .errors import GeometryError, OutOfBoundsError

Point2 = tuple[float, float]

_BOUNDS_EPS_MM = 1e-6


def is_finite(*values: float) -> bool:
    return all(math.isfinite(v) for v in values)


def dist(a: Point2, b: Point2) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def polyline_length(points: list[Point2]) -> float:
    return sum(dist(points[i], points[i + 1]) for i in range(len(points) - 1))


def point_segment_distance(p: Point2, a: Point2, b: Point2) -> float:
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    denom = dx * dx + dy * dy
    if denom == 0.0:
        return dist(p, a)
    t = ((px - ax) * dx + (py - ay) * dy) / denom
    t = max(0.0, min(1.0, t))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def dedupe_consecutive(points: list[Point2], epsilon: float) -> list[Point2]:
    if not points:
        return []
    out = [points[0]]
    for pt in points[1:]:
        if dist(out[-1], pt) > epsilon:
            out.append(pt)
    return out


def turn_angle_deg(prev: Point2, vertex: Point2, nxt: Point2) -> float:
    """Deviation from straight travel at ``vertex`` in degrees (0 = straight)."""
    v1x, v1y = vertex[0] - prev[0], vertex[1] - prev[1]
    v2x, v2y = nxt[0] - vertex[0], nxt[1] - vertex[1]
    n1 = math.hypot(v1x, v1y)
    n2 = math.hypot(v2x, v2y)
    if n1 == 0.0 or n2 == 0.0:
        return 0.0
    cos_a = (v1x * v2x + v1y * v2y) / (n1 * n2)
    cos_a = max(-1.0, min(1.0, cos_a))
    return math.degrees(math.acos(cos_a))


@dataclass
class Stroke:
    """One physical brush stroke in canvas UFRAME millimetres.

    Invariants (section 6.1):
      * at least two distinct points
      * no adjacent points closer than ``dedupe_epsilon_mm``
      * all coordinates finite
      * entirely inside the allowed rectangle
      * direction may be reversed as a whole, never internally reordered
    """

    id: str
    points: list[Point2]
    closed: bool = False
    reversible: bool = True
    source_element_id: str | None = None
    order_group: int | None = None
    _flatten_error_mm: float = field(default=0.0, repr=False)

    @property
    def start(self) -> Point2:
        return self.points[0]

    @property
    def end(self) -> Point2:
        return self.points[-1]

    def length(self) -> float:
        return polyline_length(self.points)

    def reversed_copy(self) -> "Stroke":
        return Stroke(
            id=self.id,
            points=list(reversed(self.points)),
            closed=self.closed,
            reversible=self.reversible,
            source_element_id=self.source_element_id,
            order_group=self.order_group,
            _flatten_error_mm=self._flatten_error_mm,
        )

    def rotated_to(self, index: int) -> "Stroke":
        """For closed strokes: start the loop at vertex ``index``."""
        if not self.closed:
            return self
        pts = self.points[:-1] if self.points[0] == self.points[-1] else self.points[:]
        n = len(pts)
        index %= n
        rot = pts[index:] + pts[:index]
        rot.append(rot[0])
        return Stroke(
            id=self.id,
            points=rot,
            closed=True,
            reversible=self.reversible,
            source_element_id=self.source_element_id,
            order_group=self.order_group,
            _flatten_error_mm=self._flatten_error_mm,
        )

    def validate(self, bounds_mm: tuple[float, float, float, float]) -> None:
        if len(self.points) < 2:
            raise GeometryError(
                f"stroke {self.id}: fewer than 2 points", element_id=self.source_element_id
            )
        distinct = {(round(x, 9), round(y, 9)) for x, y in self.points}
        if len(distinct) < 2:
            raise GeometryError(
                f"stroke {self.id}: all points coincide", element_id=self.source_element_id
            )
        xmin, ymin, xmax, ymax = bounds_mm
        for x, y in self.points:
            if not is_finite(x, y):
                raise GeometryError(
                    f"stroke {self.id}: non-finite coordinate",
                    element_id=self.source_element_id,
                )
            if not (
                xmin - _BOUNDS_EPS_MM <= x <= xmax + _BOUNDS_EPS_MM
                and ymin - _BOUNDS_EPS_MM <= y <= ymax + _BOUNDS_EPS_MM
            ):
                raise OutOfBoundsError(
                    f"stroke {self.id}: point ({x:.4f}, {y:.4f}) mm outside allowed "
                    f"area x[{xmin:.3f}, {xmax:.3f}] y[{ymin:.3f}, {ymax:.3f}]",
                    element_id=self.source_element_id,
                )
