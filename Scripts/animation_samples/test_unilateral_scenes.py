"""Blender integration counterexamples; only modifies loaded scenes in memory.

Run: blender -b -t 4 --python-exit-code 1 --python this_file.py
"""
import json, sys
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from library_exercises import LIBRARY_EXERCISES
from library_audit_v5 import inspect


def load(name):
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/f"docs/animation-library/male/{name}.blend"))
    return bpy.context.scene


def evaluate(name, config_name=None, change=None):
    scene = load(name)
    if change:
        change(scene)
    return inspect(scene, LIBRARY_EXERCISES[config_name or name], [1, 31, 61, 91, 121])["failures"]


def move_idle(scene):
    scene.frame_set(61)
    rig = next(o for o in scene.objects if o.type == "ARMATURE")
    bone = rig.pose.bones["mixamorig:RightForeArm"]
    bone.location.x += .05
    bone.keyframe_insert("location", frame=61)


def stretch_load(scene):
    obj = scene.objects["Dumbbell plate Left"]
    obj.keyframe_insert("scale", frame=1)
    obj.scale.x *= 1.5
    obj.keyframe_insert("scale", frame=61)


def move_bench(scene):
    obj = scene.objects["Bench pad"]
    obj.keyframe_insert("location", frame=1)
    obj.location.z += .03
    obj.keyframe_insert("location", frame=61)


def main():
    results = []
    for name, config in LIBRARY_EXERCISES.items():
        if config["batch"] == "005":
            failures = evaluate(name)
            assert not failures, (name, failures[:2])
            results.append(dict(case=name, positive=True, passed=True))
    cases = [
        ("wrong_grip", "single_curl", "single_hammer_curl", None, "grip_or_motion_intent"),
        ("two_loaded_hands", "hammer_curl", "single_hammer_curl", None, "unilateral_equipment"),
        ("unloaded_arm_moving", "single_curl", None, move_idle, "unloaded_arm_moved"),
        ("stretching_dumbbell", "single_curl", None, stretch_load, "nonrigid_dumbbell"),
        ("drifting_bench", "single_bench_press", None, move_bench, "fixed_equipment_drift"),
        ("wrong_support", "single_bench_press", "single_incline_press", None, "missing_support_object"),
    ]
    for label, name, config, change, expected in cases:
        failures = evaluate(name, config, change)
        assert expected in {f["check"] for f in failures}, (label, failures[:2])
        results.append(dict(case=label, positive=False, rejected=True, expected=expected,
                            failureCount=len(failures), checks=sorted({f["check"] for f in failures})))
    # Captured, hash-matched failures before the grip-cavity subdivision fix.
    from collision_audit import audit_scene
    import hashlib
    for name in ("single_bench_press", "single_incline_press"):
        source = ROOT/f"build/animation-library/batch-005-diagnostics/{name}-coarse.blend"
        original = json.loads(source.with_name(name+"-coarse-audit.json").read_text())
        assert hashlib.sha256(source.read_bytes()).hexdigest() == original["sceneSHA256"]
        bpy.ops.wm.open_mainfile(filepath=str(source))
        hits = audit_scene(bpy.context.scene, [16, 31, 61])
        assert any(h.get("object") == "Grip shaft Left" for h in hits)
        results.append(dict(case=name+"_coarse_grip", positive=False, rejected=True,
                            failureCount=len(hits), sceneSHA256=original["sceneSHA256"]))
    output = ROOT/"build/animation-library/batch-005-negative-controls.json"
    output.write_text(json.dumps(results, indent=2)+"\n")
    print("PASS: eight positive scenes, six physical mutations and two saved coarse-grip failures", flush=True)


if __name__ == "__main__":
    main()
