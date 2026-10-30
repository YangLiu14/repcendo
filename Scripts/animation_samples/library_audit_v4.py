"""Version 4: supported curls, rotating grips, alternating raises, shrugs and rows.

Checks evaluated geometry against movement requirements; never trusts solver flags.
"""
import math
import bpy
import numpy as np
from mathutils import Vector
from collision_audit import mesh_data


def inspect(scene, config, frames):
    assert config.get("audit_version") == 4
    family = config["family"]
    assert family in ("curl", "cross_curl", "zottman", "press", "lateral_raise", "shrug", "bent_row")
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
    support_samples = []
    first_shoulders = {}
    first_trunk = None
    required_pads = ["Seat cushion", "Back support"] if config.get("back_support") else []
    for pad in required_pads:
        if scene.objects.get(pad) is None:
            failures.append(dict(check="missing_support_object", pad=pad))
    support_ids = [v.index for v in body.data.vertices if any(g.weight > 0.4 and any(part in groups[g.group] for part in ("Hips", "UpLeg", "Spine", "Shoulder", "Head", "Neck")) for g in v.groups)]
    flat_regions = {
        region: [v.index for v in body.data.vertices if any(
            g.weight > 0.4 and any(part in groups[g.group] for part in parts)
            for g in v.groups)]
        for region, parts in (("upper_back", ("Spine2", "Shoulder")), ("head", ("Head",)))
    }
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
        for pad_name, axis in (("Bench pad", 2), ("Seat cushion", 2), ("Back support", 1)):
            pad = scene.objects.get(pad_name)
            if pad is None:
                continue
            inv = np.array(pad.matrix_world.inverted())
            local = points[support_ids] @ inv[:3,:3].T + inv[:3,3]
            box = np.array([tuple(v.co) for v in pad.data.vertices])
            lo, hi = box.min(0), box.max(0)
            other = [i for i in range(3) if i != axis]
            within = np.all((local[:,other] >= lo[other]) & (local[:,other] <= hi[other]),axis=1)
            gap = float((local[within,axis].min()-hi[axis])*pad.matrix_world.to_3x3().col[axis].length) if within.any() else 999
            support_samples.append(dict(frame=f,pad=pad_name,gap=gap))
            if not -0.002 <= gap <= 0.015:
                failures.append(dict(frame=f,check="missing_or_penetrating_support",pad=pad_name,gap=gap))
            if pad_name == "Bench pad":
                # Glute contact alone cannot prove supine head/back support.
                for region, ids in flat_regions.items():
                    region_local = points[ids] @ inv[:3,:3].T + inv[:3,3]
                    inside = np.all((region_local[:,other] >= lo[other]) & (region_local[:,other] <= hi[other]),axis=1)
                    region_gap = float((region_local[inside,axis].min()-hi[axis])*pad.matrix_world.to_3x3().col[axis].length) if inside.any() else 999
                    support_samples.append(dict(frame=f,pad=pad_name,region=region,gap=region_gap))
                    if not -0.002 <= region_gap <= 0.015:
                        failures.append(dict(frame=f,check="missing_supine_support",region=region,gap=region_gap))
        trunk = np.array([tuple(rig.matrix_world @ rig.pose.bones["mixamorig:"+part].head)
                          for part in ("Hips", "Spine", "Spine1", "Spine2", "Head")])
        if first_trunk is None:
            first_trunk = trunk.copy()
        trunk_drift = float(np.linalg.norm(trunk-first_trunk, axis=1).max())
        axis = Vector(trunk[3]-trunk[0]).normalized()
        if trunk_drift > 1e-4:
            failures.append(dict(frame=f,check="trunk_sway",drift=trunk_drift))
        if family == "bent_row" and not (0.72 < axis.y < 0.94 and 0.33 < axis.z < 0.70):
            failures.append(dict(frame=f,check="missing_hip_hinge",axis=list(axis)))
        if config.get("back_support") and not (-0.64 < axis.y < -0.38 and 0.70 < axis.z < 0.94):
            failures.append(dict(frame=f,check="missing_incline_position",axis=list(axis)))
        bends = []
        for side, sign in (("Left", -1), ("Right", 1)):
            prefix = "mixamorig:" + side
            fore, hand = rig.pose.bones[prefix + "ForeArm"], rig.pose.bones[prefix + "Hand"]
            foredir = (rig.matrix_world.to_3x3() @ (fore.tail - fore.head)).normalized()
            handdir = (rig.matrix_world.to_3x3() @ (hand.tail - hand.head)).normalized()
            wrist_bend = math.degrees(handdir.angle(foredir))
            palm = (rig.matrix_world.to_3x3() @ (hand.matrix @ hand.bone.matrix_local.inverted()).to_3x3() @ Vector((0, -1 if side == "Left" else 1, 0))).normalized()
            phase = (f - 1) / scene.frame_end
            if family == "lateral_raise":
                horizontal = Vector((foredir.x, foredir.y, 0)).normalized()
                intended = horizontal * foredir.z + Vector((0, 0, -math.hypot(foredir.x, foredir.y)))
            elif family == "cross_curl":
                active = (phase < .5 and sign == -1) or (phase >= .5 and sign == 1)
                effort = math.sin(2*math.pi*phase)**2 if active else 0
                intended = Vector((-sign*(1-.4*effort), -.95*effort, 0)).normalized()
            elif config["grip"] == "neutral":
                intended = Vector((-sign, 0, 0))
            else:
                intended = Vector((0, -foredir.z, foredir.y)).normalized()
                if config["grip"] == "pronated":
                    intended = -intended
                if family == "zottman":
                    # Linear reference intervals allow eased rotation, but require
                    # supinated ascent and pronated descent from actual palms.
                    if phase < .375:
                        turn = 0
                    elif phase < .5:
                        turn = math.pi*(phase-.375)/.125
                    elif phase < .875:
                        turn = math.pi
                    else:
                        turn = math.pi*(1-(phase-.875)/.125)
                    from mathutils import Matrix
                    intended = Matrix.Rotation(-sign*turn,4,foredir) @ intended
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
            shoulder = rig.matrix_world @ arm.head
            first_shoulders.setdefault(side, shoulder.copy())
            shoulder_delta = shoulder-first_shoulders[side]
            wrist_delta = wrist-first_wrists[side]
            low = (f in (1, 1+scene.frame_end//2, scene.frame_end+1) if config.get("alternating") else f in (1, scene.frame_end+1))
            if family == "zottman":
                peak = f in (1+3*scene.frame_end//8,1+scene.frame_end//2)
                if .375 <= phase <= .5 and not 70 <= flexion <= 140:
                    failures.append(dict(frame=f,side=side,check="turn_not_at_top",flexion=flexion))
                if phase >= .875 and flexion > 25:
                    failures.append(dict(frame=f,side=side,check="reset_not_at_bottom",flexion=flexion))
            if family == "press":
                if foredir.z < .85:
                    failures.append(dict(frame=f,side=side,check="forearm_not_stacked",vertical=foredir.z))
                if low and not 65 <= flexion <= 120:
                    failures.append(dict(frame=f,side=side,check="press_return_range",flexion=flexion))
            elif family in ("curl","cross_curl","zottman"):
                if elbow_drift > 1e-4:
                    failures.append(dict(frame=f,side=side,check="curl_elbow_shift",drift=elbow_drift))
                if low and flexion > 25:
                    failures.append(dict(frame=f,side=side,check="curl_return_range",flexion=flexion))
                if config.get("back_support") and upperdir.z > -.94:
                    failures.append(dict(frame=f,side=side,check="incline_arm_not_hanging",upper=list(upperdir)))
            elif family == "shrug":
                if flexion > 12 or (wrist_delta-shoulder_delta).length > 1e-4:
                    failures.append(dict(frame=f,side=side,check="shrug_arm_bending",flexion=flexion))
                if abs(shoulder_delta.y) > .015 or abs(shoulder_delta.x) > .025:
                    failures.append(dict(frame=f,side=side,check="shoulder_rolling",delta=list(shoulder_delta)))
            elif family == "bent_row":
                if foredir.z > -.85 or (low and flexion > 25):
                    failures.append(dict(frame=f,side=side,check="row_return_or_forearm",flexion=flexion,fore=list(foredir)))
            if idle_drift > 1e-4:
                failures.append(dict(frame=f, side=side, check="inactive_arm_moved", drift=idle_drift))
            if peak and not inactive:
                if family == "press":
                    valid_peak = 150 <= elevation <= 180 and flexion <= 25
                elif family in ("curl","cross_curl","zottman"):
                    valid_peak = 70 <= flexion <= 140
                elif family == "shrug":
                    valid_peak = .03 <= shoulder_delta.z <= .10 and flexion <= 12
                elif family == "bent_row":
                    valid_peak = upperdir.y < -.6 and 65 <= flexion <= 110 and wrist_delta.z > .12
                else:
                    valid_peak = 75 <= elevation <= 105 and flexion <= 20
                if not valid_peak:
                    failures.append(dict(frame=f, side=side, check="peak_range", elevation=elevation, flexion=flexion, shoulderRise=shoulder_delta.z, wristRise=wrist_delta.z))
                if family == "cross_curl" and not (sign*wrist.x < .035 and thumb_end.z > .5 and wrist.y > shoulder.y+.12):
                    failures.append(dict(frame=f,side=side,check="missing_cross_body_path",wrist=list(wrist),thumbUp=thumb_end.z))
                if family == "lateral_raise" and abs(upperdir.x) < 3*abs(upperdir.y):
                    failures.append(dict(frame=f,side=side,check="not_lateral_plane",upper=list(upperdir)))
            bends.append(flexion)
            r = dict(frame=f, side=side, wristBendDegrees=wrist_bend, palmIntentDot=palm_dot,
                     sectors=sectors, minSurfaceRadius=float(radius.min()), digitGaps=gaps,
                     handDrift=drift, elbowDrift=elbow_drift, elbowFlexionDegrees=flexion,
                     shoulderElevationDegrees=elevation, inactiveArmDrift=idle_drift, thumbEndUp=thumb_end.z,
                     shoulderRise=shoulder_delta.z,wristRise=wrist_delta.z,palm=list(palm),wrist=list(wrist),upperDirection=list(upperdir))
            samples.append(r)
            if (wrist_bend > 15 or palm_dot < 0.8 or sectors < 10 or radius.min() < 0.013
                    or max(gaps.values()) > 0.008 or drift > 1e-4):
                failures.append({"check": "grip_or_motion_intent", **r})
    if max_foot_drift > 1e-4 or loop_error > 1e-4:
        failures.append(dict(check="foot_or_loop_drift", foot=max_foot_drift, loop=loop_error))
    return dict(failures=failures, samples=samples, supportSamples=support_samples, maxFootDrift=max_foot_drift, meshLoopError=loop_error)
