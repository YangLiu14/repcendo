"""Fit support hardware to evaluated skin, in metres; never deform away collisions.

Pads are rigid for the entire cycle. Only intended moving apparatus (sled and
shin rollers) receives per-frame contact tracks. The independent audit is the gate.
"""
import json
import bpy
import numpy as np
from mathutils import Vector
from collision_audit import mesh_data

GAP = 0.0025


def bone_labels(body):
    return np.array(
        [
            body.vertex_groups[
                max(
                    (
                        g
                        for g in v.groups
                        if body.vertex_groups[g.group].name.startswith("mixamorig:")
                    ),
                    key=lambda g: g.weight,
                ).group
            ].name
            if v.groups
            else ""
            for v in body.data.vertices
        ]
    )


def subset(labels, words):
    return np.array([any(word in label for word in words) for label in labels])


def fit_contacts(scene, body, exercise):
    labels = bone_labels(body)
    cache = []
    for f in range(1, scene.frame_end + 2):
        scene.frame_set(f)
        cache.append(mesh_data(body, bpy.context.evaluated_depsgraph_get())[0])
    scene.frame_set(1)
    changes = []

    def support(obj, axis, sign, words, dynamic=False):
        """Place one face behind the skin in its rectangular contact footprint."""
        mask = subset(labels, words)
        shifts = []
        static = not obj.animation_data and not (
            obj.parent and obj.parent.animation_data
        )
        for f, coords in enumerate(cache, 1):
            if not static:
                scene.frame_set(f)
            inv = np.array(obj.matrix_world.inverted())
            local = coords[mask] @ inv[:3, :3].T + inv[:3, 3]
            vertices = np.array([tuple(v.co) for v in obj.data.vertices])
            lo, hi = vertices.min(0), vertices.max(0)
            others = [a for a in range(3) if a != axis]
            within = np.all(
                (local[:, others] >= lo[others]) & (local[:, others] <= hi[others]),
                axis=1,
            )
            if not within.any():
                raise ValueError(f"No skin in contact footprint: {obj.name} frame {f}")
            scale = obj.matrix_world.to_3x3().col[axis].length
            skin = (local[within, axis] * sign).min()
            face = hi[axis] if sign == 1 else -lo[axis]
            shifts.append((skin - face) * scale - GAP)
        if not dynamic:
            shifts = [min(shifts)] * len(cache)
        for f, shift in enumerate(shifts, 1):
            scene.frame_set(f)
            direction = obj.matrix_world.to_3x3().col[axis].normalized() * sign
            world_delta = direction * shift
            obj.location += (
                obj.parent.matrix_world.to_3x3().inverted() @ world_delta
                if obj.parent
                else world_delta
            )
            if dynamic:
                obj.keyframe_insert("location", frame=f)
            else:
                break
        changes.append(
            dict(object=obj.name, min_shift_m=min(shifts), max_shift_m=max(shifts))
        )
        return min(shifts)

    seat = (
        scene.objects.get("Seat cushion")
        or scene.objects.get("Seat")
        or scene.objects.get("Bench pad")
    )
    if seat:
        support(seat, 2, 1, ["Hips", "UpLeg", "Spine", "Shoulder", "Head", "Neck"])
        scene.frame_set(1)
        bottom = seat.location.z - seat.dimensions.z / 2
        beam = scene.objects.get("Bench longitudinal frame")
        if beam is not None:
            beam.location.z = bottom - beam.dimensions.z / 2
        for obj in scene.objects:
            if obj.name.startswith(("Seat pedestal", "Seat support", "Bench leg")):
                obj.location.z = (bottom + 0.06) / 2
                obj.dimensions.z = max(0.02, bottom - 0.06)
    back = scene.objects.get("Back support")
    if back:
        support(back, 1, 1, ["Hips", "Spine", "Shoulder", "Head", "Neck"])
        scene.frame_set(1)
        frame = scene.objects.get("Back frame")
        if frame:
            frame.animation_data_clear()
            frame.location = back.location - back.matrix_world.to_3x3().col[
                1
            ].normalized() * (0.05 + 0.0375)
            frame.rotation_euler = back.rotation_euler
            frame.scale.z = 0.82
    chest = scene.objects.get("Chest support")
    if chest:
        support(chest, 1, -1, ["Spine", "Hips"])
    for name in ["Thigh hold-down", "Thigh restraint"]:
        if scene.objects.get(name):
            support(scene.objects[name], 2, -1, ["UpLeg"])
    for obj in scene.objects:
        if obj.name.startswith("Shoulder pad"):
            support(obj, 2, -1, ["Shoulder", "Arm", "Spine", "Neck"])
    if exercise == "row":
        support(scene.objects["Foot plate"], 2, 1, ["Foot", "ToeBase"])
    if exercise == "leg_press":
        support(
            scene.objects["Sled footplate"], 2, 1, ["Foot", "ToeBase"], dynamic=True
        )
    if exercise in ("leg_curl", "leg_extension"):
        # Rollers touch the shin surface, with a measured gap, instead of its bone.
        for side in ["Left", "Right"]:
            roller = scene.objects["Shin roller " + side]
            shin_mask = subset(labels, [side + "Leg", side + "Foot"])
            rig = next(o for o in scene.objects if o.type == "ARMATURE")
            for f, coords in enumerate(cache, 1):
                scene.frame_set(f)
                ankle = (
                    rig.matrix_world @ rig.pose.bones["mixamorig:" + side + "Foot"].head
                )
                knee = (
                    rig.matrix_world @ rig.pose.bones["mixamorig:" + side + "Leg"].head
                )
                up = (knee - ankle).normalized()
                front = Vector((1, 0, 0)).cross(up).normalized() * -1
                offset = coords[shin_mask] - np.array(ankle)
                z = offset @ np.array(up)
                patch = offset[(z >= 0.06) & (z <= 0.18)]
                sign = -1 if exercise == "leg_curl" else 1
                distance = (patch @ np.array(front) * sign).max() + 0.065 + GAP
                roller.location = ankle + up * 0.12 + front * (sign * distance)
                roller.keyframe_insert("location", frame=f)
                lever = scene.objects["Knee lever " + side]
                s = -1 if side == "Left" else 1
                a = knee + Vector((s * 0.20, 0, 0))
                b = roller.location + Vector((s * 0.20, 0, 0))
                lever.location = (a + b) / 2
                lever.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
                lever.scale.z = (b - a).length
                for prop in ("location", "rotation_euler", "scale"):
                    lever.keyframe_insert(prop, frame=f)
            changes.append(
                dict(object=roller.name, contact="skin-fitted shin, 2.5 mm clearance")
            )
    if exercise in ("pec_fly", "reverse_fly"):
        from pec_deck import fit_pad_frame
        fit_pad_frame(scene)
    scene["contact_surface_fit"] = json.dumps(changes)
    scene.frame_set(1)
