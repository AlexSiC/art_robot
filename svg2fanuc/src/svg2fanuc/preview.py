"""Human preview (section 4.3).

Black  = contact strokes
Red dashed = travel moves on the clear plane
Green  = start of each stroke
Blue rect = allowed drawing area (margin inset)
Orange rect = canvas / safety field
Caption = job id, scale, point count
"""

from __future__ import annotations

from xml.sax.saxutils import escape

from .geometry import Stroke
from .profile import Profile
from .transform import Placement


def render_preview(
    strokes: list[Stroke],
    profile: Profile,
    placement: Placement,
    *,
    job_id: str,
    travel_start_xy: tuple[float, float],
) -> str:
    c = profile.canvas
    W, H = c.width_mm, c.height_mm

    def fx(x: float) -> float:
        return round(x, 3)

    def fy(y: float) -> float:
        return round(H - y, 3)

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {fx(W)} {fx(H)}" '
        f'width="{fx(W)}" height="{fx(H)}">'
    )
    parts.append(f'<rect x="0" y="0" width="{fx(W)}" height="{fx(H)}" '
                 f'fill="#fdfdfb" stroke="#e8912d" stroke-width="{_sw(W)}"/>')
    bx0, by0, bx1, by1 = c.bounds_mm
    parts.append(
        f'<rect x="{fx(bx0)}" y="{fy(by1)}" width="{fx(bx1 - bx0)}" '
        f'height="{fx(by1 - by0)}" fill="none" stroke="#2d6ee8" '
        f'stroke-width="{_sw(W)}" stroke-dasharray="{_sw(W) * 3},{_sw(W) * 3}"/>'
    )

    # travel moves (dashed red) in routed order
    cursor = travel_start_xy
    travel_pts: list[str] = []
    for s in strokes:
        travel_pts.append(
            f'<line x1="{fx(cursor[0])}" y1="{fy(cursor[1])}" '
            f'x2="{fx(s.start[0])}" y2="{fy(s.start[1])}" stroke="#d63b3b" '
            f'stroke-width="{_sw(W) * 0.6}" stroke-dasharray="{_sw(W) * 2},{_sw(W) * 2}"/>'
        )
        cursor = s.end
    parts.extend(travel_pts)

    # strokes (black) + start dots (green)
    for s in strokes:
        pts = " ".join(f"{fx(x)},{fy(y)}" for x, y in s.points)
        parts.append(
            f'<polyline points="{pts}" fill="none" stroke="#111111" '
            f'stroke-width="{_sw(W)}" stroke-linecap="round" stroke-linejoin="round"/>'
        )
    for s in strokes:
        parts.append(
            f'<circle cx="{fx(s.start[0])}" cy="{fy(s.start[1])}" '
            f'r="{_sw(W) * 1.6}" fill="#1a9c48"/>'
        )

    n_points = sum(len(s.points) for s in strokes)
    caption = escape(
        f"{job_id}  |  {len(strokes)} strokes  |  {n_points} points  |  "
        f"scale {placement.scale_x:.4f} mm/unit  |  canvas {W:g}x{H:g} mm"
    )
    parts.append(
        f'<text x="{fx(bx0)}" y="{fx(H) - _sw(W) * 2}" '
        f'font-family="monospace" font-size="{_sw(W) * 6}" fill="#444">{caption}</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def _sw(canvas_w_mm: float) -> float:
    return round(max(0.4, canvas_w_mm / 400.0), 3)
