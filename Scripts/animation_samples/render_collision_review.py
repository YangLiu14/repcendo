"""Independent front/side/back contact sheets; diagnostic renders, never exports."""
import sys, json, hashlib, argparse
from pathlib import Path
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collision_gate import ROOT, CATALOG
from plan_exercises import PLAN_EXERCISES

p = argparse.ArgumentParser()
p.add_argument("--sex", choices=["male", "female"])
p.add_argument("--exercise", choices=list(CATALOG))
a = p.parse_args(sys.argv[sys.argv.index("--") + 1 :])
for sex in [a.sex] if a.sex else ["male", "female"]:
    for name in [a.exercise] if a.exercise else CATALOG:
        collection = (
            "animation-plan-v3" if name in PLAN_EXERCISES else "animation-samples-v2"
        )
        source = ROOT / f"docs/{collection}/{sex}/{name}.blend"
        bpy.ops.wm.open_mainfile(filepath=str(source))
        s = bpy.context.scene
        folder = ROOT / f"build/collision-review/{sex}/{name}"
        folder.mkdir(parents=True, exist_ok=True)
        s.render.resolution_x = 600
        s.render.resolution_y = 600
        s.render.resolution_percentage = 100
        s.eevee.taa_render_samples = 16
        targets = {
            "bench": (0, -0.05, 0.55),
            "row": (0, 0.4, 0.7),
            "leg_press": (0, 0.25, 0.85),
            "reverse_crunch": (0, 0.10, 0.35),
            "dead_bug": (0, 0.1, 0.35),
        }
        target = Vector(targets.get(name, (0, 0.1, 1)))
        poses = [1, 1 + s.frame_end // 2] if name != "dead_bug" else [1, 49, 145]
        for view, delta in [
            ("front", (0, 5, 1.2)),
            ("side", (5, 0, 1.2)),
            ("back", (0, -5, 1.2)),
        ]:
            s.camera.location = target + Vector(delta)
            s.camera.rotation_euler = (
                (target - s.camera.location).to_track_quat("-Z", "Y").to_euler()
            )
            s.camera.data.ortho_scale = 3.1
            for f in poses:
                s.frame_set(f)
                s.render.filepath = str(folder / f"{view}-{f:04d}.png")
                bpy.ops.render.render(write_still=True)
        (folder / "source.json").write_text(
            json.dumps(
                dict(
                    sceneSHA256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    frames=poses,
                    views=["front", "side", "back"],
                )
            )
            + "\n"
        )
