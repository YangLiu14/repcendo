"""Render photo-comparison evidence with the equipment visible."""
import argparse, hashlib, json, sys
from pathlib import Path
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).parent))
from frame_plan_scene import fit

ROOT = Path(__file__).resolve().parents[2]
p = argparse.ArgumentParser()
p.add_argument("--root", type=Path, default=ROOT)
a = p.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
for sex in ["male", "female"]:
    for name in ["pec_fly", "reverse_fly"]:
        source = a.root / f"docs/animation-plan-v3/{sex}/{name}.blend"
        bpy.ops.wm.open_mainfile(filepath=str(source.resolve()))
        s = bpy.context.scene
        folder = a.root / f"build/pec-deck-review/{sex}/{name}"
        folder.mkdir(parents=True, exist_ok=True)
        s.render.resolution_x = 700
        s.render.resolution_y = 700
        s.render.resolution_percentage = 100
        s.eevee.taa_render_samples = 16
        original_location = s.camera.location.copy()
        original_rotation = s.camera.rotation_euler.copy()
        for view in ["main", "side"]:
            if view == "main":
                s.camera.location = original_location
                s.camera.rotation_euler = original_rotation
            else:
                target = Vector((0, 0.15, 0.95))
                s.camera.location = target + Vector((5, 0.1, 0.6))
                s.camera.rotation_euler = (
                    (target - s.camera.location).to_track_quat("-Z", "Y").to_euler()
                )
            bpy.context.view_layer.update()
            fit(s)
            for frame in [1, 31, 61]:
                s.frame_set(frame)
                s.render.filepath = str((folder / f"{view}-{frame:03d}.png").resolve())
                bpy.ops.render.render(write_still=True)
        (folder / "source.json").write_text(
            json.dumps(
                dict(
                    scene_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    frames=[1, 31, 61],
                    views=["main", "side"],
                ),
                indent=2,
            )
            + "\n"
        )
