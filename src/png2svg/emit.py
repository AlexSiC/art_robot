from __future__ import annotations

import hashlib
import html
import json
import math
import os
import platform
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from PIL import __version__ as pillow_version
import numpy as np
import yaml

from .errors import ValidationError
from .geometry import dedupe_points
from .models import Stroke
from .version import __version__

SVG_NS = "http://www.w3.org/2000/svg"


def _number(value: float, decimals: int) -> str:
    rounded = round(value, decimals)
    if rounded == 0:
        rounded = 0.0
    text = f"{rounded:.{decimals}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def quantize_and_validate(
    strokes: list[Stroke], width: int, height: int, decimals: int, epsilon: float
) -> tuple[list[Stroke], int]:
    output: list[Stroke] = []
    dropped = 0
    for stroke in strokes:
        points = [(round(x, decimals), round(y, decimals)) for x, y in stroke.points]
        points = dedupe_points(points, epsilon)
        minimum = 3 if stroke.closed else 2
        if len(points) < minimum:
            dropped += 1
            continue
        for x, y in points:
            if not (math.isfinite(x) and math.isfinite(y)):
                raise ValidationError("NaN/Inf в геометрии", code="SVG_NONFINITE")
            if x < 0 or y < 0 or x > width or y > height:
                raise ValidationError(
                    f"Точка ({x}, {y}) вне viewBox 0 0 {width} {height}",
                    code="SVG_OUT_OF_BOUNDS",
                )
        output.append(Stroke(points, stroke.closed, stroke.source_id))
    if not output:
        raise ValidationError(
            "После округления не осталось валидных штрихов", code="SVG_EMPTY"
        )
    return output, dropped


def clean_svg_bytes(
    strokes: list[Stroke], width: int, height: int, profile: dict[str, Any]
) -> bytes:
    decimals = int(profile["output"]["decimal_places"])
    stroke_width = _number(float(profile["output"]["stroke_width"]), decimals)
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="{SVG_NS}" viewBox="0 0 {width} {height}" '
            f'width="{width}" height="{height}">'
        ),
        (
            f'  <g fill="none" stroke="#000000" stroke-width="{stroke_width}" '
            'stroke-linecap="round" stroke-linejoin="round">'
        ),
    ]
    emit_ids = bool(profile["output"].get("emit_ids", True))
    for index, stroke in enumerate(strokes, start=1):
        tag = "polygon" if stroke.closed else "polyline"
        identifier = f' id="s{index:04d}"' if emit_ids else ""
        points = " ".join(
            f"{_number(x, decimals)},{_number(y, decimals)}" for x, y in stroke.points
        )
        lines.append(f'    <{tag}{identifier} fill="none" points="{points}"/>')
    lines.extend(("  </g>", "</svg>", ""))
    return "\n".join(lines).encode("utf-8")


