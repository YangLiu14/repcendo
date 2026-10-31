"""Audit, produce review evidence or render an existing library scene."""
import argparse
import json
import sys
from pathlib import Path
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).parent))
from library_exercises import LIBRARY_EXERCISES
from library_gate import ROOT, paths, digest, validator_hashes, require_scene_pass, specification_digest
from collision_audit import audit_scene, mesh_data, TOLERANCE
from deformation_audit import inspect as inspect_deformation
from library_audit_v5 import inspect as inspect_motion

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("mode", choices=["audit", "review", "render"])
p.add_argument("--exercise", choices=list(LIBRARY_EXERCISES), required=True)
p.add_argument("--sex", choices=["male", "female"], required=True)
p.add_argument("--root", type=Path, default=ROOT)
p.add_argument("--frames", default="all")
a = p.parse_args(sys.argv[sys.argv.index("--") + 1:])
folder, build = paths(a.root, a.sex, a.exercise)
source = folder / f"{a.exercise}.blend"
source_sha = digest(source)
bpy.ops.wm.open_mainfile(filepath=str(source.resolve()))
s = bpy.context.scene
assert s["exercise"] == a.exercise and s["sex"] == a.sex
config = LIBRARY_EXERCISES[a.exercise]
assert s.frame_end == config.get("frames", 120)
build.mkdir(parents=True, exist_ok=True)

if a.mode == "audit":
    frames = list(range(1, s.frame_end + 2)) if a.frames == "all" else ([1+s.frame_end*i//8 for i in range(9)] if a.frames == "key" else [int(f) for f in a.frames.split(",")])
    collisions = audit_scene(s, frames)
    deformation = inspect_deformation(s, frames)
    deformation["review_frames"] = sorted(set(deformation["review_frames"] + [1, 31, 61, 91]))
    motion = inspect_motion(s, config, frames)
    assert digest(source) == source_sha, "Source changed during audit"
    report = dict(sceneSHA256=source_sha, validatorSHA256=validator_hashes(a.exercise), specificationSHA256=specification_digest(a.exercise), frames=frames,
                  collision=dict(hits=collisions, tolerance_m=TOLERANCE, checks=dict(body_in_equipment=True, equipment_in_body=True, nonlocal_self_intersection=True)), deformation=deformation, motion=motion,
                  status="failed" if collisions or deformation["failures"] or motion["failures"] else "passed")
    target = folder / f"{a.exercise}-audit.json" if a.frames == "all" else build / "key-audit.json"
    target.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(dict(status=report["status"], collisions=len(collisions), deformation=len(deformation["failures"]), motion=len(motion["failures"]))), flush=True)
    if report["status"] != "passed":
        raise SystemExit(1)
elif a.mode == "review":
    report_path = folder / f"{a.exercise}-audit.json"
    report = json.loads(report_path.read_text()) if report_path.exists() else {}
    frames = report.get("deformation", {}).get("review_frames", [1, 1+s.frame_end//4, 1+s.frame_end//2, 1+3*s.frame_end//4])
    body = next(o for o in s.objects if o.type == "MESH" and any(m.type == "ARMATURE" for m in o.modifiers))
    rig = next(o for o in s.objects if o.type == "ARMATURE")
    output = build / "review"
    output.mkdir(parents=True, exist_ok=True)
    s.render.resolution_x = s.render.resolution_y = 480
    s.render.resolution_percentage = 100
    s.eevee.taa_render_samples = 16
    original_camera = s.camera.matrix_world.copy()
    original_scale = s.camera.data.ortho_scale
    for f in frames:
        s.frame_set(f)
        coords, _ = mesh_data(body, bpy.context.evaluated_depsgraph_get())
        target = Vector((coords.min(0) + coords.max(0)) / 2)
        for view, direction in [("main", None), ("front", (0,5,0.4)), ("side", (5,0,0.4)), ("back", (0,-5,0.4)), ("grip", (4,4,2))]:
            if direction is None:
                s.camera.matrix_world = original_camera
                s.camera.data.ortho_scale = original_scale
            else:
                center = target if view != "grip" else s.objects["Grip." + config["unilateral"]].matrix_world.translation.copy()
                s.camera.location = center + Vector(direction)
                s.camera.rotation_euler = (center - s.camera.location).to_track_quat("-Z", "Y").to_euler()
                s.camera.data.ortho_scale = max(coords.max(0)-coords.min(0))*1.12 if view != "grip" else .55
            s.render.filepath = str(output / f"{view}-{f:04d}.png")
            bpy.ops.render.render(write_still=True)
    (output / "source.json").write_text(json.dumps(dict(sceneSHA256=digest(source), frames=frames, views=["main", "front", "side", "back", "grip"]), indent=2))
else:
    require_scene_pass(a.sex, a.exercise, a.root)
    stamp = build / "render-source.json"
    previous = json.loads(stamp.read_text()) if stamp.exists() else {}
    output = build / "frames"
    output.mkdir(parents=True, exist_ok=True)
    if previous.get("sha256") != digest(source):
        for file in output.glob("frame-*.png"):
            file.unlink()
    stamp.write_text(json.dumps(dict(sha256=digest(source))))
    for f in range(1, s.frame_end + 1):
        path = output / f"frame-{f:04d}.png"
        if path.exists():
            continue
        s.frame_set(f)
        s.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
