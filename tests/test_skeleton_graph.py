from __future__ import annotations

import unittest

import numpy as np

from png2svg.graph import vectorize_skeleton
from png2svg.models import ProcessingStats
from png2svg.skeleton import zhang_suen


class SkeletonGraphTests(unittest.TestCase):
    def test_thick_line_becomes_one_pixel_centerline(self) -> None:
        mask = np.zeros((25, 50), dtype=bool)
        mask[10:15, 5:45] = True
        skeleton = zhang_suen(mask)
        self.assertGreater(int(skeleton.sum()), 30)
        self.assertLess(int(skeleton.sum()), 45)
        self.assertLessEqual(int(skeleton.sum(axis=0).max()), 1)

    def test_line_graph_is_one_open_stroke(self) -> None:
        skeleton = np.zeros((20, 40), dtype=bool)
        skeleton[10, 4:36] = True
        stats = ProcessingStats()
        strokes = vectorize_skeleton(
            skeleton, spur_len_px=2.0, smooth_iterations=0, stats=stats
        )
        self.assertEqual(len(strokes), 1)
        self.assertFalse(strokes[0].closed)
        self.assertEqual(strokes[0].points[0], (4.0, 10.0))
        self.assertEqual(strokes[0].points[-1], (35.0, 10.0))

    def test_short_terminal_spur_is_pruned(self) -> None:
        skeleton = np.zeros((30, 50), dtype=bool)
        skeleton[15, 4:46] = True
        skeleton[10:16, 25] = True
        stats = ProcessingStats()
        strokes = vectorize_skeleton(
            skeleton, spur_len_px=7.0, smooth_iterations=0, stats=stats
        )
        self.assertGreaterEqual(stats.spurs_pruned, 1)
        self.assertTrue(strokes)


if __name__ == "__main__":
    unittest.main()
