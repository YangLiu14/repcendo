"""Local surface correction with calibrated torso/upper-arm volume guides.

Positive-weight ARAP preserves local rest-shape detail; the implicit volume
constraint prevents the upper-arm collapse seen with surface relaxation alone.
The output is a pose-space corrective target, not a replacement skinning system.
Only reviewed Greek athlete profiles and the dead-bug motion are supported.
"""
import numpy as np
from scipy.sparse import coo_matrix, diags
from scipy.sparse.linalg import splu


class ShoulderVolume:
    VERSION = "greek-shoulder-volume-1"

    def __init__(self, p, edges, bones, sex, max_iterations=None):
        self.p = p
        self.bones = bones
        self.N = len(p)
        self.i, self.j = edges.T
        self.v = p[self.i] - p[self.j]
        self.ii = np.r_[self.i, self.j]
        self.degree = np.bincount(self.ii, minlength=self.N)
        self.sex = sex
        if sex not in ("male", "female"):
            raise ValueError("Unknown sculpture profile")
        self.max_iterations = max_iterations or (100 if sex == "male" else 400)
        self.arm_radius = 0.047 if sex == "male" else 0.036
        self.torso_radius = 0.10 if sex == "male" else 0.087
        self.free = (
            (p[:, 2] > 0.58)
            & (p[:, 2] < 0.85)
            & (abs(p[:, 1]) > 0.035)
            & (abs(p[:, 1]) < 0.20)
        )
        self.f = np.flatnonzero(self.free)
        self.c = np.flatnonzero(~self.free)
        self.lam = 0.7
        w = np.ones(len(self.i))
        L = (
            diags(self.degree.astype(float))
            - coo_matrix(
                (np.r_[w, w], (self.ii, np.r_[self.j, self.i])), shape=(self.N, self.N)
            ).tocsc()
        )
        self.boundary = L[self.f][:, self.c]
        self.solver = splu(
            (L[self.f][:, self.f] + diags(np.full(len(self.f), self.lam))).tocsc()
        )
        self.base, _ = self.field(p, bones[1:])
        # Rotations are needed only on free vertices and their neighbours.
        # Retain every incident edge for those rotations, so this is exactly the
        # same local/global solve as processing the entire body.
        needed = self.free.copy()
        needed[edges[np.any(self.free[edges], axis=1)].ravel()] = True
        self.active = np.flatnonzero(needed)
        retained = np.any(needed[edges], axis=1)
        self.i, self.j = edges[retained].T
        self.ii = np.r_[self.i, self.j]
        self.v = p[self.i] - p[self.j]

    def capsule(self, p, a, b, r):
        d = b - a
        t = np.clip((p - a) @ d / (d @ d), 0, 1)
        v = p - a - t[:, None] * d
        length = np.maximum(np.linalg.norm(v, axis=1), 1e-9)
        return length - r, v / length[:, None]

    def field(self, p, arms):
        x = p.copy()
        x[:, 0] = (x[:, 0] - 0.004) / 0.8
        d, g = self.capsule(
            x, np.array([0, 0, 0.59]), np.array([0, 0, 0.75]), self.torso_radius
        )
        g[:, 0] /= 0.8
        for aa, bb in arms:
            d2, g2 = self.capsule(p, aa, bb, self.arm_radius)
            h = np.clip(0.5 + 0.5 * (d2 - d) / 0.02, 0, 1)
            d = d2 * (1 - h) + d * h - 0.02 * h * (1 - h)
            g = g2 * (1 - h[:, None]) + g * h[:, None]
        g /= np.maximum(np.linalg.norm(g, axis=1), 1e-8)[:, None]
        return d, g

    def solve(self, q, D):
        inv = np.linalg.inv(D[0])
        q = q @ inv[:3, :3].T + inv[:3, 3]
        arms = []
        for k in [1, 2]:
            mat = inv @ D[k]
            arms.append(self.bones[k] @ mat[:3, :3].T + mat[:3, 3])
        boundary = self.boundary @ q[self.c]
        i, j, v = self.i, self.j, self.v
        N = self.N
        for step in range(self.max_iterations):
            delta = q[i] - q[j]
            outer = (v[:, :, None] * delta[:, None, :]).reshape(-1, 9)
            cov = np.column_stack(
                [
                    np.bincount(
                        self.ii, weights=np.r_[outer[:, k], outer[:, k]], minlength=N
                    )
                    for k in range(9)
                ]
            ).reshape(N, 3, 3)
            U, _, Vh = np.linalg.svd(cov[self.active])
            local_rot = Vh.transpose(0, 2, 1) @ U.transpose(0, 2, 1)
            bad = np.linalg.det(local_rot) < 0
            Vh[bad, 2, :] *= -1
            rot = np.broadcast_to(np.eye(3), (N, 3, 3)).copy()
            rot[self.active] = Vh.transpose(0, 2, 1) @ U.transpose(0, 2, 1)
            be = np.einsum("nij,nj->ni", 0.5 * (rot[i] + rot[j]), v)
            b = np.column_stack(
                [
                    np.bincount(
                        self.ii, weights=np.r_[be[:, k], -be[:, k]], minlength=N
                    )
                    for k in range(3)
                ]
            )
            dist, grad = self.field(q[self.f], arms)
            target = q[self.f] - grad * (dist - self.base[self.f])[:, None]
            updated = self.solver.solve(b[self.f] - boundary + self.lam * target)
            movement = np.max(np.linalg.norm(updated - q[self.f], axis=1))
            q[self.f] = updated
            if step >= 99 and movement < 0.000002:
                break
        return q @ D[0, :3, :3].T + D[0, :3, 3]
