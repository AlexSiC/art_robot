from __future__ import annotations

import pytest

from svg2fanuc.errors import (
    SvgFillError,
    SvgSecurityError,
    SvgUnsupportedError,
    SvgViewBoxRequiredError,
)
from svg2fanuc.security import gate_svg

from .conftest import data


def test_accepts_clean_svg(profile):
    res = gate_svg(data("lines.svg"), profile.security)
    assert res.viewbox == (0.0, 0.0, 100.0, 80.0)
    assert "width" not in res.normalized_svg.split(">", 1)[0]
    assert res.element_count >= 5


def test_rejects_text_element(profile):
    with pytest.raises(SvgUnsupportedError) as e:
        gate_svg(data("bad_text.svg"), profile.security)
    assert e.value.code == "SVG_ELEMENT_UNSUPPORTED"


def test_requires_viewbox(profile):
    with pytest.raises(SvgViewBoxRequiredError):
        gate_svg(data("no_viewbox.svg"), profile.security)


def test_rejects_filled_shape(profile):
    with pytest.raises(SvgFillError):
        gate_svg(data("filled.svg"), profile.security)


def test_rejects_dtd(tmp_path, profile):
    p = tmp_path / "dtd.svg"
    p.write_text(
        '<?xml version="1.0"?>\n'
        '<!DOCTYPE svg [<!ENTITY x "y">]>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1">'
        '<path d="M0 0 L1 1" fill="none"/></svg>'
    )
    with pytest.raises(SvgSecurityError):
        gate_svg(p, profile.security)


def test_rejects_href(tmp_path, profile):
    p = tmp_path / "href.svg"
    p.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 1 1">'
        '<image xlink:href="file:///etc/passwd"/></svg>'
    )
    with pytest.raises(SvgUnsupportedError):
        gate_svg(p, profile.security)


def test_rejects_oversized_input(tmp_path, make_profile):
    prof = make_profile(**{"security.max_input_bytes": 50})
    p = tmp_path / "big.svg"
    p.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        + '<path d="M0 0 L1 1" fill="none"/>' * 20
        + "</svg>"
    )
    with pytest.raises(SvgSecurityError):
        gate_svg(p, prof.security)


def test_rejects_style_attribute(tmp_path, profile):
    p = tmp_path / "style.svg"
    p.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
        '<path d="M0 0 L1 1" fill="none" style="fill:url(#x)"/></svg>'
    )
    with pytest.raises(SvgUnsupportedError):
        gate_svg(p, profile.security)