def preview_svg_bytes(
    strokes: list[Stroke], width: int, height: int, profile: dict[str, Any]
) -> bytes:
    decimals = int(profile["output"]["decimal_places"])
    margin = max(14.0, min(width, height) * 0.03)
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="{SVG_NS}" viewBox="{-margin:g} {-margin:g} '
            f'{width + 2 * margin:g} {height + 2 * margin:g}" '
            f'width="{width}" height="{height}">'
        ),
        '  <rect x="0" y="0" width="100%" height="100%" fill="#ffffff"/>',
        f'  <rect x="0" y="0" width="{width}" height="{height}" fill="none" stroke="#3178c6" stroke-width="1"/>',
    ]
    previous = (0.0, 0.0)
    for stroke in strokes:
        lines.append(
            '  <line '
            f'x1="{_number(previous[0], decimals)}" y1="{_number(previous[1], decimals)}" '
            f'x2="{_number(stroke.start[0], decimals)}" y2="{_number(stroke.start[1], decimals)}" '
            'stroke="#888888" stroke-width="0.6" stroke-dasharray="3 3"/>'
        )
        previous = stroke.end
    lines.append(
        f'  <g fill="none" stroke="#000000" stroke-width="{_number(float(profile["output"]["stroke_width"]), decimals)}" stroke-linecap="round" stroke-linejoin="round">'
    )
    for stroke in strokes:
        tag = "polygon" if stroke.closed else "polyline"
        points = " ".join(
            f"{_number(x, decimals)},{_number(y, decimals)}" for x, y in stroke.points
        )
        lines.append(f'    <{tag} points="{points}"/>')
    lines.append("  </g>")
    radius = max(1.5, min(width, height) * 0.002)
    for index, stroke in enumerate(strokes, start=1):
        lines.append(
            f'  <circle cx="{_number(stroke.start[0], decimals)}" '
            f'cy="{_number(stroke.start[1], decimals)}" r="{radius:g}" fill="#18a558"/>'
        )
        if len(strokes) <= 100:
            lines.append(
                f'  <text x="{_number(stroke.start[0] + radius * 1.5, decimals)}" '
                f'y="{_number(stroke.start[1] - radius * 1.5, decimals)}" '
                f'font-size="{max(7.0, radius * 4):g}" fill="#157347">{index}</text>'
            )
    caption = html.escape(
        f"strokes={len(strokes)} points={sum(len(item.points) for item in strokes)} viewBox=0 0 {width} {height}"
    )
    lines.append(
        f'  <text x="0" y="{-margin * 0.25:g}" font-size="{max(8.0, margin * 0.35):g}" fill="#222222">{caption}</text>'
    )
    lines.extend(("</svg>", ""))
    return "\n".join(lines).encode("utf-8")


def validate_clean_svg(data: bytes) -> None:
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ValidationError(f"Эмитирован невалидный XML: {exc}", code="SVG_XML") from exc
    if root.tag != f"{{{SVG_NS}}}svg":
        raise ValidationError("Некорректный корневой SVG element", code="SVG_ROOT")
    if "viewBox" not in root.attrib or "width" not in root.attrib or "height" not in root.attrib:
        raise ValidationError("SVG не содержит viewBox/width/height", code="SVG_DIMENSIONS")
    allowed = {f"{{{SVG_NS}}}svg", f"{{{SVG_NS}}}g", f"{{{SVG_NS}}}polyline", f"{{{SVG_NS}}}polygon"}
    geometry_count = 0
    for element in root.iter():
        if element.tag not in allowed:
            raise ValidationError(
                f"Запрещенный элемент {element.tag}", code="SVG_ELEMENT"
            )
        if element.tag in {f"{{{SVG_NS}}}polyline", f"{{{SVG_NS}}}polygon"}:
            geometry_count += 1
            if element.attrib.get("fill") != "none":
                raise ValidationError("Геометрия должна иметь fill=none", code="SVG_FILL")
            if "transform" in element.attrib:
                raise ValidationError("Transforms запрещены", code="SVG_TRANSFORM")
            points = element.attrib.get("points", "").split()
            minimum = 3 if element.tag.endswith("polygon") else 2
            if len(points) < minimum:
                raise ValidationError("Нулевой SVG-штрих", code="SVG_ZERO_STROKE")
    if geometry_count == 0:
        raise ValidationError("SVG не содержит геометрию", code="SVG_EMPTY")


def json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dependency_versions() -> dict[str, str]:
    return {
        "png2svg": __version__,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "Pillow": pillow_version,
        "PyYAML": yaml.__version__,
    }


def manifest_bytes(
    *,
    input_name: str,
    input_hash: str,
    source_profile_hash: str,
    effective_profile_hash: str,
    artifacts: dict[str, bytes],
    dry_run: bool,
) -> bytes:
    manifest = {
        "schema_version": 1,
        "input": {"name": input_name, "sha256": input_hash},
        "profile": {
            "source_sha256": source_profile_hash,
            "effective_sha256": effective_profile_hash,
        },
        "artifacts": {
            name: {"sha256": sha256_bytes(data), "bytes": len(data)}
            for name, data in sorted(artifacts.items())
        },
        "versions": dependency_versions(),
        "mode": "dry-run" if dry_run else "production",
    }
    source_date_epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if source_date_epoch is not None:
        manifest["source_date_epoch"] = source_date_epoch
    return json_bytes(manifest)
