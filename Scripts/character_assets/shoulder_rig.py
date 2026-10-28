"""Local shoulder/upper-back refinement for the selected sculpture meshes.

Keeps original source assets untouched. Corrects exaggerated posterior trap
volume and prevents upper-arm weights dragging the central neck/back surface.
"""
import math
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def smooth(a, b, x):
    t = max(0, min(1, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def refine_upper_back(mesh, sex):
    changed = 0
    maximum = 0
    weights_changed = 0
    spine = mesh.vertex_groups["mixamorig:Spine2"]
    for v in mesh.data.vertices:
        p = v.co.copy()
        # Posterior-only shape reduction, smoothly fading into neck/deltoids.
        posterior = 1 - smooth(-0.055, -0.020, p.x)
        vertical = smooth(0.72, 0.775, p.z) * (1 - smooth(0.815, 0.865, p.z))
        lateral = 1 - smooth(0.035, 0.125, abs(p.y))
        w = posterior * vertical * lateral
        dx = (0.018 if sex == "male" else 0.006) * w
        dz = (0.009 if sex == "male" else 0.003) * w
        if w > 0:
            v.co.x += dx
            v.co.z -= dz
            changed += 1
            maximum = max(maximum, math.hypot(dx, dz))
        # Preserve upper-back/head influences; remove only inappropriate arm
        # influences near the neck, with a broad fade toward the deltoid.
        blend = (
            (1 - smooth(-0.015, 0.020, p.x))
            * smooth(0.715, 0.760, p.z)
            * (1 - smooth(0.075, 0.145, abs(p.y)))
        )
        if blend <= 0:
            continue
        transfer = 0
        for g in list(v.groups):
            name = mesh.vertex_groups[g.group].name
            if any(name.endswith(suffix) for suffix in ["Arm", "ForeArm", "Hand"]):
                moved = g.weight * blend
                if moved > 1e-8:
                    mesh.vertex_groups[g.group].add(
                        [v.index], g.weight - moved, "REPLACE"
                    )
                    transfer += moved
        if transfer:
            old = next((g.weight for g in v.groups if g.group == spine.index), 0)
            spine.add([v.index], old + transfer, "REPLACE")
            weights_changed += 1
    mesh.data.update()
    return {
        "profile_vertices": changed,
        "max_profile_adjustment_model_units": maximum,
        "reweighted_vertices": weights_changed,
    }


def squat_bar_anchor(mesh, sex, scale):
    """Find a posterior tangent to the actual upper-trap surface, not an offset.

    Local model X is anterior; local Y is the bar axis. Sample the 28 mm shaft
    circumference over its central support span and solve posterior clearance.
    """
    bvh = BVHTree.FromPolygons(
        [v.co for v in mesh.data.vertices], [p.vertices[:] for p in mesh.data.polygons]
    )
    z = 0.797 if sex == "male" else 0.796
    radius = 0.014 / scale
    clearance = 0.0008 / scale
    samples = [
        (
            y / 1000,
            radius * math.cos(a * math.tau / 24),
            radius * math.sin(a * math.tau / 24),
        )
        for y in range(-160, 161, 4)
        for a in range(24)
    ]

    def minimum(x):
        value = 1
        for y, dx, dz in samples:
            p = Vector((x + dx, y, z + dz))
            loc, n, _, _ = bvh.find_nearest(p)
            value = min(value, (p - loc).dot(n))
        return value

    outside = -0.25
    inside = 0.0
    for _ in range(22):
        mid = (outside + inside) / 2
        if minimum(mid) >= clearance:
            outside = mid
        else:
            inside = mid
    # Allow for the small deltoid skin displacement in the loaded arm pose.
    outside -= 0.002 / scale if sex == "male" else 0.0
    return Vector((outside, 0, z))
