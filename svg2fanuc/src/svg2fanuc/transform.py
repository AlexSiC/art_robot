"""Place the drawing into canvas UFRAME millimetres (section 7.3).

The mapping is affine: uniform (or per-axis for ``stretch``) scale, a mandatory
Y inversion (SVG y-down -> canvas y-up), and an alignment translation. Flattening
tolerances are applied later in this same mm space.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .errors import CliError, GeometryError
from .geometry import Point2
from .profile import CanvasSpec

BBox = tuple[float, float, float, float]  # xmin, ymin, xmax, ymax (viewBox units)


@dataclass(frozen=True)
class Placement:
    scale_x: float
    scale_y: float
    src_bbox: BBox
    canvas: CanvasSpec
    align_xy: tuple[float, float]

    def to_mm(self, p: Point2) -> Point2:
        xmin, ymin, xmax, ymax = self.src_bbox
        ax, ay = self.align_xy
        m = self.canvas.margin_mm
        x_mm = m + ax + self.scale_x * (p[0] - xmin)
        y_mm = m + ay + self.scale_y * (ymax - p[1])
        return (x_mm, y_mm)

    @property
    def drawn_width_mm(self) -> float:
        xmin, _, xmax, _ = self.src_bbox
        return self.scale_x * (xmax - xmin)

    @property
    def drawn_height_mm(self) -> float:
        _, ymin, _, ymax = self.src_bbox
        return self.scale_y * (ymax - ymin)

    def describe(self) -> dict:
        return {
            "scale_x_mm_per_unit": self.scale_x,
            "scale_y_mm_per_unit": self.scale_y,
            "src_bbox_units": list(self.src_bbox),
            "drawn_size_mm": [self.drawn_width_mm, self.drawn_height_mm],
            "align_offset_mm": list(self.align_xy),
        }


def plan_placement(
    src_bbox: BBox,
    canvas: CanvasSpec,
    *,
    allow_distortion: bool = False,
) -> Placement:
    xmin, ymin, xmax, ymax = src_bbox
    dw = xmax - xmin
    dh = ymax - ymin
    if dw <= 0 or dh <= 0:
        raise GeometryError(
            f"drawing bounding box is degenerate: width={dw}, height={dh}"
        )

    area_w = canvas.area_width_mm
    area_h = canvas.area_height_mm

    if canvas.fit == "contain":
        s = min(area_w / dw, area_h / dh)
        sx = sy = s
    elif canvas.fit == "actual":
        s = 1.0 / canvas.svg_units_per_mm
        sx = sy = s
    elif canvas.fit == "stretch":
        if not allow_distortion:
            raise CliError(
                "canvas.fit=stretch requires --allow-distortion (not for production)"
            )
        sx = area_w / dw
        sy = area_h / dh
    else:  # pragma: no cover - profile validation covers this
        raise CliError(f"unknown canvas.fit {canvas.fit!r}")

    drawn_w = sx * dw
    drawn_h = sy * dh

    if canvas.align == "center":
        ax = (area_w - drawn_w) / 2.0
        ay = (area_h - drawn_h) / 2.0
    elif canvas.align == "top_left":
        ax = 0.0
        ay = area_h - drawn_h
    elif canvas.align == "offset":
        ax, ay = canvas.align_offset_mm
    else:  # pragma: no cover
        raise CliError(f"unknown canvas.align {canvas.align!r}")

    placement = Placement(
        scale_x=sx,
        scale_y=sy,
        src_bbox=src_bbox,
        canvas=canvas,
        align_xy=(ax, ay),
    )

    # Guard: drawing must fit the allowed area (within a small epsilon).
    eps = 1e-6
    if drawn_w > area_w + eps or drawn_h > area_h + eps:
        raise GeometryError(
            "scaled drawing does not fit the allowed area: "
            f"drawn {drawn_w:.2f}x{drawn_h:.2f} mm vs area {area_w:.2f}x{area_h:.2f} mm"
        )
    return placement


ToMm = Callable[[Point2], Point2]
