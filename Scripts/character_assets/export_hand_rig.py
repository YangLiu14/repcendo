"""Extract reusable sculpture masters with 30 finger bones from reviewed scenes.

.blend retains the independent muscle switches and both grip clearance keys.
.glb uses the existing ivory albedo and exports the open/close hand action.
"""
import bpy, json, sys
from pathlib import Path
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/character-assets/hand-rig-v1"
OUT.mkdir(parents=True, exist_ok=True)
records = {}
for sex in ["male", "female"]:
    bpy.ops.wm.open_mainfile(
        filepath=str(ROOT / f"docs/animation-samples-v2/{sex}/bench.blend")
    )
    scene = bpy.context.scene
    scene.frame_set(1)
    rig = next(o for o in scene.objects if o.type == "ARMATURE")
    mesh = next(
        o
        for o in scene.objects
        if o.type == "MESH" and any(m.type == "ARMATURE" for m in o.modifiers)
    )
    digits = [
        b
        for b in rig.pose.bones
        if any(
            "Hand" + d in b.name for d in ["Thumb", "Index", "Middle", "Ring", "Pinky"]
        )
    ]
    closed = {b.name: b.matrix_basis.copy() for b in digits}
    rig.animation_data_clear()
    mesh.data.shape_keys.animation_data_clear()
    for o in list(scene.objects):
        if o not in [rig, mesh]:
            bpy.data.objects.remove(o, do_unlink=True)
    # Keep the calibrated armature at the same world scale as the motion scenes.
    for b in rig.pose.bones:
        b.matrix_basis = Matrix.Identity(4)
    for k in list(rig.keys()):
        if isinstance(rig[k], float):
            rig[k] = 0.0
    for frame, t in [(1, 0.0), (21, 0.0), (61, 1.0), (81, 1.0), (121, 0.0)]:
        scene.frame_set(frame)
        for b in digits:
            m = Matrix.Identity(4).lerp(closed[b.name], t)
            b.matrix_basis = m
            b.rotation_mode = "QUATERNION"
            b.keyframe_insert("location", frame=frame)
            b.keyframe_insert("rotation_quaternion", frame=frame)
            b.keyframe_insert("scale", frame=frame)
        for key in mesh.data.shape_keys.key_blocks:
            if key.name.endswith("_Grip_Clearance"):
                key.value = t
                key.keyframe_insert("value", frame=frame)
    rig.animation_data.action.name = "Hands_Open_Close"
    for action in list(bpy.data.actions):
        if action.users == 0:
            bpy.data.actions.remove(action)
    scene.frame_start = 1
    scene.frame_end = 121
    scene.frame_set(1)
    bpy.context.view_layer.update()
    rig[
        "usage"
    ] = "FK: mixamorig:Left/RightHand + Thumb/Index/Middle/Ring/Pinky + 1/2/3. Reset clearance keys for other grips."
    # A sensible saved editing view.
    bpy.ops.object.select_all(action="DESELECT")
    rig.select_set(True)
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = rig
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                area.spaces.active.region_3d.view_distance = 2.7
    folder = OUT / sex
    folder.mkdir(exist_ok=True)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(folder / f"greek-{sex}-hand-rig.blend"))
    # Standard glTF material, without Blender-only muscle mixing drivers.
    marble = (
        next(i for i in bpy.data.images if i.name.startswith("marble-basecolor"))
        if any(i.name.startswith("marble-basecolor") for i in bpy.data.images)
        else None
    )
    if marble is None:
        marble = bpy.data.images.load(
            str(
                ROOT
                / f"docs/character-assets/muscle-overlay-v1/{sex}/textures/marble-basecolor.png"
            )
        )
    for slot in mesh.material_slots:
        mat = slot.material
        mat.animation_data_clear()
        mat.node_tree.animation_data_clear()
        mat.node_tree.nodes.clear()
        n = mat.node_tree.nodes
        links = mat.node_tree.links
        output = n.new("ShaderNodeOutputMaterial")
        bsdf = n.new("ShaderNodeBsdfPrincipled")
        tex = n.new("ShaderNodeTexImage")
        tex.image = marble
        bsdf.inputs["Roughness"].default_value = 0.62
        links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        links.new(bsdf.outputs[0], output.inputs[0])
    bpy.ops.export_scene.gltf(
        filepath=str(folder / f"greek-{sex}-hand-rig.glb"),
        export_format="GLB",
        use_selection=True,
        export_animations=True,
        export_skins=True,
        export_extras=True,
        export_frame_range=True,
        export_animation_mode="ACTIVE_ACTIONS",
    )
    records[sex] = {
        "body_bones": 23,
        "new_finger_bones": len(digits),
        "total_bones": len(rig.data.bones),
        "vertices": len(mesh.data.vertices),
        "triangles": len(mesh.data.polygons),
        "action": "Hands_Open_Close",
        "open_frames": [1, 21, 121],
        "closed_frames": [61, 81],
        "blend_has_muscle_switches": True,
        "glb_material": "ivory marble; use muscle-overlay-v1 atlas for runtime muscle display",
    }
(OUT / "manifest.json").write_text(
    json.dumps(
        {
            "shoulder_revision": 1,
            "version": 1,
            "source": "../muscle-overlay-v1/",
            "source_untouched": True,
            "characters": records,
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n"
)
print("EXPORTED_HAND_RIGS", records)
