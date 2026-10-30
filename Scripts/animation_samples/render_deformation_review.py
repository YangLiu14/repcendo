"""Render isolated-body front/side/back shape evidence, without approving it."""
import argparse, hashlib, json, sys
from pathlib import Path
import bpy, numpy as np
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).parent))
from collision_gate import ROOT, CATALOG
from plan_exercises import PLAN_EXERCISES
from collision_audit import mesh_data

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--root", type=Path, default=ROOT)
p.add_argument("--sex", choices=["male", "female"])
p.add_argument("--exercise", choices=list(CATALOG))
a = p.parse_args(sys.argv[sys.argv.index("--") + 1 :])
for sex in [a.sex] if a.sex else ["male", "female"]:
    for name in [a.exercise] if a.exercise else CATALOG:
        collection = (
            "animation-plan-v3" if name in PLAN_EXERCISES else "animation-samples-v2"
        )
        source = a.root / f"docs/{collection}/{sex}/{name}.blend"
        bpy.ops.wm.open_mainfile(filepath=str(source.resolve()))
        s = bpy.context.scene
        folder = a.root / f"build/deformation-review/{sex}/{name}"
        folder.mkdir(parents=True, exist_ok=True)
        body = next(
            o
            for o in s.objects
            if o.type == "MESH" and any(m.type == "ARMATURE" for m in o.modifiers)
        )
        visibility = {o.name: o.hide_render for o in s.objects}
        for o in s.objects:
            if o.type == "MESH" and o != body:
                o.hide_render = True
        s.render.resolution_x = 500
        s.render.resolution_y = 500
        s.render.resolution_percentage = 100
        s.eevee.taa_render_samples = 16
        frames = [
            1,
            1 + s.frame_end // 4,
            1 + s.frame_end // 2,
            1 + 3 * s.frame_end // 4,
        ]
        audit_path = a.root / "docs/animation-plan-v3/deformation-validation.json"
        if audit_path.exists():
            record = json.loads(audit_path.read_text()).get(sex + "/" + name, {})
            if (
                record.get("scene_sha256")
                == hashlib.sha256(source.read_bytes()).hexdigest()
            ):
                frames = record.get("review_frames", frames)
        for frame in frames:
            s.frame_set(frame)
            coords, _ = mesh_data(body, bpy.context.evaluated_depsgraph_get())
            target = Vector((coords.min(0) + coords.max(0)) / 2)
            extent = coords.max(0) - coords.min(0)
            size = max(extent) * 1.12
            directions = [
                ("front", (0, 5, 0.4)),
                ("side", (5, 0, 0.4)),
                ("back", (0, -5, 0.4)),
            ]
            if name == "dead_bug":
                directions = [
                    ("front", (0, 0, 5)),
                    ("side", (5, 0, 0.4)),
                    ("back", (0, 0, -5)),
                ]
            for view, direction in directions:
                s.camera.location = target + Vector(direction)
                s.camera.rotation_euler = (
                    (target - s.camera.location).to_track_quat("-Z", "Y").to_euler()
                )
                s.camera.data.ortho_scale = size
                s.render.filepath = str(folder / f"{view}-{frame:04d}.png")
                bpy.ops.render.render(write_still=True)
        if name == "dead_bug":
            rig = next(o for o in s.objects if o.type == "ARMATURE")
            for frame in frames:
                s.frame_set(frame)
                points = [
                    rig.matrix_world @ rig.pose.bones["mixamorig:" + n].head
                    for n in ["Spine2", "LeftArm", "RightArm"]
                ]
                target = sum(points, Vector()) / len(points)
                s.camera.location = target + Vector((3, 2, 3))
                s.camera.rotation_euler = (
                    (target - s.camera.location).to_track_quat("-Z", "Y").to_euler()
                )
                s.camera.data.ortho_scale = 1.05
                s.render.filepath = str(folder / f"shoulder-{frame:04d}.png")
                bpy.ops.render.render(write_still=True)
        # Isolated-body views cannot establish whether the hands face the rope
        # correctly. Keep the equipment visible in a separate close-up series.
        if name == "cable_crunch":
            for o in s.objects:
                o.hide_render = visibility[o.name]
            rig = next(o for o in s.objects if o.type == "ARMATURE")
            for frame in frames:
                s.frame_set(frame)
                points = [
                    rig.matrix_world @ rig.pose.bones["mixamorig:" + side + part].head
                    for side in ["Left", "Right"]
                    for part in ["Arm", "ForeArm", "Hand"]
                ]
                target = sum(points, Vector()) / len(points)
                s.camera.location = target + Vector((5, 3, 2.5))
                s.camera.rotation_euler = (
                    (target - s.camera.location).to_track_quat("-Z", "Y").to_euler()
                )
                s.camera.data.ortho_scale = 0.85
                s.render.filepath = str(folder / f"grip-{frame:04d}.png")
                bpy.ops.render.render(write_still=True)
        (folder / "source.json").write_text(
            json.dumps(
                dict(
                    scene_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    frames=frames,
                    views=["front", "side", "back"],
                ),
                indent=2,
            )
        )
        print("REVIEW", sex, name, flush=True)
