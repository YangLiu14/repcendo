"""Inspect saved meshes, grip-to-bar alignment and stable support surfaces."""
import json, sys, hashlib
from pathlib import Path
import bpy, numpy as np
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from plan_exercises import PLAN_EXERCISES

REPO = Path(__file__).resolve().parents[2]
import argparse

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--root", type=Path, default=REPO)
parser.add_argument(
    "--exercise", help="Audit only this motion in an isolated output root"
)
args = parser.parse_args(
    sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
)
ROOT = args.root.resolve()
if args.exercise and args.exercise not in PLAN_EXERCISES:
    parser.error("unknown exercise: " + args.exercise)
OUT = ROOT / "docs/animation-plan-v3"
result = {}
errors = []
planted = {
    "incline_press",
    "pec_fly",
    "pushdown",
    "pulldown",
    "straight_pulldown",
    "curl",
    "rdl",
    "shoulder_press",
    "lateral_raise",
    "reverse_fly",
}
for sex in ["male", "female"]:
    for name, config in PLAN_EXERCISES.items():
        if args.exercise and name != args.exercise:
            continue
        bpy.ops.wm.open_mainfile(filepath=str(OUT / sex / f"{name}.blend"))
        scene = bpy.context.scene
        rig = next(o for o in scene.objects if o.type == "ARMATURE")
        obj = next(
            o
            for o in scene.objects
            if o.type == "MESH" and any(m.type == "ARMATURE" for m in o.modifiers)
        )
        feet = np.array(
            [v.index for v in obj.data.vertices if v.co.z < 0.025], dtype=int
        )
        first = None
        foot_drift = 0
        loop = 0
        bounds = []
        bar_alignment = 0
        bar_gap = 0
        count = config.get("frames", 120)
        samples = [1, 1 + count // 4, 1 + count // 2, 1 + 3 * count // 4, count + 1]
        for f in samples:
            scene.frame_set(f)
            bpy.context.view_layer.update()
            ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
            mesh = ev.to_mesh()
            coords = np.empty(len(mesh.vertices) * 3)
            mesh.vertices.foreach_get("co", coords)
            coords = coords.reshape(-1, 3)
            matrix = np.array(ev.matrix_world)
            points = coords @ matrix[:3, :3].T + matrix[:3, 3]
            ev.to_mesh_clear()
            assert np.isfinite(points).all() and np.abs(points).max() < 5, (
                sex,
                name,
                f,
                "invalid mesh",
            )
            if first is None:
                first = points.copy()
            foot_drift = max(
                foot_drift,
                float(np.linalg.norm(points[feet] - first[feet], axis=1).max()),
            )
            if f == count + 1:
                loop = float(np.linalg.norm(points - first, axis=1).max())
            bounds.append(
                dict(
                    frame=f,
                    min=points.min(axis=0).tolist(),
                    max=points.max(axis=0).tolist(),
                )
            )
            if name in ["rdl", "pulldown", "straight_pulldown"]:
                bar = bpy.data.objects["RDL barbell" if name == "rdl" else "Cable bar"]
                axis = bar.matrix_world.to_3x3() @ Vector(
                    (1, 0, 0) if name == "rdl" else (0, 0, 1)
                )
                axis.normalize()
                for side in ["Left", "Right"]:
                    grip = bpy.data.objects["Grip." + side]
                    gx = (grip.matrix_world.to_3x3() @ Vector((1, 0, 0))).normalized()
                    bar_alignment = max(bar_alignment, 1 - abs(gx.dot(axis)))
                    delta = grip.matrix_world.translation - bar.matrix_world.translation
                    bar_gap = max(bar_gap, (delta - axis * delta.dot(axis)).length)
        min_z = min(b["min"][2] for b in bounds)
        if name in ["reverse_crunch", "dead_bug"] and min_z < 0.0279:
            errors.append(f"{sex}/{name}: mat penetration {min_z}")
        if name == "calf_raise" and abs(min_z - 0.10) > 0.002:
            errors.append(f"{sex}/{name}: step contact {min_z}")
        if name in planted and foot_drift > 1e-4:
            errors.append(f"{sex}/{name}: planted feet drift {foot_drift}")
        if loop > 1e-4:
            errors.append(f"{sex}/{name}: mesh loop {loop}")
        if bar_alignment > 1e-4 or bar_gap > 1e-4:
            errors.append(f"{sex}/{name}: rigid bar grip {bar_alignment}/{bar_gap}")
        result[f"{sex}/{name}"] = dict(
            sceneSHA256=hashlib.sha256(
                (OUT / sex / f"{name}.blend").read_bytes()
            ).hexdigest(),
            mesh_loop_error_m=loop,
            foot_surface_drift_m=foot_drift,
            planted_feet_expected=name in planted,
            rigid_bar_axis_error=bar_alignment,
            rigid_bar_grip_gap_m=bar_gap,
            bounds=bounds,
        )
report = dict(
    scope=args.exercise or "all",
    status="failed" if errors else "passed",
    samples=result,
    errors=errors,
)
(
    OUT
    / ("scene-validation" + ("-" + args.exercise if args.exercise else "") + ".json")
).write_text(json.dumps(report, indent=2) + "\n")
for e in errors:
    print("SCENE_FAIL", e)
assert not errors
print("SCENE_PASS", len(result), "scenes")
