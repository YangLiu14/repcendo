"""Character-space calibration and rotation transport shared by all motions.

No surface smoothing. Keep rotation transport separate from end-effector targets.
"""
import math
from mathutils import Matrix, Vector

VERSION = "athlete-deformation-2"


def calibrate_hinge_weights(body, rig, sex):
    """Continuous joint-centred weight ramps, preserving other bone influences.

    The sculpture's bulky knees need a broader transition than the heat binding.
    These character-specific ramps are reviewed with ROM poses, not per-exercise
    geometry smoothing. Only vertices already owned by the two limb bones change.
    """
    for side in ["Left", "Right"]:
        for proximal, distal, width in [
            ("UpLeg", "Leg", 0.08 if sex == "male" else 0.065),
            ("Arm", "ForeArm", 0.055 if sex == "male" else 0.05),
        ]:
            parent = rig.data.bones["mixamorig:" + side + proximal]
            child = rig.data.bones["mixamorig:" + side + distal]
            axis = (child.tail_local - parent.head_local).normalized()
            ga, gb = body.vertex_groups[parent.name], body.vertex_groups[child.name]
            for vertex in body.data.vertices:
                weights = {g.group: g.weight for g in vertex.groups}
                total = weights.get(ga.index, 0) + weights.get(gb.index, 0)
                along = (vertex.co - child.head_local).dot(axis)
                if total < 0.8 or abs(along) > 0.12:
                    continue
                t = max(0, min(1, 0.5 + along / (2 * width)))
                t = t * t * (3 - 2 * t)
                ga.add([vertex.index], total * (1 - t), "REPLACE")
                gb.add([vertex.index], total * t, "REPLACE")


def install_forearm_twist(body, rig):
    """Two auxiliary deform bones distribute pronation toward the wrist."""
    import bpy

    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    for side in ["Left", "Right"]:
        parent = rig.data.edit_bones["mixamorig:" + side + "ForeArm"]
        for index in [1, 2]:
            bone = rig.data.edit_bones.new(parent.name + "Twist" + str(index))
            bone.head = parent.head
            bone.tail = parent.tail
            bone.roll = parent.roll
            bone.parent = parent
    bpy.ops.object.mode_set(mode="OBJECT")
    for side in ["Left", "Right"]:
        name = "mixamorig:" + side + "ForeArm"
        bone = rig.data.bones[name]
        groups = [body.vertex_groups[name]] + [
            body.vertex_groups.new(name=name + "Twist" + str(i)) for i in [1, 2]
        ]
        direction = bone.tail_local - bone.head_local
        for vertex in body.data.vertices:
            weight = next(
                (g.weight for g in vertex.groups if g.group == groups[0].index), 0.0
            )
            if not weight:
                continue
            t = max(
                0.0,
                min(
                    1.0,
                    (vertex.co - bone.head_local).dot(direction)
                    / direction.length_squared,
                ),
            )
            weights = [max(0, 1 - 2 * t), 1 - abs(2 * t - 1), max(0, 2 * t - 1)]
            for group, fraction in zip(groups, weights):
                group.add([vertex.index], weight * fraction, "REPLACE")


def pose_forearm_twist(rig, side, frame=None):
    """Extract wrist axial rotation and distribute it; do not twist the elbow seam."""
    import bpy

    name = "mixamorig:" + side + "ForeArm"
    fore = rig.pose.bones[name]
    hand = rig.pose.bones["mixamorig:" + side + "Hand"]
    delta = fore.matrix @ fore.bone.matrix_local.inverted()
    hand_delta = (
        hand.matrix.to_quaternion() @ hand.bone.matrix_local.to_quaternion().inverted()
    )
    relative = delta.to_quaternion().inverted() @ hand_delta
    axis = (fore.bone.tail_local - fore.bone.head_local).normalized()
    angle = 2 * math.atan2(
        Vector((relative.x, relative.y, relative.z)).dot(axis), relative.w
    )
    angle = (angle + math.pi) % (2 * math.pi) - math.pi
    for index in [1, 2]:
        bone = rig.pose.bones[name + "Twist" + str(index)]
        matrix = (
            delta @ Matrix.Rotation(angle * index / 2, 4, axis) @ bone.bone.matrix_local
        )
        matrix.translation = fore.head.copy()
        bone.matrix = matrix
        bone.rotation_mode = "QUATERNION"
        bpy.context.view_layer.update()
        if frame is not None:
            bone.keyframe_insert("location", frame=frame)
            bone.keyframe_insert("rotation_quaternion", frame=frame)
    return angle


def transport_rotation(rest_direction, posed_direction, parent_rotation):
    """Shortest swing in the parent's transported frame, with no extra axial roll."""
    old = Vector(rest_direction).normalized()
    new = (parent_rotation.inverted().to_3x3() @ Vector(posed_direction)).normalized()
    return parent_rotation @ old.rotation_difference(new).to_matrix().to_4x4()


def arm_rotations(upper_rest, fore_rest, upper_posed, fore_posed, torso):
    upper = transport_rotation(upper_rest, upper_posed, torso)
    fore = transport_rotation(fore_rest, fore_posed, upper)
    return upper, fore


def calibrate_ankle_weights(body, rig):
    """Blend at the calibrated ankle, rather than rotating the distal calf as foot.

    The original height mask faded from 8 to 13 cm in a unit-height character,
    entirely above its 6.5 cm ankle. A joint-centred band preserves the lower shin.
    Toe influence is assigned independently along the forefoot for later toe poses.
    """
    counts = {}
    for side, sign in [("Left", 1), ("Right", -1)]:
        prefix = "mixamorig:" + side
        ankle = rig.data.bones[prefix + "Foot"].head_local
        toe = rig.data.bones[prefix + "ToeBase"].head_local
        groups = {
            part: body.vertex_groups[prefix + part]
            for part in ["Leg", "Foot", "ToeBase"]
        }
        count = 0
        for vertex in body.data.vertices:
            p = vertex.co
            if p.y * sign <= 0 or p.z > ankle.z + 0.085:
                continue
            foot = max(0.0, min(1.0, (ankle.z + 0.025 - p.z) / 0.05))
            foot = foot * foot * (3 - 2 * foot)
            distal = max(0.0, min(1.0, (p.x - toe.x + 0.012) / 0.024))
            distal = distal * distal * (3 - 2 * distal)
            # Blender group memberships are live views; cache indices before
            # removal, otherwise subsequent entries can refer to shifted data.
            indices = [
                g.group
                for g in vertex.groups
                if body.vertex_groups[g.group].name in rig.data.bones
                and rig.data.bones[body.vertex_groups[g.group].name].use_deform
            ]
            for index in indices:
                body.vertex_groups[index].remove([vertex.index])
            for part, weight in [
                ("Leg", 1 - foot),
                ("Foot", foot * (1 - distal)),
                ("ToeBase", foot * distal),
            ]:
                if weight > 0:
                    groups[part].add([vertex.index], weight, "REPLACE")
            count += 1
        counts[side] = count
    body["deformation_rig_version"] = VERSION
    rig["deformation_rig_version"] = VERSION
    return counts
