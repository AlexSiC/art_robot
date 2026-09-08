from __future__ import annotations

import unittest

from png2svg.geometry import (
    merge_strokes,
    point_segment_distance,
    simplify_stroke,
    sort_strokes,
    travel_length,
)
from png2svg.models import Stroke


class GeometryTests(unittest.TestCase):
    def test_rdp_reduces_points_within_tolerance(self) -> None:
        original = Stroke([(float(x), 0.2 if x % 2 else 0.0) for x in range(20)])
        simplified, deviation = simplify_stroke(original, 0.25)
        self.assertEqual(simplified.points, [(0.0, 0.0), (19.0, 0.2)])
        self.assertLessEqual(deviation, 0.25)
        self.assertLess(len(simplified.points), len(original.points))
        for point in original.points:
            self.assertLessEqual(
                point_segment_distance(point, simplified.start, simplified.end), 0.25
            )

    def test_merge_connects_close_endpoints(self) -> None:
        strokes = [
            Stroke([(0.0, 0.0), (5.0, 0.0)]),
            Stroke([(5.2, 0.0), (10.0, 0.0)]),
        ]
        merged, count = merge_strokes(strokes, 0.25)
        self.assertEqual(count, 1)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].start, (0.0, 0.0))
        self.assertEqual(merged[0].end, (10.0, 0.0))

    def test_sort_never_increases_travel(self) -> None:
        source = [
            Stroke([(90.0, 0.0), (91.0, 0.0)]),
            Stroke([(10.0, 0.0), (11.0, 0.0)]),
            Stroke([(50.0, 0.0), (51.0, 0.0)]),
        ]
        ordered = sort_strokes(source, two_opt=True)
        self.assertLessEqual(travel_length(ordered), travel_length(source))
        self.assertEqual(ordered, sort_strokes(source, two_opt=True))


if __name__ == "__main__":
    unittest.main()
