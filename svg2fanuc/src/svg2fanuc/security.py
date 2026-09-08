"""Secure SVG gate (section 7.1 of the specification).

Runs *before* the geometry parser. Rejects the whole file on anything outside
the ``SVG-DRAW-1`` allowlist; unsupported geometry never silently disappears.
"""

from __future__ import annotations

import io
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from defusedxml.ElementTree import parse as defused_parse

from .errors import SvgFillError, SvgSecurityError, SvgUnsupportedError, SvgViewBoxRequiredError
from .profile import SecuritySpec

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
XML_NS = "http://www.w3.org/XML/1998/namespace"

# Elements allowed by SVG-DRAW-1. `title`/`desc`/`metadata` carry no geometry and
# are tolerated but ignored; everything else is rejected.
_ALLOWED_ELEMENTS = {
    "svg",
    "g",
    "path",
    "polyline",
    "polygon",
    "line",
    "circle",
    "ellipse",
    "rect",
    "title",
    "desc",
    "metadata",
}
_GEOMETRY_ELEMENTS = {
    "path",
    "polyline",
    "polygon",
    "line",
    "circle",
    "ellipse",
    "rect",
}

# Attributes that may affect rendering in ways SVG-DRAW-1 forbids.
_FORBIDDEN_ATTRS = {
    "clip-path",
    "mask",
    "filter",
    "marker",
    "marker-start",
    "marker-mid",
    "marker-end",
    "style",  # inline CSS: could carry url() / display tricks
}
_FORBIDDEN_ATTR_PREFIXES = ("on",)  # event handlers


@dataclass
class GateResult:
    tree: ET.ElementTree
    root: ET.Element
    viewbox: tuple[float, float, float, float]
    element_count: int
    normalized_svg: str  # width/height stripped, ready for svgelements


def _localname(tag: str) -> tuple[str | None, str]:
    if tag.startswith("{"):
        ns, _, local = tag[1:].partition("}")
        return ns, local
    return None, tag


def gate_svg(path: str | Path, security: SecuritySpec) -> GateResult:
    p = Path(path)
    data = _read_limited(p, security.max_input_bytes)

    if data[:2] == b"\x1f\x8b":
        raise SvgSecurityError("gzip-compressed SVG is not accepted (SVG-DRAW-1)")

    try:
        tree = defused_parse(
            io.BytesIO(data),
            forbid_dtd=True,
            forbid_entities=True,
            forbid_external=True,
        )
    except Exception as exc:  # defusedxml raises several types
        raise SvgSecurityError(
            f"unsafe or unparseable XML: {exc}", detail={"error": type(exc).__name__}
        ) from exc

    root = tree.getroot()
    ns, local = _localname(root.tag)
    if local != "svg" or (ns not in (None, SVG_NS)):
        raise SvgUnsupportedError(f"root element must be <svg>, got <{local}>")

    element_count = _walk(root, security, depth=1)
    if element_count > security.max_elements:
        raise SvgSecurityError(
            f"too many elements: {element_count} > {security.max_elements}"
        )

    viewbox = _require_viewbox(root)
    _check_fills(root)

    normalized = _normalize(root)
    return GateResult(
        tree=tree,
        root=root,
        viewbox=viewbox,
        element_count=element_count,
        normalized_svg=normalized,
    )


def _read_limited(p: Path, limit: int) -> bytes:
    try:
        size = p.stat().st_size
    except OSError as exc:
        raise SvgSecurityError(f"cannot stat input: {exc}") from exc
    if size > limit:
        raise SvgSecurityError(f"input too large: {size} bytes > {limit}")
    return p.read_bytes()


