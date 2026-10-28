"""Render the actual corrected hand geometry for inspection and the preview page."""
import bpy
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/animation-samples-v2/hand-closeups"
OUT.mkdir(exist_ok=True)
for sex in ["male", "female"]:
    for exercise in ["squat", "bench", "row"]:
        bpy.ops.wm.open_mainfile(
            filepath=str(ROOT / f"docs/animation-samples-v2/{sex}/{exercise}.blend")
        )
        scene = bpy.context.scene
        scene.render.resolution_x = 800
        scene.render.resolution_y = 800
        scene.render.resolution_percentage = 100
        scene.render.film_transparent = True
        for frame in [1, 61]:
            scene.frame_set(frame)
            origin = bpy.data.objects[
                "Cable handle" if exercise == "row" else "Barbell"
            ].location
            target = origin + Vector(
                (
                    -0.085
                    if exercise == "row"
                    else (-0.39 if exercise == "bench" else -0.37),
                    0,
                    0,
                )
            )
            camera = scene.camera
            camera.location = target + Vector((0.24, 0.32, 0.15))
            camera.rotation_euler = (
                (target - camera.location).to_track_quat("-Z", "Y").to_euler()
            )
            camera.data.ortho_scale = 0.30
            scene.render.filepath = str(OUT / f"{sex}-{exercise}-{frame:03d}.png")
            bpy.ops.render.render(write_still=True)
print("HAND_CLOSEUPS: 12 actual rendered hand poses")
