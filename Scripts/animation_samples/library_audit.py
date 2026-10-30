"""Full-cycle dumbbell grip, wrist, motion intent, foot and mesh-loop checks."""
import math
import bpy
import numpy as np
from mathutils import Vector
from collision_audit import mesh_data


def inspect(scene, config, frames):
    rig = next(o for o in scene.objects if o.type == "ARMATURE")
    body = next(o for o in scene.objects if o.type == "MESH" and any(m.type == "ARMATURE" for m in o.modifiers))
    feet = [v.index for v in body.data.vertices if v.co.z < 0.025]
    groups = {g.index: g.name for g in body.vertex_groups}
    selected, digits, stable = {}, {}, {}
    for side in ("Left", "Right"):
        prefix = f"mixamorig:{side}Hand"
        weights = {v.index: sum(g.weight for g in v.groups if groups[g.group].startswith(prefix)) for v in body.data.vertices}
        selected[side] = [i for i, w in weights.items() if w > 0.65]
        stable[side] = [i for i, w in weights.items() if w > 0.9999]
        for digit in ("Thumb", "Index", "Middle", "Ring", "Pinky"):
            digits[side, digit] = [v.index for v in body.data.vertices if sum(g.weight for g in v.groups if groups[g.group].startswith(prefix + digit)) > 0.7]
    failures, samples, first_grips, first_elbows, first_wrists = [], [], {}, {}, {}
    first = None
    max_foot_drift = 0
    loop_error = 0
    for f in frames:
        scene.frame_set(f)
        points, _ = mesh_data(body, bpy.context.evaluated_depsgraph_get())
        if first is None:
            first = points.copy()
        if not np.isfinite(points).all():
            failures.append({"frame": f, "check": "non_finite_mesh"})
        max_foot_drift = max(max_foot_drift, float(np.linalg.norm(points[feet] - first[feet], axis=1).max()))
        if f == scene.frame_end + 1:
            loop_error = float(np.linalg.norm(points - first, axis=1).max())
        bends = []
        for side, sign in (("Left", -1), ("Right", 1)):
            prefix = "mixamorig:" + side
            fore, hand = rig.pose.bones[prefix + "ForeArm"], rig.pose.bones[prefix + "Hand"]
            foredir = (rig.matrix_world.to_3x3() @ (fore.tail - fore.head)).normalized()
            handdir = (rig.matrix_world.to_3x3() @ (hand.tail - hand.head)).normalized()
            wrist_bend = math.degrees(handdir.angle(foredir))
            palm = (rig.matrix_world.to_3x3() @ (hand.matrix @ hand.bone.matrix_local.inverted()).to_3x3() @ Vector((0, -1 if side == "Left" else 1, 0))).normalized()
            if config["family"] == "scaption":
                intended = Vector((-sign * 0.5, math.sqrt(3) / 2, 0))
            elif config["family"] in ("lateral_raise", "lateral_front"):
                horizontal = Vector((foredir.x, foredir.y, 0)).normalized()
                intended = -horizontal * (-foredir.z) + Vector((0, 0, -math.hypot(foredir.x, foredir.y)))
            elif config["grip"] == "neutral":
                intended = Vector((-sign, 0, 0))
            else:
                intended = Vector((0, -foredir.z, foredir.y)).normalized()
                if config["grip"] == "pronated":
                    intended = -intended
            palm_dot = palm.dot(intended)
            grip = scene.objects["Grip." + side]
            local = np.array(grip.matrix_world.inverted())
            coords = points @ local[:3, :3].T + local[:3, 3]
            radial = coords[selected[side]][:, 1:]
            radius = np.linalg.norm(radial, axis=1)
            near = radial[(radius >= 0.013) & (radius <= 0.026)]
            sectors = len(set((np.floor((np.arctan2(near[:, 1], near[:, 0]) + np.pi) * 12 / (2 * np.pi)).astype(int) % 12).tolist()))
            gaps = {digit: float(np.abs(np.linalg.norm(coords[ids][:, 1:], axis=1) - 0.014).min()) if ids else 999 for (s, digit), ids in digits.items() if s == side}
            rel = coords[stable[side]]
            if side not in first_grips:
                first_grips[side] = rel.copy()
            drift = float(np.linalg.norm(rel - first_grips[side], axis=1).max())
            elbow = rig.matrix_world @ fore.head
            if side not in first_elbows:
                first_elbows[side] = elbow.copy()
            elbow_drift = (elbow - first_elbows[side]).length
            arm = rig.pose.bones[prefix + "Arm"]
            flexion = math.degrees((fore.tail - fore.head).angle(arm.tail - arm.head))
            upperdir = (rig.matrix_world.to_3x3() @ (arm.tail - arm.head)).normalized()
            elevation = math.degrees(upperdir.angle(Vector((0, 0, -1))))
            wrist = rig.matrix_world @ hand.head
            first_wrists.setdefault(side, wrist.copy())
            phase = (f - 1) / scene.frame_end
            inactive = config.get("alternating") and ((phase < 0.5 and side == "Right") or (phase >= 0.5 and side == "Left"))
            idle_drift = (wrist - first_wrists[side]).length if inactive else 0
            # Verify phase semantics from evaluated bones, independently of the
            # solver: raised side, lifting plane and actual thumb end of the fist.
            peak = f in ((1 + scene.frame_end // 4, 1 + 3 * scene.frame_end // 4)
                         if config.get("alternating") or config.get("quarter_phases") else (1 + scene.frame_end // 2,))
            index = rig.pose.bones[prefix + "HandIndex1"].head
            pinky = rig.pose.bones[prefix + "HandPinky1"].head
            thumb_end = (rig.matrix_world.to_3x3() @ (index - pinky)).normalized()
            if idle_drift > 1e-4:
                failures.append(dict(frame=f, side=side, check="inactive_arm_moved", drift=idle_drift))
            if peak and not inactive:
                if config["family"] == "curl":
                    valid_peak = 70 <= flexion <= 140
                else:
                    valid_peak = 75 <= elevation <= 105 and flexion <= 20
                if not valid_peak:
                    failures.append(dict(frame=f, side=side, check="peak_range", elevation=elevation, flexion=flexion))
                if config["family"] == "scaption" and (thumb_end.z < 0.7 or not 0.35 < upperdir.y / abs(upperdir.x) < 0.8):
                    failures.append(dict(frame=f, side=side, check="full_can_orientation", thumbUp=thumb_end.z, upper=list(upperdir)))
                if config["family"] == "lateral_front":
                    lateral = phase < 0.5
                    if (abs(upperdir.x) < 3 * upperdir.y if lateral else upperdir.y < 3 * abs(upperdir.x)):
                        failures.append(dict(frame=f, side=side, check="lateral_front_sequence", upper=list(upperdir)))
            bends.append(flexion)
            r = dict(frame=f, side=side, wristBendDegrees=wrist_bend, palmIntentDot=palm_dot,
                     sectors=sectors, minSurfaceRadius=float(radius.min()), digitGaps=gaps,
                     handDrift=drift, elbowDrift=elbow_drift, elbowFlexionDegrees=flexion,
                     shoulderElevationDegrees=elevation, inactiveArmDrift=idle_drift, thumbEndUp=thumb_end.z)
            samples.append(r)
            if (wrist_bend > 15 or palm_dot < 0.8 or sectors < 10 or radius.min() < 0.013
                    or max(gaps.values()) > 0.008 or drift > 1e-4
                    or (config["family"] == "curl" and elbow_drift > 1e-4)):
                failures.append({"check": "grip_or_motion_intent", **r})
        if config.get("alternating") and config["family"] == "curl" and min(bends) > 25:
            failures.append(dict(frame=f, check="both_arms_curling", angles=bends))
    if max_foot_drift > 1e-4 or loop_error > 1e-4:
        failures.append(dict(check="foot_or_loop_drift", foot=max_foot_drift, loop=loop_error))
    return dict(failures=failures, samples=samples, maxFootDrift=max_foot_drift, meshLoopError=loop_error)
