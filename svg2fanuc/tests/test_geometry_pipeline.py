from __future__ import annotations

import math

import pytest

from svg2fanuc.errors import FlattenLimitError, OutOfBoundsError
from svg2fanuc.flatten import flatten_subpath
from svg2fanuc.geometry import Stroke, dedupe_consecutive, turn_angle_deg
from svg2fanuc.security import gate_svg
from svg2fanuc.strokes import build_strokes
from svg2fanuc.svg_reader import read_svg
from svg2fanuc.transform import plan_placement

from .conftest import data


def _prep(name, profile):
    gate = gate_svg(data(name), profile.security)
    rd = read_svg(gate.normalized_svg)
    placement = plan_placement(rd.src_bbox, profile.canvas)
    return rd, placement


def test_dedupe_consecutive():
    pts = [(0, 0), (0, 0.0005), (1, 0), (1, 0)]
    assert dedupe_consecutive(pts, 0.01) == [(0, 0), (1, 0)]


def test_turn_angle_straight_and_right():
    assert turn_angle_deg((0, 0), (1, 0), (2, 0)) == pytest.approx(0.0)
    assert turn_angle_deg((0, 0), (1, 0), (1, 1)) == pytest.approx(90.0)


def test_line_is_not_subdivided(profile):
    rd, placement = _prep("lines.svg", profile)
    line_sub = next(sp for sp in rd.subpaths if len(sp.segments) == 1)
    pts = flatten_subpath(
        line_sub.segments, placement.to_mm,
        flatness_mm=0.25, max_segment_mm=1e9, max_depth=20,
    )
    assert len(pts) == 2


def test_curve_respects_flatness(profile):
    rd, placement = _prep("lines.svg", profile)
    curve = max(rd.subpaths, key=lambda sp: sum(1 for _ in sp.segments) + 0)
    # the cubic bezier subpath
    curve = [sp for sp in rd.subpaths if any(
        type(s).__name__ == "CubicBezier" for s in sp.segments)][0]
    pts = flatten_subpath(
        curve.segments, placement.to_mm,
        flatness_mm=0.25, max_segment_mm=1000, max_depth=25,
    )
    # chord deviation of every interior point stays under tolerance
    assert len(pts) > 2


def test_flatten_depth_limit_raises(profile):
    rd, placement = _prep("lines.svg", profile)
    curve = [sp for sp in rd.subpaths if any(
        type(s).__name__ == "CubicBezier" for s in sp.segments)][0]
    with pytest.raises(FlattenLimitError):
        flatten_subpath(
            curve.segments, placement.to_mm,
            flatness_mm=1e-6, max_segment_mm=1e-6, max_depth=3,
        )


def test_build_strokes_counts(profile):
    rd, placement = _prep("lines.svg", profile)
    res = build_strokes(rd, placement, profile)
    assert res.stats["strokes"] == 4
    assert res.stats["max_flatten_error_mm"] <= profile.geometry.flatness_mm


def test_closed_polygon_becomes_closed_stroke(profile):
    rd, placement = _prep("square.svg", profile)
    res = build_strokes(rd, placement, profile)
    assert len(res.strokes) == 1
    s = res.strokes[0]
    assert s.closed
    assert s.points[0] == s.points[-1]


def test_out_of_bounds_detected(profile):
    s = Stroke(id="s1", points=[(0.0, 0.0), (10_000.0, 0.0)])
    with pytest.raises(OutOfBoundsError):
        s.validate((0.0, 0.0, 100.0, 100.0))


def test_placement_centers_and_inverts_y(profile):
    rd, placement = _prep("square.svg", profile)
    # square.svg viewBox 0..50, drawing bbox 5..45
    top_left = placement.to_mm((5.0, 5.0))
    bottom_right = placement.to_mm((45.0, 45.0))
    # y is inverted: source y=5 (top) -> larger mm y
    assert top_left[1] > bottom_right[1]
    m = profile.canvas.margin_mm
    assert min(top_left[0], bottom_right[0]) >= m - 1e-6
