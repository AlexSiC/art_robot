"""Parse the gated SVG into ordered raw subpaths (sections 7.2 and 5).

Input is the *normalised* SVG string from the security gate (root width/height
removed, so svgelements maps the viewBox 1:1). Transforms are reified into the
geometry. Output coordinates are in root viewBox user units.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field

from svgelements import SVG, Close, Move, Path, Shape

from .errors import SvgEmptyError, SvgUnsupportedError

BBox = tuple[float, float, float, float]


@dataclass
class RawSubpath:
    segments: list  # drawable svgelements segments (Line/Bezier/Arc/Close), viewBox units
    closed: bool
    source_element_id: str | None
    order_index: int
    order_group: int | None = None


@dataclass
class ReadResult:
    subpaths: list[RawSubpath]
    src_bbox: BBox
    stats: dict = field(default_factory=dict)


def read_svg(normalized_svg: str) -> ReadResult:
    try:
        svg = SVG.parse(io.StringIO(normalized_svg), reify=True)
    except Exception as exc:  # noqa: BLE001 - svgelements raises broadly
        raise SvgUnsupportedError(f"svgelements failed to parse SVG: {exc}") from exc

    subpaths: list[RawSubpath] = []
    order = 0
    bbox: list[float] | None = None
    element_ids_seen = 0

    for element in svg.elements():
        if not isinstance(element, Shape) or isinstance(element, SVG):
            continue
        try:
            path = Path(element)
        except Exception:  # noqa: BLE001
            continue
        seglist = list(path.segments())
        if not seglist:
            continue
        element_ids_seen += 1
        eid = getattr(element, "id", None)

        current: list = []
        current_closed = False
        for seg in seglist:
            if isinstance(seg, Move):
                if current:
                    subpaths.append(
                        RawSubpath(current, current_closed, eid, order)
                    )
                    order += 1
                current = []
                current_closed = False
                continue
            if isinstance(seg, Close):
                # keep the closing edge as a real drawn segment
                if seg.start is not None and seg.end is not None:
                    current.append(seg)
                current_closed = True
                continue
            current.append(seg)
        if current:
            subpaths.append(RawSubpath(current, current_closed, eid, order))
            order += 1

        eb = _safe_bbox(element)
        if eb is not None:
            bbox = eb if bbox is None else [
                min(bbox[0], eb[0]),
                min(bbox[1], eb[1]),
                max(bbox[2], eb[2]),
                max(bbox[3], eb[3]),
            ]

    subpaths = [sp for sp in subpaths if _has_extent(sp)]
    if not subpaths or bbox is None:
        raise SvgEmptyError("SVG contains no drawable strokes")

    return ReadResult(
        subpaths=subpaths,
        src_bbox=(bbox[0], bbox[1], bbox[2], bbox[3]),
        stats={
            "elements_with_geometry": element_ids_seen,
            "raw_subpaths": len(subpaths),
        },
    )


def _safe_bbox(element) -> list[float] | None:
    try:
        b = element.bbox()
    except Exception:  # noqa: BLE001
        return None
    if b is None:
        return None
    xmin, ymin, xmax, ymax = b
    if not all(v == v and abs(v) != float("inf") for v in (xmin, ymin, xmax, ymax)):
        return None
    return [float(xmin), float(ymin), float(xmax), float(ymax)]


def _has_extent(sp: RawSubpath) -> bool:
    for seg in sp.segments:
        s = seg.point(0.0)
        e = seg.point(1.0)
        if abs(s.x - e.x) > 1e-9 or abs(s.y - e.y) > 1e-9:
            return True
    return False
