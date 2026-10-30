"""Blender regression fixtures: run with --python-exit-code 1."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import unittest
import numpy as np
from mathutils.bvhtree import BVHTree
from collision_audit import penetrations, surface_samples, self_intersections


def box(center=(0, 0, 0), half=(0.1, 0.1, 0.1)):
    points = (
        np.array(
            [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], dtype=float
        )
        * half
        + center
    )
    faces = [
        (0, 1, 3),
        (0, 3, 2),
        (4, 6, 7),
        (4, 7, 5),
        (0, 4, 5),
        (0, 5, 1),
        (2, 3, 7),
        (2, 7, 6),
        (0, 2, 6),
        (0, 6, 4),
        (1, 5, 7),
        (1, 7, 3),
    ]
    return points, faces


class CollisionFixtures(unittest.TestCase):
    def setUp(self):
        self.p, self.t = box()
        self.tree = BVHTree.FromPolygons(self.p.tolist(), self.t, all_triangles=True)

    def test_inside_and_outside(self):
        hits = penetrations(
            np.array([[0, 0, 0], [0.12, 0, 0], [0.099, 0, 0]]),
            self.tree,
            self.p.min(0),
            self.p.max(0),
        )
        self.assertEqual([h[1] for h in hits], [0])

    def test_contact_is_not_penetration(self):
        self.assertFalse(
            penetrations(
                np.array([[0.1, 0, 0], [0.099, 0, 0]]),
                self.tree,
                self.p.min(0),
                self.p.max(0),
            )
        )

    def test_thin_rod_without_inside_endpoints(self):
        p, t = box(half=(0.5, 0.007, 0.007))
        self.assertFalse(penetrations(p, self.tree, self.p.min(0), self.p.max(0)))
        self.assertTrue(
            penetrations(surface_samples(p, t), self.tree, self.p.min(0), self.p.max(0))
        )

    def test_nonlocal_body_crossing(self):
        p2, t2 = box(center=(0.15, 0.03, 0.02))
        p = np.concatenate([self.p, p2])
        t = self.t + [tuple(i + 8 for i in f) for f in t2]
        labels = ["mixamorig:Spine"] * 8 + ["mixamorig:LeftHand"] * 8
        tree = BVHTree.FromPolygons(p.tolist(), t, all_triangles=True)
        self.assertTrue(self_intersections(p, t, tree, labels, p))

    def test_shared_surface_is_not_self_collision(self):
        labels = ["mixamorig:Spine"] * 8
        self.assertFalse(self_intersections(self.p, self.t, self.tree, labels, self.p))


suite = unittest.defaultTestLoader.loadTestsFromTestCase(CollisionFixtures)
result = unittest.TextTestRunner(verbosity=2).run(suite)
if not result.wasSuccessful():
    raise AssertionError("Collision regression failed")
