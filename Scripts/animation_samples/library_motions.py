"""Explicit motion adapters for library batches, using the calibrated athlete."""
import math
from functools import partial
from mathutils import Vector, Matrix
from plan_motions import PlanMotion, unit
from library_exercises import LIBRARY_EXERCISES


class LibraryMotion(PlanMotion):
    def __init__(self, env):
        super().__init__(env, LIBRARY_EXERCISES[env["args"].exercise])
        if self.name in ("reverse_curl", "single_reverse_curl") and self.args.sex == "male":
            self.pose_fingers = partial(self.pose_fingers, thumb_clearance=0.008)

    def equipment(self):
        self.f = 1
        for sign, side in self.SIDES.items():
            if self.config.get("unilateral") and side != self.config["unilateral"]:
                continue
            grip = self.empty("Grip." + side)
            self.grips[sign] = grip
            self.cylinder("Grip shaft " + side, (-0.09, 0, 0), (0.09, 0, 0),
                          0.014, self.STEEL, grip)
            for end in (-1, 1):
                self.cylinder("Dumbbell plate " + side, (end * 0.10, 0, 0),
                              (end * 0.16, 0, 0), 0.075, self.DARK, grip)
        if self.config.get("press_type") == "flat":
            self.block("Bench pad", (0, -0.47, 0.49), (0.34, 1.60, 0.10), True)
            for y in (-1.05, 0.15):
                self.block("Bench leg " + str(y), (0, y, 0.24), (0.16, 0.18, 0.48))
                self.block("Bench foot " + str(y), (0, y, 0.04), (0.64, 0.32, 0.08))
            if self.config.get("unilateral"):
                self.block("Bench longitudinal frame", (0, -.45, .38), (.09, 1.30, .10))
        elif self.seated:
            self.block("Seat cushion", (0, 0.08, 0.49), (0.34, 0.40, 0.10), True)
            self.block("Seat pedestal", (0, 0.08, 0.24), (0.12, 0.16, 0.48))
            self.block("Seat base", (0, 0.08, 0.04), (0.65, 0.75, 0.08))
            if self.config["family"] == "press" or self.config.get("back_support"):
                angle = self.config["torso_angle"]
                origin = Vector((0, 0.05, 0.605))
                center = origin + self.rx(angle) @ Vector((0, -0.09, 0.35))
                self.block("Back support", center, (0.28 if self.config.get("back_support") else 0.33, 0.10, 0.90), True, angle)
                self.rod("Back frame", origin, center + self.rx(angle) @ Vector((0, 0, 0.38)), 0.035)

    def arm(self, s, d, t):
        config = self.config
        if config.get("alternating"):
            active = (t < 0.5 and s == -1) or (t >= 0.5 and s == 1)
            d = math.sin(2 * math.pi * t) ** 2 if active else 0
        side = self.SIDES[s]
        if config.get("unilateral") and side != config["unilateral"]:
            shoulder = self.joint("mixamorig:" + side + "Arm")
            if config.get("press_type") == "flat":
                u, v = unit((s*.45, .90, -.15)), unit((s*.25, .95, .05))
            else:
                u, v = unit((s*.32, .10, -1)), unit((s*.18, .08, -1))
            elbow = shoulder + u*self.L[s, "upper"]
            wrist = elbow + v*self.L[s, "fore"]
            handR, basis = self.hand_rotation(Vector((0, 1, 0)), v)
            self.open = True
            try:
                self.apply_arm(s, shoulder, elbow, wrist, handR, basis, wrist)
            finally:
                self.open = False
            return
        if config["family"] == "shrug" or (config["family"] == "press" and config["press_type"] in ("seated", "standing")):
            sn = "mixamorig:" + side + "Shoulder"
            sp, sr = self.body[sn]
            sr = sr @ Matrix.Rotation(-s * (0.42 if config["family"] == "shrug" else 0.40) * d, 4, "Y")
            self.setbone(sn, sp, sr, self.f)
            self.body[sn] = (sp, sr)
        shoulder = self.joint("mixamorig:" + side + "Arm")
        a, b = self.L[s, "upper"], self.L[s, "fore"]
        if config["family"] == "press":
            overhead = config["press_type"] in ("seated", "standing")
            angle = (-0.15 + 1.55 * d) if overhead else (-0.10 + 1.55 * d)
            tuck = 0.65 if config["grip"] == "neutral" else 0.88
            spread = 0.12*d if (config["press_type"] == "standing" and self.args.sex == "male") or (config["press_type"] == "flat" and config["grip"] == "neutral" and self.args.sex == "female") else 0
            u = unit((s * (tuck * math.cos(angle) + spread), math.sqrt(1-tuck*tuck) * math.cos(angle), math.sin(angle)))
            v = unit((-s * 0.02, 0.035, 1))
            axis = Vector((0, -1, 0)) if config["grip"] == "neutral" else Vector((-s, 0, 0))
        elif config["family"] in ("curl", "zottman"):
            turn = 0
            if config["family"] == "zottman":
                smooth = lambda x: 0.5 - 0.5 * math.cos(math.pi * min(1, max(0, x)))
                if t <= 0.375:
                    d = smooth(t / 0.375)
                elif t <= 0.5:
                    d, turn = 1, math.pi * smooth((t - 0.375) / 0.125)
                elif t <= 0.875:
                    d, turn = 1 - smooth((t - 0.5) / 0.375), math.pi
                else:
                    d, turn = 0, math.pi * (1 - smooth((t - 0.875) / 0.125))
            # A transverse (supinated) dumbbell needs anterior clearance;
            # a longitudinal hammer grip hangs beside the thigh instead.
            u = unit((s * (0.30 if self.seated else 0.22),
                      0.65 if config["grip"] != "neutral" else 0.20, -1))
            angle = (0.65 + 1.55 * d) if config["grip"] != "neutral" else (0.30 + 1.90 * d)
            v = unit((s * (0.32 if self.args.sex == "female" else 0.27), math.sin(angle), -math.cos(angle)))
            if self.seated and config["grip"] == "supinated":
                u = unit((s * 0.45, 0.35, -1))
                v = unit((s * (0.32 + 0.33 * (1-d)), math.sin(angle), -math.cos(angle)))
            if config.get("back_support"):
                u = unit((s * 0.25, 0.04, -1))
                angle = 0.18 + 2.02 * d
                spread = 0.28 + (0.55 * math.sin(math.pi*d) if config["grip"] == "supinated" else 0)
                v = unit((s * spread, math.sin(angle), -math.cos(angle)))
            axis = Vector((0, math.cos(angle), math.sin(angle))) if config["grip"] == "neutral" else Vector((s, 0, 0))
            if config["grip"] == "pronated":
                axis = -axis
            if config["family"] == "zottman":
                axis = Matrix.Rotation(-s * turn, 4, v) @ axis
        elif config["family"] == "cross_curl":
            u = unit((s * (0.30 if self.args.sex == "female" else 0.12), 0.90 if self.args.sex == "female" else 0.65, -1))
            v = unit((s * (0.50 * (1-d) - 1.80*d), 0.45 + 0.15*d,
                      -1 + (1.80 if self.args.sex == "female" else 2.1)*d))
            # The thumb end follows the curl plane while the fist crosses the chest.
            palm = unit((-s * (1-.4*d), -.95*d, 0))
            axis = s * v.cross(palm)
        elif config["family"] == "shrug":
            u = v = unit((s * 0.25, 0.06, -1))
            axis = Vector((0, 1, 0))
        elif config["family"] == "bent_row":
            u = unit((s * (0.45 if self.args.sex == "female" else 0.30), -0.90*d, -1 + 0.95*d))
            v = unit((s * (0.22 if self.args.sex == "female" else 0.08), 0.12, -1))
            axis = Vector((0, 1, 0))
        elif config["family"] == "raise":
            angle = 0.48 + 1.07 * d
            u = unit((s * (0.25 if self.args.sex == "female" else 0.13), math.sin(angle), -math.cos(angle)))
            v = unit((s * 0.06, math.sin(angle + 0.06), -math.cos(angle + 0.06)))
            if self.seated:
                # Seated thighs occupy the standing front-raise return path.
                # Let the hands return beside them, then converge gradually
                # into the forward lifting plane as they clear the legs.
                spread = 0.65 if config["grip"] == "pronated" else 0.45
                u = unit((s * (0.25 + spread * (1-d)), math.sin(angle), -math.cos(angle)))
                v = unit((s * (0.06 + spread * 0.75 * (1-d)), math.sin(angle + 0.06), -math.cos(angle + 0.06)))
            # Slight external rotation near shoulder height; no overhead reach.
            axis = Vector((-s, 0, 0.15 * d))
            if config["grip"] == "neutral":
                axis = Vector((0, math.cos(angle), math.sin(angle)))
        elif config["family"] in ("lateral_raise", "scaption", "lateral_front"):
            azimuth = math.pi / 6 if config["family"] == "scaption" else 0
            base = 0.38
            if config["family"] == "scaption" and self.args.sex == "female":
                base = 0.46
            if config["family"] == "lateral_front":
                # Two distinct repetitions: lateral up/down, then front up/down.
                # Change the lifting plane only near the lowered position.
                d = math.sin(2 * math.pi * t) ** 2
                blend = min(1, max(0, (t - 0.375) / 0.125)) if t < 0.5 else 1 - min(1, max(0, (t - 0.875) / 0.125))
                azimuth = math.pi / 2 * (0.5 - 0.5 * math.cos(math.pi * blend))
                base = 0.48
            angle = base + (1.52 - base) * d
            h = Vector((s * math.cos(azimuth), math.sin(azimuth), 0))
            spread = 0.25 if self.args.sex == "female" and config["family"] == "lateral_front" else 0.10
            u = unit(h * math.sin(angle) + Vector((s * spread, 0.08, -math.cos(angle))))
            v = unit(h * math.sin(angle - 0.04) + Vector((s * 0.06, 0.08, -math.cos(angle - 0.04))))
            axis = Vector((-s * math.sin(azimuth), math.cos(azimuth), 0))
            if config["grip"] == "thumbs_up":
                axis = h * math.cos(angle - 0.04) + Vector((0, 0, math.sin(angle - 0.04)))
        else:
            raise ValueError("No motion adapter for " + self.name)
        elbow = shoulder + u * a
        wrist = elbow + v * b
        handR, basis = self.hand_rotation(axis, v)
        # The calibrated hand's rest axis is not the world vertical axis.
        # Align the actual metacarpal direction with the forearm, carrying the
        # entire grip frame so the shaft and finger contact remain consistent.
        p = "mixamorig:" + side + "Hand"
        forward = (handR @ (self.tail[p] - self.head[p])).normalized()
        align = forward.rotation_difference(v).to_matrix().to_4x4()
        handR, basis = align @ handR, align @ basis
        target = wrist + handR @ self.grip_offsets[s]
        self.apply_arm(s, shoulder, elbow, wrist, handR, basis, target)

    def move_equipment(self, d):
        # Both dumbbells are parented to their independently solved grip frames.
        pass
