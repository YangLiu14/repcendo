"""Check the intended neutral rope grip, not merely hand/shaft proximity.

Cable crunch requires the thumb side of both fists toward the upper rope and
no half-turn compensation between forearm and hand. These are motion-specific
orientation constraints, not universal anatomical range limits.
"""
import argparse, hashlib, json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--root", type=Path, default=ROOT)
p.add_argument("--frames", default="all")
a = p.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
results = {}
for sex in ["male", "female"]:
    path = a.root / f"docs/animation-plan-v3/{sex}/cable_crunch.blend"
    bpy.ops.wm.open_mainfile(filepath=str(path.resolve()))
    scene = bpy.context.scene
    rig = next(o for o in scene.objects if o.type == "ARMATURE")
    frames = (
        list(range(1, scene.frame_end + 2))
        if a.frames == "all"
        else [int(x) for x in a.frames.split(",")]
    )
    hits = []
    samples = []
    for frame in frames:
        scene.frame_set(frame)
        for side in ["Left", "Right"]:
            prefix = "mixamorig:" + side
            fore = rig.pose.bones[prefix + "ForeArm"]
            hand = rig.pose.bones[prefix + "Hand"]
            delta = (
                fore.matrix.to_quaternion()
                @ fore.bone.matrix_local.to_quaternion().inverted()
            )
            hdelta = (
                hand.matrix.to_quaternion()
                @ hand.bone.matrix_local.to_quaternion().inverted()
            )
            relative = delta.inverted() @ hdelta
            axis = (fore.bone.tail_local - fore.bone.head_local).normalized()
            angle = 2 * math.atan2(
                Vector((relative.x, relative.y, relative.z)).dot(axis), relative.w
            )
            twist = math.degrees((angle + math.pi) % (2 * math.pi) - math.pi)
            # The index-to-pinky knuckle line identifies the thumb END of a
            # closed fist. The thumb root is near the wrist, not that endpoint.
            thumb_end = rig.matrix_world @ rig.pose.bones[prefix + "HandIndex1"].head
            pinky = rig.matrix_world @ rig.pose.bones[prefix + "HandPinky1"].head
            # Body-up travels with the thorax; the rope split stays above the fists.
            spine = rig.pose.bones["mixamorig:Spine2"]
            torso = spine.matrix @ spine.bone.matrix_local.inverted()
            up = (
                rig.matrix_world.to_3x3() @ torso.to_3x3() @ Vector((0, 0, 1))
            ).normalized()
            thumb_up = (thumb_end - pinky).normalized().dot(up)
            palm = (
                rig.matrix_world.to_3x3()
                @ (hand.matrix @ hand.bone.matrix_local.inverted()).to_3x3()
                @ Vector((0, -1 if side == "Left" else 1, 0))
            ).normalized()
            inward = Vector((1 if side == "Left" else -1, 0, 0))
            palm_inward = palm.dot(inward)
            bend = math.degrees((hand.tail - hand.head).angle(fore.tail - fore.head))
            record = dict(
                frame=frame,
                hand=side,
                wrist_twist_deg=twist,
                wrist_bend_deg=bend,
                thumb_up_dot=thumb_up,
                palm_inward_dot=palm_inward,
            )
            samples.append(record)
            if abs(twist) > 90 or thumb_up < 0.25 or bend > 15 or palm_inward < 0.5:
                hits.append(record)
    results[sex + "/cable_crunch"] = dict(
        passed=not hits,
        sceneSHA256=hashlib.sha256(path.read_bytes()).hexdigest(),
        validatorSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        frames=frames,
        failures=hits,
        max_wrist_twist_deg=max(abs(x["wrist_twist_deg"]) for x in samples),
        max_wrist_bend_deg=max(x["wrist_bend_deg"] for x in samples),
        min_thumb_up_dot=min(x["thumb_up_dot"] for x in samples),
        min_palm_inward_dot=min(x["palm_inward_dot"] for x in samples),
    )
    print(
        "GRIP_ORIENTATION",
        sex,
        "PASS" if not hits else "FAIL",
        results[sex + "/cable_crunch"]["max_wrist_twist_deg"],
        results[sex + "/cable_crunch"]["min_thumb_up_dot"],
        flush=True,
    )
out = a.root / "docs/animation-plan-v3/grip-orientation-validation.json"
if a.frames == "all":
    out.write_text(json.dumps(results, indent=2) + "\n")
if any(not r["passed"] for r in results.values()):
    raise SystemExit("Reversed rope grip / excessive compensating wrist twist")
