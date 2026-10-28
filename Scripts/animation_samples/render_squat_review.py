"""Render actual corrected shoulder contact from three views for visual review."""
import bpy
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/animation-samples-v2/shoulder-review"
OUT.mkdir(exist_ok=True)
for sex in ["male", "female"]:
    bpy.ops.wm.open_mainfile(
        filepath=str(ROOT / f"docs/animation-samples-v2/{sex}/squat.blend")
    )
    s = bpy.context.scene
    rig = next(o for o in s.objects if o.type == "ARMATURE")
    s.render.resolution_x = 900
    s.render.resolution_y = 900
    s.render.resolution_percentage = 100
    s.render.film_transparent = True
    for f in [1, 61]:
        s.frame_set(f)
        D = (
            rig.matrix_world
            @ rig.pose.bones["mixamorig:Spine2"].matrix
            @ rig.data.bones["mixamorig:Spine2"].matrix_local.inverted()
        )
        center = D @ Vector((0, 0, 0.82))
        cam = s.camera
        for view, offset in [
            ("front", (2, 3, 1)),
            ("back", (2, -3, 1)),
            ("side", (3, -0.3, 0.3)),
        ]:
            for o in s.objects:
                if o.name.startswith(("Weight plate", "Sleeve", "Collar")):
                    o.hide_render = view == "side"
            cam.location = center + Vector(offset)
            cam.rotation_euler = (
                (center - cam.location).to_track_quat("-Z", "Y").to_euler()
            )
            cam.data.ortho_scale = 0.95
            s.render.filepath = str(OUT / f"{sex}-{f:03d}-{view}.png")
            bpy.ops.render.render(write_still=True)
print(
    "SQUAT_REVIEW: 12 front/back/side shoulder views (side hides plates for visibility)"
)