def _walk(el: ET.Element, security: SecuritySpec, depth: int) -> int:
    if depth > security.max_xml_depth:
        raise SvgSecurityError(f"XML nesting deeper than {security.max_xml_depth}")

    ns, local = _localname(el.tag)
    if ns not in (None, SVG_NS):
        raise SvgUnsupportedError(f"element in unsupported namespace: {el.tag}")
    if local not in _ALLOWED_ELEMENTS:
        raise SvgUnsupportedError(
            f"element <{local}> is not allowed by SVG-DRAW-1",
            element_id=el.get("id"),
        )

    for name, value in el.attrib.items():
        _check_attr(el, name, value, security)

    count = 1
    for child in el:
        if not isinstance(child.tag, str):  # comments / PIs -> ET.Comment objects
            raise SvgSecurityError("comments or processing instructions are not allowed")
        count += _walk(child, security, depth + 1)
    return count


def _check_attr(el: ET.Element, name: str, value: str, security: SecuritySpec) -> None:
    ns, local = _localname(name)
    if ns == XLINK_NS or local in ("href", "xlink:href"):
        raise SvgUnsupportedError(
            "href / xlink:href references are not allowed", element_id=el.get("id")
        )
    if ns not in (None, XML_NS):
        raise SvgUnsupportedError(f"attribute in unsupported namespace: {name}")
    if len(value) > security.max_attribute_chars:
        raise SvgSecurityError(f"attribute {local!r} exceeds length limit")
    low = local.lower()
    if low in _FORBIDDEN_ATTRS or low.startswith(_FORBIDDEN_ATTR_PREFIXES):
        raise SvgUnsupportedError(
            f"attribute {local!r} is not allowed by SVG-DRAW-1", element_id=el.get("id")
        )
    if "url(" in value.lower() or "data:" in value.lower() or "javascript:" in value.lower():
        raise SvgUnsupportedError(
            f"attribute {local!r} contains a URL / data URI", element_id=el.get("id")
        )


def _require_viewbox(root: ET.Element) -> tuple[float, float, float, float]:
    vb = root.get("viewBox") or root.get("viewbox")
    if not vb:
        raise SvgViewBoxRequiredError("root <svg> must declare a viewBox")
    parts = vb.replace(",", " ").split()
    if len(parts) != 4:
        raise SvgViewBoxRequiredError(f"viewBox must have 4 values, got {vb!r}")
    try:
        minx, miny, w, h = (float(x) for x in parts)
    except ValueError as exc:
        raise SvgViewBoxRequiredError(f"viewBox has non-numeric values: {vb!r}") from exc
    if not (w > 0 and h > 0):
        raise SvgViewBoxRequiredError("viewBox width and height must be > 0")
    for v in (minx, miny, w, h):
        if v != v or v in (float("inf"), float("-inf")):
            raise SvgViewBoxRequiredError("viewBox contains NaN/Inf")
    return (minx, miny, w, h)


def _effective_fill(el: ET.Element, inherited: str | None) -> str | None:
    fill = el.get("fill")
    if fill is None:
        return inherited
    return fill.strip().lower()


def _check_fills(root: ET.Element, inherited: str | None = None) -> None:
    ns, local = _localname(root.tag)
    fill = _effective_fill(root, inherited)
    if local in _GEOMETRY_ELEMENTS:
        if fill != "none":
            raise SvgFillError(
                f"<{local}> must have fill=\"none\" (SVG-DRAW-1); effective fill={fill!r}",
                element_id=root.get("id"),
            )
    for child in root:
        if isinstance(child.tag, str):
            _check_fills(child, fill)


def _normalize(root: ET.Element) -> str:
    """Strip root width/height so svgelements maps the viewBox 1:1."""
    ET.register_namespace("", SVG_NS)
    clone = _deepcopy_stripping(root)
    return ET.tostring(clone, encoding="unicode")


def _deepcopy_stripping(el: ET.Element) -> ET.Element:
    ns, local = _localname(el.tag)
    new = ET.Element(f"{{{SVG_NS}}}{local}")
    for k, v in el.attrib.items():
        kns, klocal = _localname(k)
        if local == "svg" and klocal in ("width", "height"):
            continue
        new.set(klocal if kns in (None,) else k, v)
    for child in el:
        if isinstance(child.tag, str):
            cns, clocal = _localname(child.tag)
            if clocal in ("title", "desc", "metadata"):
                continue
            new.append(_deepcopy_stripping(child))
    new.text = el.text
    new.tail = el.tail
    return new
