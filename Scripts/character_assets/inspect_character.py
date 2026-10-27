"""Inspect an imported character, save an editable .blend, and render four views.

Run with Blender --background --python-exit-code 1 --python this_file -- --source model.glb --out DIR.
Adapted from Whimphony prototype/tools/inspect_character_blender.py.
This preserves imported geometry, materials and skinning; it does not create a rig.
The optional action is a deformation diagnostic, not a fitness instruction clip.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector, Quaternion


def arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--pose-check", action="store_true", help="Check Mixamo upper/lower body deformation")
    parser.add_argument("--render-motion", action="store_true", help="Render diagnostic animation frames")
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1:])


def import_character(source):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if source.suffix.lower() == ".glb":
        bpy.ops.import_scene.gltf(filepath=str(source))
    elif source.suffix.lower() == ".fbx":
        bpy.ops.import_scene.fbx(filepath=str(source))
    else:
        raise ValueError("Expected a GLB or FBX character")
    bpy.context.view_layer.update()
    # glTF import creates a viewport-only Icosphere to display joints. It is not
    # part of the GLB mesh or skin; exclude actual bone display objects from QA.
    bone_shapes = {bone.custom_shape for obj in bpy.context.scene.objects if obj.type == "ARMATURE"
                   for bone in obj.pose.bones if bone.custom_shape}
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj not in bone_shapes]
    if not meshes:
        raise ValueError("Imported asset contains no mesh")
    points = [obj.matrix_world @ Vector(point) for obj in meshes for point in obj.bound_box]
    minimum = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
    maximum = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
    if not all(math.isfinite(value) for value in (*minimum, *maximum)):
        raise ValueError("Non-finite mesh bounds")
    if maximum.z - minimum.z <= 0:
        raise ValueError("Character has zero height")
    return meshes, minimum, maximum


def inspect(meshes, minimum, maximum, source):
    armatures = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
    mesh_reports = []
    for obj in meshes:
        armature_mods = [mod for mod in obj.modifiers if mod.type == "ARMATURE" and mod.object]
        sums = []
        if armature_mods:
            bone_names = {bone.name for mod in armature_mods for bone in mod.object.data.bones}
            groups = {group.index for group in obj.vertex_groups if group.name in bone_names}
            sums = [sum(group.weight for group in vertex.groups if group.group in groups)
                    for vertex in obj.data.vertices]
        mesh_reports.append({
            "name": obj.name,
            "vertices": len(obj.data.vertices),
            "triangles": sum(max(0, len(face.vertices) - 2) for face in obj.data.polygons),
            "uvLayers": [layer.name for layer in obj.data.uv_layers],
            "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
            "armatures": [mod.object.name for mod in armature_mods],
            "unweightedVertices": sum(weight <= 1e-6 for weight in sums) if sums else None,
            "boneWeightRange": [min(sums), max(sums)] if sums else None,
        })
    materials = []
    for material in bpy.data.materials:
        nodes = material.node_tree.nodes if material.use_nodes else []
        images = [node.image for node in nodes if node.type == "TEX_IMAGE" and node.image]
        materials.append({
            "name": material.name,
            "textureImages": [{"name": image.name, "size": list(image.size)} for image in images],
            "hasNormalMapNode": any(node.type == "NORMAL_MAP" for node in nodes),
        })
    return {
        "source": str(source),
        "meshCount": len(meshes),
        "vertices": sum(mesh["vertices"] for mesh in mesh_reports),
        "triangles": sum(mesh["triangles"] for mesh in mesh_reports),
        "bounds": {"min": list(minimum), "max": list(maximum)},
        "meshes": mesh_reports,
        "materials": materials,
        "armatures": [{"name": obj.name, "bones": [{"name": bone.name,
            "parent": bone.parent.name if bone.parent else None} for bone in obj.data.bones]}
            for obj in armatures],
        "actions": [action.name for action in bpy.data.actions],
        "visualReviewRequired": True,
        "performanceCompatibility": "not established by this inspection",
    }


def aim(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def studio(minimum, maximum):
    scene = bpy.context.scene
    center = (minimum + maximum) * .5
    size = maximum - minimum
    span = max(size)
    world = bpy.data.worlds.new("Inspection studio")
    world.use_nodes = True
    next(node for node in world.node_tree.nodes if node.type == "BACKGROUND").inputs[0].default_value = (.72, .75, .78, 1)
    next(node for node in world.node_tree.nodes if node.type == "BACKGROUND").inputs[1].default_value = .35
    scene.world = world
    for name, offset, energy, scale in [
        ("Key", (2, -3, 3), 700, 2.5),
        ("Fill", (-3, -1, 2), 450, 3),
        ("Back", (1, 3, 3), 600, 2.5),
    ]:
        data = bpy.data.lights.new(name, "AREA")
        data.energy = energy * (span / 2.5) ** 2
        data.shape = "DISK"
        data.size = span * scale
        light = bpy.data.objects.new(name, data)
        scene.collection.objects.link(light)
        light.location = center + Vector(offset) * span
        aim(light, center)
    camera_data = bpy.data.cameras.new("Inspection camera")
    camera = bpy.data.objects.new("Inspection camera", camera_data)
    scene.collection.objects.link(camera)
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = max(size.z, size.x * 4 / 3, size.y * 4 / 3) * 1.18
    camera_data.clip_start = max(span * .0001, .00001)
    camera_data.clip_end = span * 100
    scene.camera = camera
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 768
    scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    return camera, center, span


def check_pose(meshes, camera, center, span, out, render_motion=False):
    rig = next(obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE")
    rig.show_in_front = True
    rig.data.display_type = "OCTAHEDRAL"
    required = [f"mixamorig:{side}{part}" for side in ["Left", "Right"]
                for part in ["Arm", "ForeArm", "Hand", "UpLeg", "Leg", "Foot"]]
    if any(name not in rig.pose.bones for name in required):
        raise ValueError("Expected complete Mixamo limb chains")
    weighted = inspect(meshes, center, center, Path("diagnostic"))
    if any(m["unweightedVertices"] != 0 for m in weighted["meshes"]):
        raise ValueError("Unweighted character vertices")
    if any(abs(w - 1) > 1e-4 for m in weighted["meshes"] for w in m["boneWeightRange"]):
        raise ValueError("Skin weights are not normalized")
    original = {b.name: b.matrix_basis.copy() for b in rig.pose.bones}
    rig.animation_data_clear()
    def restore():
        for bone in rig.pose.bones:
            bone.matrix_basis = original[bone.name]
            bone.rotation_mode = "QUATERNION"
        bpy.context.view_layer.update()
    def rotate(name, world_axis, degrees):
        bone = rig.pose.bones[name]
        local_axis = (rig.matrix_world @ bone.bone.matrix_local).to_3x3().inverted() @ Vector(world_axis)
        bone.rotation_quaternion = Quaternion(local_axis.normalized(), math.radians(degrees))
    def positions():
        bpy.context.view_layer.update()
        graph = bpy.context.evaluated_depsgraph_get()
        result = []
        for obj in meshes:
            evaluated = obj.evaluated_get(graph)
            mesh = evaluated.to_mesh()
            try:
                result.extend(evaluated.matrix_world @ v.co for v in mesh.vertices)
            finally:
                evaluated.to_mesh_clear()
        return result
    restore()
    rest = positions()
    # Tripo's current delivered assets face +X; verified using four neutral renders.
    suites = {
        "upper-body": {
            "mixamorig:LeftArm": ((1,0,0), 35),
            "mixamorig:RightArm": ((1,0,0), -35),
            "mixamorig:LeftForeArm": ((0,1,0), -65),
            "mixamorig:RightForeArm": ((0,1,0), -65),
        },
        "lower-body": {
            "mixamorig:LeftUpLeg": ((0,1,0), -40),
            "mixamorig:LeftLeg": ((0,1,0), 70),
            "mixamorig:RightUpLeg": ((0,1,0), -15),
            "mixamorig:RightLeg": ((0,1,0), 30),
        },
    }
    report = {"scope": "diagnostic joint flexion only; not an exercise or full range-of-motion certification", "poses": {}}
    camera.data.ortho_scale = span * 1.65
    for name, rotations in suites.items():
        restore()
        for bone_name, (axis, angle) in rotations.items():
            rotate(bone_name, axis, angle)
        points = positions()
        if not all(math.isfinite(x) for point in points for x in point):
            raise ValueError("Non-finite deformed vertices")
        maximum_distance = max((point - center).length for point in points)
        maximum_displacement = max((point - initial).length for point, initial in zip(points, rest))
        changed = sum((point - initial).length > span * .001 for point, initial in zip(points, rest))
        if maximum_distance > span * 3 or maximum_displacement < span * .01:
            raise ValueError("Skin exploded or did not deform")
        report["poses"][name] = {"rotationsWorldAxisDegrees": rotations,
            "finiteDeformedVertices": True, "maximumVertexDistance": maximum_distance,
            "maximumVertexDisplacement": maximum_displacement, "movedVertexCount": changed}
        for view, direction in {"front": (1,0,.02), "side": (0,1,.02)}.items():
            camera.location = center + Vector(direction) * span * 3
            aim(camera, center)
            bpy.context.scene.render.filepath = str(out / f"pose-{name}-{view}.png")
            bpy.ops.render.render(write_still=True)
    # Keep a reusable named diagnostic action in the editable Blender source.
    animated_names = sorted({n for rotations in suites.values() for n in rotations})
    scene = bpy.context.scene
    scene.render.fps = 24
    for frame, pose in [(1,None),(25,"upper-body"),(49,None),(73,"lower-body"),(97,None)]:
        restore()
        if pose:
            for name,(axis,angle) in suites[pose].items():
                rotate(name,axis,angle)
        for name in animated_names:
            rig.pose.bones[name].keyframe_insert(data_path="rotation_quaternion", frame=frame, group=name)
        scene.timeline_markers.new(pose or "Neutral", frame=frame)
    rig.animation_data.action.name = "QA_JointFlexion_NOT_Exercise"
    scene.frame_start, scene.frame_end = 1,97
    camera.location = center + Vector((1,.65,.06)) * span * 3
    aim(camera, center)
    if render_motion:
        frames = out / "motion-frames"
        frames.mkdir(exist_ok=True)
        scene.render.resolution_x, scene.render.resolution_y = 480,640
        for index,frame in enumerate(range(1,98,4)):
            scene.frame_set(frame)
            scene.render.filepath = str(frames / f"{index:03}.png")
            bpy.ops.render.render(write_still=True)
        scene.render.resolution_x, scene.render.resolution_y = 768,1024
    scene.frame_set(1)
    report["finiteDeformedVertices"] = True
    report["diagnosticAction"] = "QA_JointFlexion_NOT_Exercise"
    report["actionFrames"] = [1,97]
    return report


def render_skeleton_projection(camera, center, span, maximum, out):
    """Front-plane projection of actual rest-joint locations, for readable QA."""
    rig = next(obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE")
    helpers = []
    material = bpy.data.materials.new("QA skeleton copper")
    material.diffuse_color = (.95,.32,.06,1)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (.95,.32,.06,1)
    shader.inputs["Emission Color"].default_value = (.95,.20,.025,1)
    shader.inputs["Emission Strength"].default_value = .8
    def projected(v):
        p = rig.matrix_world @ v
        p.x = maximum.x + span * .05
        return p
    for bone in rig.data.bones:
        head, tail = projected(bone.head_local), projected(bone.tail_local)
        curve = bpy.data.curves.new("QA projection " + bone.name, "CURVE")
        curve.dimensions = "3D"
        curve.bevel_depth, curve.bevel_resolution = span * .0018, 2
        spline = curve.splines.new("POLY")
        spline.points.add(1)
        spline.points[0].co, spline.points[1].co = (*head,1), (*tail,1)
        obj = bpy.data.objects.new(curve.name,curve)
        bpy.context.scene.collection.objects.link(obj)
        obj.data.materials.append(material)
        helpers.append(obj)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=span*.004, location=head)
        obj = bpy.context.object
        obj.data.materials.append(material)
        helpers.append(obj)
    camera.location = center + Vector((1,0,0)) * span * 3
    aim(camera,center)
    bpy.context.scene.render.filepath = str(out / "rig-skeleton-projection.png")
    bpy.ops.render.render(write_still=True)
    for obj in helpers:
        bpy.data.objects.remove(obj,do_unlink=True)


def main():
    args = arguments()
    source, out = args.source.resolve(), args.out.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    out.mkdir(parents=True, exist_ok=True)
    meshes, minimum, maximum = import_character(source)
    report = inspect(meshes, minimum, maximum, source)
    (out / "inspection.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    camera, center, span = studio(minimum, maximum)
    views = {"view-pos-x": (1, 0, .02), "view-neg-x": (-1, 0, .02),
             "view-pos-y": (0, 1, .02), "view-neg-y": (0, -1, .02)}
    for name, direction in views.items():
        camera.location = center + Vector(direction) * span * 3
        aim(camera, center)
        bpy.context.scene.render.filepath = str(out / f"{name}.png")
        bpy.ops.render.render(write_still=True)
    if args.pose_check:
        report["poseCheck"] = check_pose(meshes, camera, center, span, out, args.render_motion)
        render_skeleton_projection(camera, center, span, maximum, out)
        (out / "inspection.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(out / "character.blend"))
    print(json.dumps({"output": str(out), "triangles": report["triangles"],
                      "armatures": len(report["armatures"]), "materials": len(report["materials"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
