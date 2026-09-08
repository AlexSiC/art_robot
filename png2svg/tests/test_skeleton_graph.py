from __future__ import annotations

import unittest

import numpy as np

from png2svg.graph import merge_nearby_junction_nodes, remove_collinear_points, vectorize_skeleton
from png2svg.models import GraphEdge, ProcessingStats
from png2svg.skeleton import zhang_suen


class SkeletonGraphTests(unittest.TestCase):
    def test_collinear_micro_points_are_removed(self) -> None:
        points = [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (2.0, 1.0)]
        self.assertEqual(
            remove_collinear_points(points, 4.0),
            [(0.0, 0.0), (2.0, 0.0), (2.0, 1.0)],
        )

    def test_nearby_junction_nodes_are_merged(self) -> None:
        positions = {
            0: (10.0, 10.0),
            1: (12.0, 10.0),
            2: (0.0, 10.0),
            3: (20.0, 10.0),
            4: (10.0, 0.0),
            5: (12.0, 20.0),
        }
        pairs = [(2, 0), (4, 0), (0, 1), (1, 3), (1, 5)]
        edges = [
            GraphEdge(index, start, end, [positions[start], positions[end]])
            for index, (start, end) in enumerate(pairs)
        ]
        merged_positions, merged_edges, count = merge_nearby_junction_nodes(
            positions, edges, 3.0
        )
        self.assertEqual(count, 1)
        self.assertEqual(len(merged_positions), 5)
        self.assertEqual(len(merged_edges), 4)

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

    def test_cross_keeps_two_continuous_strokes(self) -> None:
        skeleton = np.zeros((31, 31), dtype=bool)
        skeleton[15, 3:28] = True
        skeleton[3:28, 15] = True
        stats = ProcessingStats()
        strokes = vectorize_skeleton(
            skeleton,
            spur_len_px=2.0,
            smooth_iterations=0,
            stats=stats,
            node_merge_dist_px=4.0,
            collinear_deg=4.0,
        )
        self.assertEqual(len(strokes), 2)
        self.assertTrue(all(not stroke.closed for stroke in strokes))

    def test_pixel_ring_becomes_closed_stroke(self) -> None:
        skeleton = np.zeros((31, 31), dtype=bool)
        skeleton[5, 5:26] = True
        skeleton[25, 5:26] = True
        skeleton[5:26, 5] = True
        skeleton[5:26, 25] = True
        stats = ProcessingStats()
        strokes = vectorize_skeleton(
            skeleton,
            spur_len_px=2.0,
            smooth_iterations=0,
            stats=stats,
            node_merge_dist_px=2.0,
            collinear_deg=4.0,
        )
        self.assertEqual(len(strokes), 1)
        self.assertTrue(strokes[0].closed)

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
