"""Actual skinned shoulder/neck and bar-surface regression check.

Uses ray parity to distinguish a genuinely embedded shaft from the wrong sign
of a nearest triangle normal beside an outside concave shoulder crease.
"""
import bpy, json, math, sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/animation-samples-v2"


def inside(bvh, p):
    votes = 0
    for direction in [
        Vector((0.173, 0.493, 0.852)),
        Vector((-0.381, 0.819, 0.428)),
        Vector((0.657, -0.281, 0.699)),
    ]:
        direction.normalize()
        origin = p.copy()
        crossings = 0
        for _ in range(40):
            point, _, _, distance = bvh.ray_cast(origin, direction, 5.0)
            if point is None:
                break
            crossings += 1
            origin = point + direction * 1e-5
        votes += crossings % 2
    return votes >= 2


frames = [1, 31, 61, 91, 121] if "--keyframes" in sys.argv else range(1, 122)
report = {}
errors = []
for sex in ["male", "female"]:
    bpy.ops.wm.open_mainfile(filepath=str(OUT / sex / "squat.blend"))
    scene = bpy.context.scene
    rig = next(o for o in scene.objects if o.type == "ARMATURE")
    obj = next(
        o
        for o in scene.objects
        if o.type == "MESH" and any(m.type == "ARMATURE" for m in o.modifiers)
    )
    records = []
    for frame in frames:
        scene.frame_set(frame)
        ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = ev.to_mesh()
        pts = [ev.matrix_world @ v.co for v in mesh.vertices]
        bvh = BVHTree.FromPolygons(pts, [p.vertices[:] for p in mesh.polygons])
        torso = (
            rig.matrix_world
            @ rig.pose.bones["mixamorig:Spine2"].matrix
            @ rig.data.bones["mixamorig:Spine2"].matrix_local.inverted()
        )
        neck = [
            v.index
            for v in obj.data.vertices
            if v.co.x < -0.02 and abs(v.co.y) < 0.07 and 0.78 < v.co.z < 0.855
        ]
        deviation = max((pts[i] - torso @ obj.data.vertices[i].co).length for i in neck)
        bar = bpy.data.objects["Barbell"]
        intrusions = []
        support = {"left": 1.0, "right": 1.0}
        for i in range(145):
            x = -0.29 + 0.58 * i / 144
            for j in range(25):
                a = j * math.tau / 24
                local = (
                    Vector((x, 0, 0))
                    if j == 24
                    else Vector((x, 0.014 * math.cos(a), 0.014 * math.sin(a)))
                )
                p = bar.matrix_world @ local
                nearest, n, _, distance = bvh.find_nearest(p)
                signed = (p - nearest).dot(n)
                if j < 24 and 0.04 < abs(x) < 0.17:
                    key = "left" if x < 0 else "right"
                    support[key] = min(support[key], distance)
                if signed < -0.0005 and inside(bvh, p):
                    intrusions.append(distance)
        record = {
            "frame": frame,
            "neck_vertices_checked": len(neck),
            "max_neck_surface_deviation_m": deviation,
            "shaft_samples": 145 * 25,
            "shaft_inside_samples": len(intrusions),
            "max_shaft_penetration_m": max(intrusions, default=0),
            "upper_back_contact_gap_m": support,
        }
        records.append(record)
        if deviation > 0.003:
            errors.append(f"{sex}/{frame}: neck pulled {deviation} m")
        if max(intrusions, default=0) > 0.001:
            errors.append(f"{sex}/{frame}: shaft inside {max(intrusions)} m")
        if max(support.values()) > 0.006:
            errors.append(f"{sex}/{frame}: bar floating off upper back {support}")
        ev.to_mesh_clear()
    report[sex] = records
result = {
    "status": "failed" if errors else "passed",
    "test": "deformed triangle mesh; 3-ray parity for shaft penetration; bilateral upper-back contact; neck skin vs rigid torso",
    "errors": errors,
    "samples": report,
}
(OUT / "squat-shoulder-validation.json").write_text(json.dumps(result, indent=2) + "\n")
for error in errors:
    print("SQUAT_FAIL", error)
assert not errors, f"{len(errors)} squat shoulder failures"
print(
    f"SQUAT_SHOULDERS_PASS: {len(frames)*2} poses, actual shaft surface/axis and upper-back contacts; neck not dragged by arms"
)
