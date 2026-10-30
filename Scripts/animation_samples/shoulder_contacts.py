"""Separate nonlocal shoulder skin crossings after pose correction.

Contact projections are spread over a compact patch in the *rest* surface so
they cannot jump across the armpit to the opposing patch. The independent
full-scene collision audit remains the publication gate.
"""

import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from scipy.spatial import cKDTree

from collision_audit import TOLERANCE, region


class ShoulderContacts:
    def __init__(self, body, free, sex="male"):
        self.world = np.array(body.matrix_world)
        self.inverse = np.linalg.inv(self.world)
        rest = np.array([v.co[:] for v in body.data.vertices])
        self.rest = rest @ self.world[:3, :3].T + self.world[:3, 3]
        body.data.calc_loop_triangles()
        self.triangles = np.array([t.vertices[:] for t in body.data.loop_triangles])
        self.centers = self.rest[self.triangles].mean(1)
        labels = [
            region(body.vertex_groups[max(v.groups, key=lambda g: g.weight).group].name)
            for v in body.data.vertices
        ]
        self.regions = np.array(labels)[self.triangles[:, 0]]
        self.tree = cKDTree(self.rest)
        self.free = free
        self.sex = sex
        self.radius = 0.015 if sex == "female" else 0.045

    def separate(self, points):
        q = points @ self.world[:3, :3].T + self.world[:3, 3]
        original = q.copy()
        for iteration in range(30):
            tree = BVHTree.FromPolygons(
                [Vector(v) for v in q], self.triangles.tolist(), all_triangles=True
            )
            moves = {}
            for a, b in tree.overlap(tree):
                if a >= b or {self.regions[a], self.regions[b]} not in (
                    {"RightArm", "Torso"},
                    {"LeftArm", "Torso"},
                ):
                    continue
                # Same nonlocal seam definition as the established audit;
                # adjacent triangles of one joint are not separate solids.
                if np.linalg.norm(self.centers[a] - self.centers[b]) < 0.14:
                    continue
                if self.regions[a] == "Torso":
                    a, b = b, a
                pa, pb = q[self.triangles[a]], q[self.triangles[b]]
                normal = np.cross(pb[1] - pb[0], pb[2] - pb[0])
                normal /= max(np.linalg.norm(normal), 1e-12)
                distances = (pa - pb[0]) @ normal
                arm_normal = np.cross(pa[1] - pa[0], pa[2] - pa[0])
                arm_normal /= max(np.linalg.norm(arm_normal), 1e-12)
                reverse_distances = (pb - pa[0]) @ arm_normal
                # BVH overlap alone is not a penetration constraint. Require
                # both signed triangle-plane tests before moving either patch.
                depth = min(
                    max(0.0, -distances.min()), max(0.0, -reverse_distances.min())
                )
                # Cloth contacts use the existing audit tolerance; chasing
                # sub-tolerance creases can create larger folds.
                if depth <= (TOLERANCE if self.sex == "female" else 0.001):
                    continue
                if self.sex == "female":
                    # The clothed female shoulder contains folds whose normals
                    # point in similar directions. Opposing normal projections
                    # translate both patches together. A minimum separating
                    # translation gives them equal/opposite displacements.
                    options = []
                    for axis in (normal, arm_normal):
                        aa, bb = pa @ axis, pb @ axis
                        options.extend(
                            [
                                (bb.max() - aa.min() + 0.0015, axis),
                                (aa.max() - bb.min() + 0.0015, -axis),
                            ]
                        )
                    amount, direction = min(options, key=lambda item: item[0])
                    amount = min(0.003, amount * 0.5)
                    for triangle, sign in ((a, 1), (b, -1)):
                        for index in self.triangles[triangle]:
                            if self.free[index]:
                                moves.setdefault(index, []).append(
                                    sign * direction * amount
                                )
                else:
                    for index, distance in zip(self.triangles[a], distances):
                        if distance < 0 and self.free[index]:
                            moves.setdefault(index, []).append(
                                normal * min(0.003, (-distance + 0.0015) * 0.5)
                            )
                    # Share the compression between opposing skin patches. Moving
                    # only the arm can push it into another part of the chest.
                    for index, distance in zip(self.triangles[b], reverse_distances):
                        if distance < 0 and self.free[index]:
                            moves.setdefault(index, []).append(
                                arm_normal * min(0.003, (-distance + 0.0015) * 0.5)
                            )
            if not moves:
                return (
                    q @ self.inverse[:3, :3].T + self.inverse[:3, 3],
                    float(np.linalg.norm(q - original, axis=1).max()),
                )
            shift = np.zeros_like(q)
            denominator = np.zeros(len(q))
            for index, vectors in moves.items():
                nearby = np.array(
                    self.tree.query_ball_point(self.rest[index], self.radius)
                )
                nearby = nearby[self.free[nearby]]
                weights = (
                    1
                    - np.linalg.norm(self.rest[nearby] - self.rest[index], axis=1)
                    / self.radius
                ) ** 2
                shift[nearby] += weights[:, None] * np.mean(vectors, axis=0)
                denominator[nearby] += weights
            q += shift / np.maximum(denominator[:, None], 1)
            if np.linalg.norm(q - original, axis=1).max() > 0.035:
                raise RuntimeError(
                    "Shoulder contact needs manual review: displacement exceeds 35 mm"
                )
        raise RuntimeError("Shoulder contact projection did not converge")
