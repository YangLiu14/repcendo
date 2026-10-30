"""Check actual deformed hand surfaces around the equipment, not IK targets.

Each closed grip must have skin in >=10/12 radial sectors within 12 mm of the
shaft, at least one close contact per digit, no vertex deep inside the shaft,
and no drift of fully hand-weighted vertices over the sampled motion.
"""
import bpy, json, math, sys, hashlib
import numpy as np
from pathlib import Path

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
sys.path.insert(0, str(Path(__file__).resolve().parent))
from plan_exercises import PLAN_EXERCISES

if args.exercise and args.exercise not in PLAN_EXERCISES:
    parser.error("unknown exercise: " + args.exercise)
OUT = ROOT / "docs/animation-plan-v3"
result = {}
errors = []
for sex in ["male", "female"]:
    for name, config in PLAN_EXERCISES.items():
        if args.exercise and name != args.exercise:
            continue
        if config.get("open_hands"):
            continue
        bpy.ops.wm.open_mainfile(filepath=str(OUT / sex / f"{name}.blend"))
        s = bpy.context.scene
        rig = next(o for o in s.objects if o.type == "ARMATURE")
        obj = next(
            o
            for o in s.objects
            if o.type == "MESH" and any(m.type == "ARMATURE" for m in o.modifiers)
        )
        digits = ("Thumb", "Index", "Middle", "Ring", "Pinky")
        bones = [
            f"mixamorig:{side}Hand{digit}{j}"
            for side in ["Left", "Right"]
            for digit in digits
            for j in [1, 2, 3]
        ]
        absent = [n for n in bones if n not in rig.data.bones]
        if absent:
            errors.append(f"{sex}/{name}: missing {len(absent)} finger bones")
        selected = {}
        stable = {}
        by_digit = {}
        for side in ["Left", "Right"]:
            prefix = "mixamorig:" + side + "Hand"
            handweights = {
                v.index: sum(
                    g.weight
                    for g in v.groups
                    if obj.vertex_groups[g.group].name.startswith(prefix)
                )
                for v in obj.data.vertices
            }
            selected[side] = [i for i, w in handweights.items() if w > 0.65]
            stable[side] = [i for i, w in handweights.items() if w > 0.9999]
            for digit in digits:
                by_digit[side, digit] = [
                    v.index
                    for v in obj.data.vertices
                    if sum(
                        g.weight
                        for g in v.groups
                        if obj.vertex_groups[g.group].name.startswith(prefix + digit)
                    )
                    > 0.7
                ]
        first = {}
        sample = []
        for f in [1, 31, 61, 91, 121]:
            s.frame_set(f)
            bpy.context.view_layer.update()
            ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
            mesh = ev.to_mesh()
            coords = np.array([list(ev.matrix_world @ v.co) for v in mesh.vertices])
            ev.to_mesh_clear()
            world_coords = coords
            for side, sgn in [("Left", -1), ("Right", 1)]:
                item = bpy.data.objects["Grip." + side]
                local = np.array(item.matrix_world.inverted())
                coords = world_coords @ local[:3, :3].T + local[:3, 3]
                center = np.zeros(3)
                axes = [1, 2]
                pts = coords[selected[side]] - center
                radial = pts[:, axes]
                r = np.linalg.norm(radial, axis=1)
                near = radial[(r >= 0.013) & (r <= 0.026)]
                bins = sorted(
                    set(
                        (
                            np.floor(
                                (np.arctan2(near[:, 1], near[:, 0]) + np.pi)
                                * 12
                                / (2 * np.pi)
                            ).astype(int)
                            % 12
                        ).tolist()
                    )
                )
                contacts = {}
                for digit in digits:
                    ids = by_digit[side, digit]
                    contacts[digit] = (
                        float(
                            np.abs(
                                np.linalg.norm((coords[ids] - center)[:, axes], axis=1)
                                - 0.014
                            ).min()
                        )
                        if ids
                        else 999
                    )
                rel = coords[stable[side]] - center
                if side not in first:
                    first[side] = rel.copy()
                drift = float(np.linalg.norm(rel - first[side], axis=1).max())
                record = {
                    "frame": f,
                    "hand": side,
                    "radial_sectors": bins,
                    "min_surface_radius_m": float(r.min()),
                    "digit_nearest_shaft_gap_m": contacts,
                    "max_hand_drift_m": drift,
                }
                sample.append(record)
                if len(bins) < 10:
                    errors.append(
                        f"{sex}/{name}/{side}/{f}: only {len(bins)} radial sectors"
                    )
                if r.min() < 0.013:
                    errors.append(
                        f"{sex}/{name}/{side}/{f}: deep shaft penetration {r.min():.5f}"
                    )
                if max(contacts.values()) > 0.008:
                    errors.append(
                        f"{sex}/{name}/{side}/{f}: a digit is not gripping {contacts}"
                    )
                if drift > 1e-4:
                    errors.append(f"{sex}/{name}/{side}/{f}: hand slides {drift}")
        # Independent control must actually deform vertices. FK MCP rotation probe.
        if not absent:
            s.frame_set(1)
            bpy.context.view_layer.update()
            ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
            me = ev.to_mesh()
            before = np.array([list(v.co) for v in me.vertices])
            ev.to_mesh_clear()
            b = rig.pose.bones["mixamorig:LeftHandIndex1"]
            saved = b.rotation_quaternion.copy()
            from mathutils import Quaternion

            b.rotation_quaternion = b.rotation_quaternion @ Quaternion((1, 0, 0), 0.25)
            bpy.context.view_layer.update()
            ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
            me = ev.to_mesh()
            after = np.array([list(v.co) for v in me.vertices])
            ev.to_mesh_clear()
            changed = int((np.linalg.norm(after - before, axis=1) > 0.0001).sum())
            b.rotation_quaternion = saved
            if changed < 10:
                errors.append(f"{sex}/{name}: finger control has no skin effect")
        else:
            changed = 0
        result[sex + "/" + name] = {
            "sceneSHA256": hashlib.sha256(
                (OUT / sex / f"{name}.blend").read_bytes()
            ).hexdigest(),
            "finger_bone_count": 30 - len(absent),
            "index_control_affected_vertices": changed,
            "surface_checks": sample,
        }
report = {
    "scope": args.exercise or "all",
    "status": "failed" if errors else "passed",
    "frames_per_clip": [1, 31, 61, 91, 121],
    "shaft_radius_m": 0.014,
    "errors": errors,
    "samples": result,
}
(
    OUT
    / (
        "hand-grip-validation"
        + ("-" + args.exercise if args.exercise else "")
        + ".json"
    )
).write_text(json.dumps(report, indent=2) + "\n")
for err in errors:
    print("GRIP_FAIL", err)
assert not errors, f"{len(errors)} grip failures"
print(
    f"GRIP_PASS: {args.exercise or 'all closed-hand plan motions'}; surface contact, functional fingers and no hand drift."
)
