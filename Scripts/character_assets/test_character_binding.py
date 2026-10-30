"""Exercise the actual character binding and Blender Armature evaluation."""
import sys, math
from pathlib import Path
import bpy
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(Path(__file__).parent), str(ROOT / "Scripts/animation_samples")]
from prepare_athlete import prepare_character
from skin_matrix import blend_rigid
from deformation_rig import pose_forearm_twist
from hand_rig import pose_fingers, add_contact_clearance

for sex in ["male", "female"]:
    rig, body, centers, chains, *_ = prepare_character(sex)
    assert len(rig.data.bones) == 57
    labels = {g.index: g.name for g in body.vertex_groups}
    deform = {b.name for b in rig.data.bones if b.use_deform}
    for v in body.data.vertices:
        total = sum(g.weight for g in v.groups if labels[g.group] in deform)
        assert abs(total - 1) < 1e-5, (sex, v.index, total)
    graph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(graph)
    mesh = evaluated.to_mesh()
    assert (
        max(
            (
                body.matrix_world @ v.co
                - evaluated.matrix_world @ mesh.vertices[v.index].co
            ).length
            for v in body.data.vertices
        )
        < 1e-5
    ), "neutral pose drift"
    evaluated.to_mesh_clear()
    # Simultaneous elbow bend and wrist rotation exercise blended DQ vertices.
    for side in ["Left", "Right"]:
        fore = rig.pose.bones["mixamorig:" + side + "ForeArm"]
        mat = Matrix.Rotation(0.9, 4, "X") @ fore.bone.matrix_local
        mat.translation = fore.bone.head_local
        fore.matrix = mat
        bpy.context.view_layer.update()
        hand = rig.pose.bones["mixamorig:" + side + "Hand"]
        hand.rotation_mode = "QUATERNION"
        hand.rotation_quaternion = Vector((0, 1, 0)).rotation_difference(
            Vector((0.6, 0.8, 0))
        )
        bpy.context.view_layer.update()
        pose_forearm_twist(rig, side)
    matrices = {
        b.name: b.matrix @ b.bone.matrix_local.inverted() for b in rig.pose.bones
    }
    evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    worst = 0
    for v in list(body.data.vertices)[::31]:
        weights = [
            (labels[g.group], g.weight)
            for g in v.groups
            if labels[g.group] in matrices and g.weight > 0
        ]
        predicted = (
            rig.matrix_world
            @ blend_rigid(matrices, weights)
            @ rig.matrix_world.inverted()
            @ body.matrix_world
            @ v.co
        )
        actual = evaluated.matrix_world @ mesh.vertices[v.index].co
        worst = max(worst, (predicted - actual).length)
    evaluated.to_mesh_clear()
    assert worst < 1e-5, ("DQ inverse differs from Blender", sex, worst)
    print(
        "PASS",
        sex,
        "57 bones; normalized weights; neutral mesh unchanged; DQ inverse error",
        worst,
        flush=True,
    )
    for bone in rig.pose.bones:
        bone.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    for side in ["Left", "Right"]:
        pose_fingers(rig, chains, centers, side, 1)
    add_contact_clearance(rig, body, centers, preserve_thickness=True)
    left_ids = [
        v.index
        for v in body.data.vertices
        if sum(g.weight for g in v.groups if "LeftHand" in labels[g.group]) > 0.999
    ]
    assert left_ids, "No left-hand vertices exercised"

    def left_surface():
        body.update_tag()
        bpy.context.view_layer.update()
        evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        points = [mesh.vertices[i].co.copy() for i in left_ids]
        evaluated.to_mesh_clear()
        return points

    together = left_surface()
    body.data.shape_keys.key_blocks["Right_Grip_Clearance"].value = 0
    left_only = left_surface()
    assert (
        max((a - b).length for a, b in zip(together, left_only)) < 1e-6
    ), "Right corrective duplicates left-hand deformation"
    print(
        "PASS",
        sex,
        "independent left/right thickness-preserving grip correctives",
        flush=True,
    )
