"""Original motion/equipment adapters for the plan. World +Y forward, +Z up.

All limbs retain calibrated lengths. Equipment follows explicit grip frames;
seated knee rollers and leg-press sleds follow the actual solved joints.
"""
import math
import bpy
from mathutils import Vector, Matrix
from plan_exercises import PLAN_EXERCISES
from deformation_rig import arm_rotations, pose_forearm_twist


def unit(v):
    return Vector(v).normalized()


class PlanMotion:
    def __init__(self, env, config=None):
        for k in (
            "args",
            "rig",
            "character",
            "head",
            "tail",
            "rest",
            "hip0",
            "scale",
            "L",
            "grip_offsets",
            "ankle_z",
            "stand_z",
            "SIDES",
            "hand_centers",
            "hand_chains",
            "cube",
            "cylinder",
            "empty",
            "setbone",
            "orient",
            "ik",
            "rx",
            "frame",
            "pose_fingers",
            "STEEL",
            "DARK",
            "PAD",
            "ACCENT",
            "contact_errors",
            "length_errors",
            "pose_records",
        ):
            setattr(self, k, env[k])
        self.name = self.args.exercise
        self.config = config if config is not None else PLAN_EXERCISES[self.name]
        self.frames = self.config.get("frames", 120)
        self.open = self.config.get("open_hands", False)
        self.items = {}
        self.grips = {}
        self.pose_data = {}
        self.body = {}
        self.soles = {
            sign: [
                self.character.matrix_world @ v.co
                - self.head["mixamorig:" + side + "Foot"]
                for v in self.character.data.vertices
                if v.co.z < 0.025 and (self.character.matrix_world @ v.co).x * sign > 0
            ]
            for sign, side in self.SIDES.items()
        }
        self.rot_inv = (
            self.rig.matrix_world.to_quaternion().to_matrix().to_4x4().inverted()
        )
        self.seated = self.config.get("seated", False) or self.name in (
            "incline_press",
            "pec_fly",
            "pulldown",
            "leg_press",
            "leg_curl",
            "leg_extension",
            "shoulder_press",
            "reverse_fly",
        )
        self.floor = self.name in ("reverse_crunch", "dead_bug")
        if self.args.view == "motion":
            self.equipment()

    def block(self, name, p, size, pad=False, rotation=0):
        obj = self.cube(name, p, size, self.PAD if pad else self.DARK, 0.018)
        obj.rotation_euler.x = rotation
        self.items[name] = obj
        return obj

    def rod(self, name, a, b, radius=0.018, mat=None):
        obj = self.items.get(name)
        if obj is None:
            obj = self.cylinder(name, (0, 0, 0), (0, 0, 1), radius, mat or self.STEEL)
            self.items[name] = obj
        a, b = Vector(a), Vector(b)
        obj.location = (a + b) / 2
        obj.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
        obj.scale.z = (b - a).length
        for prop in ("location", "rotation_euler", "scale"):
            obj.keyframe_insert(prop, frame=self.f)
        return obj

    def equipment(self):
        self.f = 1
        n = self.name
        if self.floor:
            self.block("Exercise mat", (0, 0.15, 0.015), (0.86, 2.50, 0.025), True)
            return
        for s, side in self.SIDES.items():
            grip = self.empty("Grip." + side)
            self.grips[s] = grip
            self.cylinder(
                "Grip shaft " + side,
                (
                    -0.045
                    if n == "calf_raise" and self.args.sex == "female"
                    else -0.09,
                    0,
                    0,
                ),
                (0.09, 0, 0),
                0.014,
                self.STEEL,
                grip,
            )
            if n in ("curl", "lateral_raise", "incline_press", "shoulder_press"):
                for sign in (-1, 1):
                    self.cylinder(
                        "Dumbbell plate",
                        (sign * 0.10, 0, 0),
                        (sign * 0.16, 0, 0),
                        0.085,
                        self.DARK,
                        grip,
                    )
        if self.seated:
            h = 0.49 if n not in ("leg_curl", "leg_extension") else 0.57
            self.block(
                "Seat cushion",
                (
                    0,
                    0.02
                    if n in ("incline_press", "leg_curl", "leg_extension")
                    else 0.10,
                    h,
                ),
                (0.34, 0.28, 0.10)
                if n in ("incline_press", "leg_curl")
                else (0.43, 0.46, 0.10),
                True,
            )
            self.block("Seat pedestal", (0, 0.05, h / 2), (0.12, 0.16, h))
            self.block("Seat base", (0, 0.05, 0.04), (0.70, 0.85, 0.08))
            if n == "pec_fly":
                self.block("Back support", (0, -0.15, 0.94), (0.30, 0.10, 0.54), True)
            elif n not in ("reverse_fly", "pulldown"):
                angle = (
                    math.pi / 3
                    if n == "incline_press"
                    else (1.0 if n == "leg_press" else 0.08)
                )
                origin = Vector((0, -0.03, h + 0.08))
                center = origin + self.rx(angle) @ Vector((0, -0.08, 0.38))
                self.block("Back support", center, (0.33, 0.10, 0.86), True, angle)
                self.rod(
                    "Back frame",
                    origin,
                    center + self.rx(angle) @ Vector((0, 0, 0.38)),
                    0.035,
                    self.DARK,
                )
            elif n == "reverse_fly":
                self.block("Chest support", (0, 0.24, 0.94), (0.30, 0.10, 0.54), True)
        if n in ("pushdown", "pulldown", "straight_pulldown", "cable_crunch"):
            y = 1.05 if n != "pulldown" else 1.00
            self.anchor = Vector((0, y, 2.18))
            for s in (-1, 1):
                self.block("Cable tower", (s * 0.36, y + 0.12, 1.1), (0.06, 0.10, 2.2))
                self.block("Tower foot", (s * 0.44, y, 0.04), (0.14, 0.60, 0.08))
            self.block("Tower bridge", (0, y + 0.12, 2.18), (0.79, 0.13, 0.08))
            for j in range(8):
                self.block(
                    "Stack plate", (0, y + 0.12, 0.15 + j * 0.045), (0.33, 0.16, 0.035)
                )
            self.cylinder(
                "High pulley", (-0.035, y, 2.18), (0.035, y, 2.18), 0.07, self.STEEL
            )
            if n == "pulldown":
                self.block("Thigh restraint", (0, 0.30, 0.75), (0.62, 0.14, 0.10), True)
            if n == "cable_crunch":
                self.block("Kneeling mat", (0, -0.08, 0.015), (0.75, 1.05, 0.025), True)
        if n in ("pec_fly", "reverse_fly"):
            from pec_deck import PecDeck
            self.pec_deck = PecDeck(self)
        if n in ("leg_curl", "leg_extension"):
            for sign in (-1, 1):
                self.block(
                    "Leg machine beam", (sign * 0.46, 0.28, 0.10), (0.10, 1.25, 0.12)
                )
            if n == "leg_curl":
                self.block("Thigh hold-down", (0, 0.44, 0.77), (0.64, 0.14, 0.10), True)
        if n == "leg_press":
            self.block(
                "Sled footplate", (0, 0.8, 1), (0.76, 0.52, 0.07), True, 3 * math.pi / 4
            )
            for s in (-1, 1):
                self.rod(
                    "Sled guide " + str(s),
                    (s * 0.56, 0.24, 0.30),
                    (s * 0.56, 1.30, 1.36),
                    0.035,
                )
                self.block(
                    "Sled upright " + str(s), (s * 0.56, 1.30, 0.69), (0.09, 0.10, 1.38)
                )
            self.block("Sled base", (0, 0.62, 0.045), (1.24, 1.90, 0.09))
        if n == "calf_raise":
            self.block("Calf step", (0, 0.20, 0.05), (0.64, 0.24, 0.10), True)
            self.carriage = self.empty("Calf moving carriage")
            for s in (-1, 1):
                self.block("Calf frame", (s * 0.48, -0.22, 1.05), (0.07, 0.10, 2.1))
                pad = self.cube(
                    "Shoulder pad",
                    (s * 0.26, 0, 0),
                    (0.14, 0.26, 0.10),
                    self.PAD,
                    0.025,
                    self.carriage,
                )
            self.block("Calf base", (0, -0.05, 0.035), (1.04, 0.80, 0.07))
        if n == "rdl":
            self.bar = self.empty("RDL barbell")
            self.cylinder(
                "Barbell shaft",
                (-0.94, 0, 0),
                (0.94, 0, 0),
                0.014,
                self.STEEL,
                self.bar,
            )
            for s in (-1, 1):
                self.cylinder(
                    "Sleeve",
                    (s * 0.60, 0, 0),
                    (s * 0.94, 0, 0),
                    0.024,
                    self.STEEL,
                    self.bar,
                )
                self.cylinder(
                    "Weight plate",
                    (s * 0.72, 0, 0),
                    (s * 0.79, 0, 0),
                    0.16,
                    self.DARK,
                    self.bar,
                )
                self.cylinder(
                    "Collar",
                    (s * 0.81, 0, 0),
                    (s * 0.84, 0, 0),
                    0.032,
                    self.ACCENT,
                    self.bar,
                )

    def torso(self, d):
        n = self.name
        angle = 0
        hip = Vector((0, 0, self.stand_z))
        if self.seated:
            hip = Vector((0, 0.05, 0.605))
            angle = 0.08
        if n == "incline_press":
            angle = math.pi / 3
        if n == "leg_press":
            angle = 1.0
        if n in ("leg_curl", "leg_extension"):
            hip.z = 0.69
        if n in ("rdl", "straight_pulldown", "pushdown"):
            angle = -0.85 * d if n == "rdl" else -0.10
            hip.y = 0.07 - 0.25 * d if n == "rdl" else -0.03
            hip.z -= 0.08 * d if n == "rdl" else 0.01
        if self.floor:
            hip = Vector((0, 0.10, 0.20 if self.args.sex == "male" else 0.19))
            angle = math.pi / 2
        if n == "cable_crunch":
            hip = Vector((0, -0.05, 0.09 + self.L[-1, "thigh"] * 0.99955))
            angle = -0.05
        if n == "calf_raise":
            ankle, _ = self.calf_ankle(-1, d)
            hip += Vector((0, ankle.y, ankle.z - self.ankle_z))
        hip += Vector(self.config.get("hip_offset", (0, 0, 0)))
        angle = self.config.get("torso_angle", angle)
        angle += self.config.get("torso_angle_offset_by_sex", {}).get(self.args.sex, 0)
        angles = {b.name: angle for b in self.rig.data.bones}
        head_offset = self.config.get("head_angle_offset_by_sex", {}).get(self.args.sex, 0)
        for part in ("Neck", "Head", "HeadTop_End"):
            angles["mixamorig:" + part] = angle + head_offset
        if n == "cable_crunch":
            for bone, a in [
                ("Spine", -0.10 - 0.20 * d),
                ("Spine1", -0.15 - 0.40 * d),
                ("Spine2", -0.20 - 0.65 * d),
            ]:
                angles["mixamorig:" + bone] = a
            for bone in (
                "Neck",
                "Head",
                "HeadTop_End",
                "LeftShoulder",
                "RightShoulder",
            ):
                angles["mixamorig:" + bone] = -0.20 - 0.65 * d
        if n == "reverse_crunch":
            for bone, a in [
                ("Hips", angle + 0.32 * d),
                ("Spine", angle + 0.20 * d),
                ("Spine1", angle + 0.07 * d),
            ]:
                angles["mixamorig:" + bone] = a
            pivot = hip + self.rx(angle) @ (self.head["mixamorig:Spine2"] - self.hip0)
            offset = Vector((0, 0, 0))
            for parent, child in [
                ("Hips", "Spine"),
                ("Spine", "Spine1"),
                ("Spine1", "Spine2"),
            ]:
                offset += self.rx(angles["mixamorig:" + parent]) @ (
                    self.head["mixamorig:" + child] - self.head["mixamorig:" + parent]
                )
            hip = pivot - offset
        self.body = {}
        for bone in self.rig.data.bones:
            name = bone.name
            if (
                name == "Root"
                or any(
                    x in name
                    for x in ("UpLeg", "Leg", "Foot", "ToeBase", "ForeArm", "Hand")
                )
                or name.endswith("Arm")
            ):
                continue
            R = self.rx(angles[name])
            if name == "mixamorig:Hips":
                p = hip
            elif bone.parent and bone.parent.name in self.body:
                pp, pr = self.body[bone.parent.name]
                p = pp + pr @ (self.head[name] - self.head[bone.parent.name])
            else:
                p = hip + self.rx(angle) @ (self.head[name] - self.hip0)
            self.setbone(name, p, R, self.f)
            self.body[name] = (p.copy(), R)
        self.hip = hip
        self.R = self.body["mixamorig:Spine2"][1]

    def joint(self, name):
        parent = self.rig.data.bones[name].parent.name
        p, R = self.body[parent]
        return p + R @ (self.head[name] - self.head[parent])

    def calf_ankle(self, s, d):
        R = self.rx(-0.38 * d)
        pivot = Vector((s * 0.16, 0.15, 0.10))
        ankle = pivot + R @ (Vector((s * 0.16, 0, self.ankle_z + 0.10)) - pivot)
        lowest = min((ankle + R @ offset).z for offset in self.soles[s])
        ankle.z += 0.10 - lowest
        return ankle, R

    def leg(self, s, d, t):
        side = self.SIDES[s]
        prefix = "mixamorig:" + side
        hip = self.joint(prefix + "UpLeg")
        a, b = self.L[s, "thigh"], self.L[s, "shin"]
        n = self.name
        footR = Matrix.Identity(4)
        if n in ("leg_curl", "leg_extension"):
            knee = hip + Vector((0, a, 0))
            angle = 1.30 * (1 - d) if n == "leg_curl" else 1.30 * d
            ankle = knee + self.rx(angle) @ Vector((0, 0, -b))
            footR = self.rx(angle)
        elif n == "leg_press":
            hips = (
                self.joint("mixamorig:LeftUpLeg") + self.joint("mixamorig:RightUpLeg")
            ) / 2
            reach = min(self.L[k, "thigh"] + self.L[k, "shin"] for k in self.SIDES)
            ankle = hips + unit((0, 1, 1)) * reach * (0.92 - 0.24 * d)
            ankle.x = s * 0.23
            knee = self.ik(hip, ankle, a, b, hip + Vector((s * 0.30, 0.2, 1)))
            footR = self.rx(3 * math.pi / 4)
        elif n == "cable_crunch":
            # Hips sit slightly in front of the knees; shins stay on the mat.
            knee = hip + unit((0, -0.12, -1)) * a
            ankle = knee + unit((0, -1, 0)) * b
            footR = self.rx(3.85)
        elif self.floor:
            amount = (
                d
                if n == "reverse_crunch"
                else (
                    math.sin(2 * math.pi * t) ** 2
                    if ((t < 0.5 and s == 1) or (t >= 0.5 and s == -1))
                    else 0
                )
            )
            if n == "reverse_crunch":
                thigh = unit((0, -0.35 * amount, 1))
                shin = unit((0, 1, 0.35 * amount))
            else:
                thigh = unit((0, math.sin(1.32 * amount), math.cos(1.32 * amount)))
                shin = unit((0, 1, -0.1 * amount))
            knee = hip + thigh * a
            ankle = knee + shin * b
            footR = self.rx(
                math.pi / 2 + (math.atan(0.35 * amount) if n == "reverse_crunch" else 0)
            )
        else:
            ankle = Vector(
                (
                    s * (0.25 if n == "incline_press" else 0.16),
                    0.62 if self.seated else 0,
                    self.ankle_z,
                )
            )
            if n == "calf_raise":
                ankle, footR = self.calf_ankle(s, d)
            knee = self.ik(hip, ankle, a, b, hip + Vector((s * 0.08, 1, -0.2)))
        self.orient(prefix + "UpLeg", hip, knee, (1, 0, 0), self.f)
        self.orient(prefix + "Leg", knee, ankle, (1, 0, 0), self.f)
        self.setbone(prefix + "Foot", ankle, footR, self.f)
        toe = ankle + footR @ (
            self.head[prefix + "ToeBase"] - self.head[prefix + "Foot"]
        )
        self.setbone(prefix + "ToeBase", toe, footR, self.f)
        self.length_errors.extend(
            [abs((knee - hip).length - a), abs((ankle - knee).length - b)]
        )
        self.pose_data[side] = dict(hip=hip, knee=knee, ankle=ankle, footR=footR)

    def hand_rotation(self, axis, direction):
        z = -unit(direction)
        x = Vector(axis)
        x = (x - z * x.dot(z)).normalized()
        y = z.cross(x).normalized()
        basis = Matrix((x, y, z)).transposed().to_4x4()
        return basis @ self.rot_inv, basis

    def arm(self, s, d, t):
        side = self.SIDES[s]
        p = "mixamorig:" + side
        if self.name in ("dead_bug", "shoulder_press", "pec_fly", "reverse_fly"):
            sn = p + "Shoulder"
            sp, sr = self.body[sn]
            if self.name == "dead_bug":
                amount = (
                    math.sin(2 * math.pi * t) ** 2
                    if ((t < 0.5 and s == -1) or (t >= 0.5 and s == 1))
                    else 0
                )
                sr = sr @ Matrix.Rotation(-s * 0.45 * amount, 4, "Y")
                sr = sr @ Matrix.Rotation(s * 0.14 * (1 - amount), 4, "Z")
            elif self.name == "shoulder_press":
                sr = sr @ Matrix.Rotation(-s * 0.40 * d, 4, "Y")
            else:
                amount = d if self.name == "pec_fly" else 1 - d
                sr = sr @ Matrix.Rotation(s * 0.28 * amount, 4, "Z")
            self.setbone(sn, sp, sr, self.f)
            self.body[sn] = (sp, sr)
        shoulder = self.joint(p + "Arm")
        a, b = self.L[s, "upper"], self.L[s, "fore"]
        n = self.name
        axis = Vector((-s, 0, 0))
        target = None
        shoulders = (
            self.joint("mixamorig:LeftArm") + self.joint("mixamorig:RightArm")
        ) / 2
        if n in ("pec_fly", "reverse_fly"):
            target, handdir, _ = self.pec_deck.target(s, d)
            axis = Vector((0, 0, 1))
            pole = shoulder + Vector((s * 0.5, 0.10, -0.12))
        elif n == "incline_press":
            target = Vector(
                (
                    s * (0.20 + 0.18 * d),
                    shoulder.y + 0.08 + 0.13 * d,
                    shoulder.z + 0.58 - 0.43 * d,
                )
            )
            handdir = Vector((0, 0, 1))
            pole = shoulder + Vector((s * 0.5, 0.15, -0.25))
        elif n == "pulldown":
            target = Vector(
                (s * 0.40, shoulders.y + 0.20, shoulders.z + 0.49 - 0.53 * d)
            )
            handdir = Vector((0, 0, 1))
            pole = shoulder + Vector((s * 0.5, 0.02, -0.35))
        elif n in ("rdl", "straight_pulldown"):
            if n == "rdl":
                handdir = Vector((0, 0, -1))
                heights = []
                for sign, other in self.SIDES.items():
                    sh = self.joint("mixamorig:" + other + "Arm")
                    rotation, _ = self.hand_rotation((-sign, 0, 0), handdir)
                    offset = rotation @ self.grip_offsets[sign]
                    dx = sign * 0.27 - offset.x - sh.x
                    dy = 0.25 - offset.y - sh.y
                    reach = self.L[sign, "upper"] + self.L[sign, "fore"] - 0.008
                    heights.append(
                        sh.z - math.sqrt(reach * reach - dx * dx - dy * dy) + offset.z
                    )
                target = Vector((s * 0.27, 0.25, max(heights)))
            else:
                angle = 1.82 - 1.42 * d
                reach = (
                    min(self.L[k, "upper"] + self.L[k, "fore"] for k in self.SIDES)
                    * 0.96
                    + 0.06
                )
                handdir = Vector((0, math.sin(angle), -math.cos(angle)))
                target = shoulders + handdir * reach
                target.x = s * 0.22
            pole = shoulder + Vector((s * 0.25, 0.45, -0.25))
        elif n == "cable_crunch":
            head = self.body["mixamorig:Head"][0]
            target = head + self.R @ Vector((s * 0.22, 0.32, 0.08))
            # Neutral rope grip: shaft/thumb side up, palms facing each other.
            # Pointing the hand up around a forward shaft inverted the grip
            # and forced the forearms to compensate by almost half a turn.
            handdir = self.R @ Vector((0, 1, 0))
            axis = self.R @ Vector((0, 0, 1))
            pole = shoulder + self.R @ Vector((s * 0.15, 0.22, -0.32))
        elif n in ("leg_press", "leg_curl", "leg_extension"):
            target = Vector(
                (
                    s * 0.32,
                    -0.05 if n == "leg_press" else 0.14,
                    0.60 if n == "leg_press" else 0.65,
                )
            )
            handdir = Vector((0, 0, -1))
            axis = Vector((0, 1, 0))
            pole = shoulder + Vector((s * 0.25, -0.3, -0.25))
        elif n == "calf_raise":
            target = shoulder + Vector((s * 0.03, 0.28, -0.28))
            handdir = Vector((0, 0, 1))
            axis = Vector((0, 1, 0))
            pole = shoulder + Vector((s * 0.3, 0.10, -0.32))
        else:
            if n == "curl":
                u = unit((s * 0.12, 0.65, -1))
                angle = 0.65 + 1.55 * d
                v = unit((0, math.sin(angle), -math.cos(angle)))
                axis = Vector((s, 0, 0))
            elif n == "pushdown":
                u = unit((s * 0.08, 0.42, -1))
                angle = 1.48 - 1.08 * d
                v = unit((0, math.sin(angle), -math.cos(angle)))
            elif n == "lateral_raise":
                angle = 0.32 + 1.19 * d
                u = unit((s * math.sin(angle), 0.07, -math.cos(angle)))
                v = unit((s * math.sin(angle - 0.07), 0.10, -math.cos(angle - 0.07)))
                axis = Vector((0, 1, 0))
            elif n == "shoulder_press":
                angle = -0.15 + 1.30 * d
                u = unit((s * math.cos(angle), 0.07, math.sin(angle)))
                v = unit((-s * 0.04, 0.02, 1))
            elif n == "reverse_crunch":
                drop = (shoulder.z - 0.085) / (a + b)
                u = unit((s * 0.24, 1, -drop))
                v = unit((0, 1, -drop))
                axis = Vector((-s, 0, 0))
            elif n == "dead_bug":
                amount = (
                    math.sin(2 * math.pi * t) ** 2
                    if ((t < 0.5 and s == -1) or (t >= 0.5 and s == 1))
                    else 0
                )
                u = unit((s * 0.05, -math.sin(1.32 * amount), math.cos(1.32 * amount)))
                v = unit((0, -math.sin(1.35 * amount), math.cos(1.35 * amount)))
                axis = Vector((s, 0, 0))
            else:
                raise ValueError(n)
            elbow = shoulder + u * a
            wrist = elbow + v * b
            handR, basis = self.hand_rotation(axis, v)
            target = wrist + handR @ self.grip_offsets[s]
        if n in (
            "pec_fly",
            "reverse_fly",
            "incline_press",
            "pulldown",
            "cable_crunch",
            "leg_press",
            "leg_curl",
            "leg_extension",
            "calf_raise",
            "rdl",
            "straight_pulldown",
        ):
            handR, basis = self.hand_rotation(axis, handdir)
            wrist = target - handR @ self.grip_offsets[s]
            elbow = self.ik(shoulder, wrist, a, b, pole)
            if n == "cable_crunch":
                # A rope permits the handle to tilt. Keep the anatomical hand
                # axis in line with the forearm instead of fixing the wrist to
                # a torso/world angle. Re-solve because the grip offset moves
                # the wrist when the hand rotates; the fist target stays fixed.
                for _ in range(16):
                    forward = (
                        handR @ (self.tail[p + "Hand"] - self.head[p + "Hand"])
                    ).normalized()
                    forearm = (wrist - elbow).normalized()
                    if forward.dot(forearm) > 1 - 1e-8:
                        break
                    align = forward.rotation_difference(forearm).to_matrix().to_4x4()
                    handR = align @ handR
                    basis = align @ basis
                    wrist = target - handR @ self.grip_offsets[s]
                    elbow = self.ik(shoulder, wrist, a, b, pole)
        self.apply_arm(s, shoulder, elbow, wrist, handR, basis, target)

    def apply_arm(self, s, shoulder, elbow, wrist, handR, basis, target):
        """Shared length-preserving FK, twist distribution and actual grip binding."""
        side = self.SIDES[s]
        p = "mixamorig:" + side
        a, b = self.L[s, "upper"], self.L[s, "fore"]
        rotations = arm_rotations(
            self.tail[p + "Arm"] - self.head[p + "Arm"],
            self.tail[p + "ForeArm"] - self.head[p + "ForeArm"],
            elbow - shoulder,
            wrist - elbow,
            self.body[p + "Shoulder"][1],
        )
        for (part, aa), R in zip([("Arm", shoulder), ("ForeArm", elbow)], rotations):
            self.setbone(p + part, aa, R, self.f)
        if self.open:
            # An unloaded open palm follows the forearm; imposing a world-fixed
            # grip frame made the dead-bug wrist cross a 180-degree twist branch.
            handR = rotations[1]
            target = wrist + handR @ self.grip_offsets[s]
        self.setbone(p + "Hand", wrist, handR, self.f)
        pose_forearm_twist(self.rig, side, self.f)
        self.pose_fingers(
            self.rig,
            self.hand_chains,
            self.hand_centers,
            side,
            self.f,
            closed=not self.open,
        )
        actual = (
            self.rig.matrix_world
            @ self.rig.pose.bones[p + "Hand"].matrix
            @ self.rest[p + "Hand"].inverted()
            @ (self.head[p + "Hand"] + self.grip_offsets[s])
        )
        if not self.open:
            self.contact_errors.append((actual - target).length)
        self.length_errors.extend(
            [abs((elbow - shoulder).length - a), abs((wrist - elbow).length - b)]
        )
        self.pose_data[side].update(
            shoulder=shoulder, elbow=elbow, wrist=wrist, grip=target
        )
        if not self.open:
            grip = self.grips[s]
            grip.matrix_world = basis
            grip.location = target
            grip.keyframe_insert("location", frame=self.f)
            grip.rotation_mode = "QUATERNION"
            grip.keyframe_insert("rotation_quaternion", frame=self.f)

    def grip_end(self, s, sign=1):
        """Attach hardware outside the palm, along the actual shaft axis."""
        return self.pose_data[self.SIDES[s]]["grip"] + self.grips[
            s
        ].matrix_world.to_3x3() @ Vector((sign * 0.09, 0, 0))

    def move_equipment(self, d):
        n = self.name
        if self.open:
            return
        left, right = self.pose_data["Left"], self.pose_data["Right"]
        center = (left["grip"] + right["grip"]) / 2
        if n in ("pulldown", "straight_pulldown"):
            extra = 0.12 if n != "pulldown" else 0.22
            self.rod(
                "Cable bar",
                left["grip"] - Vector((extra, 0, 0)),
                right["grip"] + Vector((extra, 0, 0)),
                0.014,
            )
            self.rod("Tension cable", center, self.anchor, 0.004, self.DARK)
        if n in ("cable_crunch", "pushdown"):
            split = (
                center + Vector((0, 0.20, 0.32))
                if n == "pushdown"
                else self.body["mixamorig:Head"][0] + self.R @ Vector((0, 0.38, 0.44))
            )
            for s, side in self.SIDES.items():
                self.rod(
                    "Rope " + side,
                    self.grip_end(
                        s,
                        1
                        if (split - self.pose_data[side]["grip"]).dot(
                            self.grips[s].matrix_world.to_3x3().col[0]
                        )
                        > 0
                        else -1,
                    ),
                    split,
                    0.012,
                    self.DARK,
                )
            self.rod("Tension cable", split, self.anchor, 0.004, self.DARK)
        if n in ("pec_fly", "reverse_fly"):
            self.pec_deck.animate(d)
        if n in ("leg_curl", "leg_extension"):
            for s, side in self.SIDES.items():
                self.rod(
                    "Seat handle " + side,
                    self.grip_end(s, -1),
                    (s * 0.32, -0.10, 0.53),
                    0.018,
                )
                p = self.pose_data[side]
                ankle, knee = p["ankle"], p["knee"]
                offset = p["footR"] @ Vector(
                    (0, -0.17 if n == "leg_curl" else 0.17, 0.12)
                )
                roller = ankle + offset
                self.rod(
                    "Shin roller " + side,
                    roller + Vector((-0.12, 0, 0)),
                    roller + Vector((0.12, 0, 0)),
                    0.065,
                    self.PAD,
                )
                self.rod(
                    "Knee lever " + side,
                    knee + Vector((s * 0.20, 0, 0)),
                    roller + Vector((s * 0.20, 0, 0)),
                    0.025,
                    self.DARK,
                )
        if n == "leg_press":
            footR = left["footR"]
            ankle = (left["ankle"] + right["ankle"]) / 2
            plate = self.items["Sled footplate"]
            plate.location = ankle + footR @ Vector((0, 0.06, -self.ankle_z - 0.035))
            plate.keyframe_insert("location", frame=self.f)
            track_z = plate.location.z - plate.location.y - 0.07
            for sign in (-1, 1):
                point = Vector((sign * 0.56, plate.location.y, plate.location.z - 0.07))
                self.rod(
                    "Sled guide " + str(sign),
                    (sign * 0.56, 0.24, 0.24 + track_z),
                    (sign * 0.56, 1.30, 1.30 + track_z),
                    0.035,
                )
                support = self.items["Sled upright " + str(sign)]
                support.dimensions.z = 1.30 + track_z
                support.location.z = support.dimensions.z / 2
                support.keyframe_insert("location", frame=self.f)
                support.keyframe_insert("scale", frame=self.f)
                delta = unit((0, 1, 1)) * 0.09
                self.rod(
                    "Sled carriage " + str(sign),
                    point - delta,
                    point + delta,
                    0.055,
                    self.DARK,
                )
                self.rod(
                    "Sled connector " + str(sign),
                    point,
                    plate.location + Vector((sign * 0.38, 0.07, 0.07)),
                    0.035,
                    self.DARK,
                )
            for s, side in self.SIDES.items():
                self.rod(
                    "Seat handle " + side,
                    self.grip_end(s, -1),
                    (s * 0.32, -0.10, 0.45),
                    0.018,
                )
        if n == "calf_raise":
            shoulder = (left["shoulder"] + right["shoulder"]) / 2
            self.carriage.location = shoulder + Vector((0, -0.015, 0.11))
            self.carriage.keyframe_insert("location", frame=self.f)
            for s, side in self.SIDES.items():
                corner = self.grip_end(s) + Vector((s * 0.10, 0.06, 0.15))
                self.rod(
                    "Calf handle " + side,
                    self.grip_end(s),
                    corner,
                    0.018,
                )
                self.rod(
                    "Calf handle mount " + side,
                    corner,
                    self.carriage.location + Vector((s * 0.26, 0.18, 0)),
                    0.018,
                )
        if n == "rdl":
            self.bar.location = center
            self.bar.rotation_mode = "QUATERNION"
            self.bar.rotation_quaternion = Vector((1, 0, 0)).rotation_difference(
                right["grip"] - left["grip"]
            )
            self.bar.keyframe_insert("location", frame=self.f)
            self.bar.keyframe_insert("rotation_quaternion", frame=self.f)

    def pose(self, f):
        self.f = f
        t = (f - 1) / self.frames
        d = 0.5 - 0.5 * math.cos(2 * math.pi * t)
        self.torso(d)
        for s in self.SIDES:
            self.leg(s, d, t)
            self.arm(s, d, t)
        self.move_equipment(d)
        record = {
            "frame": f,
            "hips": list(self.hip),
            "depth": d,
            "contact_error": max(self.contact_errors[-2:], default=0),
            "joints": {},
        }
        for side, points in self.pose_data.items():
            record["joints"][side] = {
                k: list(v) for k, v in points.items() if isinstance(v, Vector)
            }
        self.pose_records.append(record)

    def finish(self):
        """Compress only the underside against the mat after skeletal deformation.

        The stylized scapular volume needs a local contact corrective when supine.
        It is not a substitute for motion solves: hips/spine keep their baked pose.
        """
        if not self.floor:
            return
        group = bpy.data.node_groups.new("Mat surface contact", "GeometryNodeTree")
        group.interface.new_socket(
            name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry"
        )
        group.interface.new_socket(
            name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry"
        )
        nodes = group.nodes
        links = group.links
        inp = nodes.new("NodeGroupInput")
        out = nodes.new("NodeGroupOutput")
        position = nodes.new("GeometryNodeInputPosition")
        split = nodes.new("ShaderNodeSeparateXYZ")
        combine = nodes.new("ShaderNodeCombineXYZ")
        maximum = nodes.new("ShaderNodeMath")
        maximum.operation = "MAXIMUM"
        plane = (self.character.matrix_world.inverted() @ Vector((0, 0, 0.028))).z
        maximum.inputs[1].default_value = plane
        setter = nodes.new("GeometryNodeSetPosition")
        links.new(position.outputs["Position"], split.inputs[0])
        for axis in ["X", "Y"]:
            links.new(split.outputs[axis], combine.inputs[axis])
        links.new(split.outputs["Z"], maximum.inputs[0])
        links.new(maximum.outputs[0], combine.inputs["Z"])
        links.new(combine.outputs[0], setter.inputs["Position"])
        links.new(inp.outputs["Geometry"], setter.inputs["Geometry"])
        links.new(setter.outputs[0], out.inputs["Geometry"])
        modifier = self.character.modifiers.new("Mat contact compression", "NODES")
        modifier.node_group = group
        bpy.context.scene[
            "floor_contact_corrective"
        ] = "Post-skin underside compression to mat top at 0.028 m; supine motions only"

    def camera(self):
        n = self.name
        if self.floor:
            return (3.4, 3.0, 3.7), (0, 0.15, 0.30), 3.15, 1.45, 0.15
        if n == "leg_press":
            return (3.7, 3.5, 2.8), (0, 0.50, 0.75), 3.55, 1.55, 0.35
        if n == "incline_press":
            return (3.6, 4.6, 3.0), (0, -0.10, 0.85), 3.05, 1.22, 0
        if n in ("pulldown", "straight_pulldown", "reverse_fly"):
            return (3.6, -4.8, 2.9), (0, 0.35, 1.03), 3.35, 1.35, 0.25
        if n in ("pushdown", "cable_crunch"):
            return (4.4, 3.6, 2.6), (0, 0.30, 0.98), 3.30, 1.32, 0.25
        if n in ("leg_curl", "leg_extension"):
            return (3.8, 4.0, 2.4), (0, 0.25, 0.85), 3.05, 1.26, 0.20
        return (3.7, 5.0, 2.7), (0, 0, 1.02), 3.12, 1.20, 0
