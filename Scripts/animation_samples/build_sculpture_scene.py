"""Animate the selected skinned sculptures with original two-bone motion solves.

Local Blender only. Keeps source character assets intact; writes v2 samples.
"""
import argparse, json, math, sys, hashlib
from pathlib import Path
import bpy
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from exercise_catalog import EXERCISES, PRIMARY_MUSCLES
from plan_exercises import PLAN_EXERCISES, PLAN_MUSCLES
from plan_motions import PlanMotion
from library_exercises import LIBRARY_EXERCISES, LIBRARY_MUSCLES
from library_motions import LibraryMotion
from library_motions_v6 import LibraryMotionV6
from library_motions_v7 import LibraryMotionV7
from frame_plan_scene import fit as fit_plan_camera

ALL_EXERCISES = {**EXERCISES, **PLAN_EXERCISES, **LIBRARY_EXERCISES}

P = argparse.ArgumentParser()
P.add_argument("--exercise", choices=list(ALL_EXERCISES), required=True)
P.add_argument("--sex", choices=["male", "female"], default="male")
P.add_argument("--preview", action="store_true")
P.add_argument("--no-render", action="store_true")
P.add_argument("--frame", type=int, default=61)
P.add_argument(
    "--output-root",
    type=Path,
    default=ROOT,
    help="Isolated candidate output; source assets still come from the project",
)
P.add_argument("--view", choices=["motion", "front", "back"], default="motion")
args = P.parse_args(sys.argv[sys.argv.index("--") + 1 :])
if args.view == 'motion' and args.exercise in LIBRARY_EXERCISES:
    from motion_reference_gate import load_reference
    load_reference(args.exercise)
collection = (
    "animation-library" if args.exercise in LIBRARY_EXERCISES else
    "animation-plan-v3" if args.exercise in PLAN_EXERCISES else "animation-samples-v2"
)
frame_count = ALL_EXERCISES[args.exercise].get("frames", 120)
OUT = args.output_root / f"build/{collection}/{args.sex}/{args.exercise}"
OUT.mkdir(parents=True, exist_ok=True)
DELIVER = args.output_root / f"docs/{collection}/{args.sex}"
DELIVER.mkdir(parents=True, exist_ok=True)
import bmesh

sys.path.insert(0, str(ROOT / "Scripts/character_assets"))
from prepare_athlete import prepare_character
from hand_rig import pose_fingers, add_contact_clearance
from shoulder_rig import squat_bar_anchor
from deformation_rig import arm_rotations, pose_forearm_twist, VERSION as RIG_VERSION

(
    rig,
    character,
    hand_centers,
    hand_chains,
    shoulder_report,
    ankle_report,
    scale,
) = prepare_character(args.sex)
rest = {b.name: rig.matrix_world @ b.matrix_local for b in rig.data.bones}
head = {b.name: (rig.matrix_world @ b.head_local) for b in rig.data.bones}
tail = {b.name: (rig.matrix_world @ b.tail_local) for b in rig.data.bones}
inv = rig.matrix_world.inverted()
hip0 = head["mixamorig:Hips"]
keys = [
    "pectoralis_major",
    "deltoid_anterior",
    "deltoid_lateral",
    "deltoid_posterior",
    "biceps_brachii",
    "triceps_brachii",
    "forearm_flexors",
    "forearm_extensors",
    "rectus_abdominis",
    "external_oblique",
    "trapezius",
    "latissimus_dorsi",
    "gluteus_maximus",
    "quadriceps",
    "hamstrings",
    "gastrocnemius",
    "tibialis_anterior",
]
active = {**PRIMARY_MUSCLES, **PLAN_MUSCLES, **LIBRARY_MUSCLES}[args.exercise]
for k in keys:
    rig[k] = float(k in active)
rig.update_tag()
bpy.context.view_layer.update()


def material(name, color, metal=0, rough=0.45):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    m.node_tree.nodes.clear()
    p = m.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    output = m.node_tree.nodes.new("ShaderNodeOutputMaterial")
    m.node_tree.links.new(p.outputs[0], output.inputs[0])
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Metallic"].default_value = metal
    p.inputs["Roughness"].default_value = rough
    return m


STEEL = material("Brushed steel", (0.43, 0.48, 0.47), 0.8, 0.28)
DARK = material("Graphite steel", (0.045, 0.064, 0.058), 0.4)
PAD = material("Bench upholstery", (0.10, 0.15, 0.125), 0, 0.8)
ACCENT = material("Copper collar", (0.53, 0.21, 0.08), 0.65)
BASE = material("Stone stage", (0.72, 0.73, 0.69), 0, 0.95)


def finish(o, name, mat, parent=None):
    o.name = name
    o.data.materials.append(mat)
    if parent:
        o.parent = parent
    return o


def cube(name, loc, size, mat, bevel=0.02, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = finish(bpy.context.object, name, mat, parent)
    o.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        m = o.modifiers.new("Soft edges", "BEVEL")
        m.width = bevel
        m.segments = 3
        o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    return o


def cylinder(name, a, b, r, mat, parent=None):
    a, b = Vector(a), Vector(b)
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=40, radius=r, depth=(b - a).length, location=(a + b) / 2
    )
    o = finish(bpy.context.object, name, mat, parent)
    o.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
    return o


def empty(name):
    o = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(o)
    return o


def rx(angle):
    return Matrix.Rotation(angle, 4, "X")


def frame(direction, normal):
    y = Vector(direction).normalized()
    x = Vector(normal)
    x = (x - y * x.dot(y)).normalized()
    z = x.cross(y).normalized()
    return Matrix((x, y, z)).transposed().to_4x4()


def setbone(name, pos, rotation, frame_number):
    m = rotation @ rest[name]
    m.translation = pos
    b = rig.pose.bones[name]
    b.matrix = inv @ m
    bpy.context.view_layer.update()
    b.rotation_mode = "QUATERNION"
    b.keyframe_insert("location", frame=frame_number)
    b.keyframe_insert("rotation_quaternion", frame=frame_number)


def orient(name, a, b, normal, f):
    rd = tail[name] - head[name]
    R = frame(Vector(b) - Vector(a), normal) @ frame(rd, (1, 0, 0)).inverted()
    setbone(name, Vector(a), R, f)


def ik(a, b, l1, l2, pole):
    a, b, pole = Vector(a), Vector(b), Vector(pole)
    delta = b - a
    d = delta.length
    if d > l1 + l2 - 0.0002 or d < abs(l1 - l2) + 0.0002:
        raise ValueError(f"Unreachable {args.exercise} {d:.4f} / {l1+l2:.4f}")
    axis = delta / d
    along = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    height = math.sqrt(max(0, l1 * l1 - along * along))
    bend = pole - a
    bend = (bend - axis * bend.dot(axis)).normalized()
    return a + axis * along + bend * height


def depth(f):
    t = (f - 1) / 120
    if t < 0.06 or t > 0.94:
        return 0
    if t < 0.46:
        return 0.5 - 0.5 * math.cos(math.pi * (t - 0.06) / 0.4)
    if t < 0.54:
        return 1
    return 0.5 + 0.5 * math.cos(math.pi * (t - 0.54) / 0.4)


# Native, original equipment; all bar/handle contact points are animated.
BAR = empty("Barbell")
HANDLE = empty("Cable handle")
CABLE = None
if args.view == "motion":
    if args.exercise in ["squat", "bench"]:
        cylinder("Bar shaft", (-0.94, 0, 0), (0.94, 0, 0), 0.014, STEEL, BAR)
        for s in [-1, 1]:
            cylinder("Sleeve", (s * 0.59, 0, 0), (s * 0.94, 0, 0), 0.024, STEEL, BAR)
            for x, r, w in [(0.72, 0.15, 0.055), (0.79, 0.12, 0.045)]:
                cylinder(
                    "Weight plate",
                    (s * (x - w / 2), 0, 0),
                    (s * (x + w / 2), 0, 0),
                    r,
                    DARK,
                    BAR,
                )
            cylinder("Collar", (s * 0.84, 0, 0), (s * 0.87, 0, 0), 0.033, ACCENT, BAR)
    if args.exercise == "bench":
        cube("Bench pad", (0, -0.18, 0.405), (0.30, 1.32, 0.11), PAD, 0.045)
        for y in [-0.65, 0.30]:
            cube("Bench leg", (0, y, 0.21), (0.075, 0.09, 0.35), DARK)
            cube("Bench foot", (0, y, 0.035), (0.55, 0.13, 0.07), DARK)
    if args.exercise == "row":
        for s in [-1, 1]:
            cylinder(
                "Handle grip",
                (s * 0.085, 0, -0.065),
                (s * 0.085, 0, 0.10),
                0.014,
                STEEL,
                HANDLE,
            )
            cylinder(
                "V handle", (s * 0.085, 0, 0.10), (0, 0.09, 0.10), 0.013, STEEL, HANDLE
            )
        CABLE = cylinder("Cable", (0, 0, 0), (0, 0, 1), 0.004, DARK)
        cube("Seat", (0, -0.10, 0.42), (0.43, 0.43, 0.10), PAD, 0.04)
        for y in [-0.24, 0.04]:
            cube("Seat support", (0, y, 0.21), (0.32, 0.07, 0.40), DARK)
        cube("Machine rail", (0, 0.65, 0.045), (0.54, 1.95, 0.09), DARK)
        cube("Pulley tower", (0, 1.55, 0.62), (0.38, 0.25, 1.14), DARK)
        for i in range(8):
            cube(
                "Weight stack",
                (0, 1.39, 0.14 + i * 0.055),
                (0.29, 0.18, 0.04),
                STEEL,
                0.005,
            )
        cylinder("Low pulley", (-0.07, 1.36, 0.40), (0.07, 1.36, 0.40), 0.072, STEEL)
        plate = cube("Foot plate", (0, 0.69, 0.18), (0.58, 0.34, 0.04), PAD)
        plate.rotation_euler.x = math.radians(25)
SIDES = {-1: "Left", 1: "Right"}
L = {}
grip_offsets = {}
for s, side in SIDES.items():
    n = lambda part: "mixamorig:" + side + part
    L[s, "thigh"] = (head[n("Leg")] - head[n("UpLeg")]).length
    L[s, "shin"] = (head[n("Foot")] - head[n("Leg")]).length
    L[s, "upper"] = (head[n("ForeArm")] - head[n("Arm")]).length
    L[s, "fore"] = (head[n("Hand")] - head[n("ForeArm")]).length
    # Grip center estimated in rest pose, distal to the calibrated wrist.
    rest_grip = rig.matrix_world @ hand_centers[side]
    grip_offsets[s] = rest_grip - head[n("Hand")]
ankle_z = min(head["mixamorig:" + side + "Foot"].z for side in SIDES.values())
# Solve a relaxed 6-degree knee angle with the actual hip offsets and stance.
# A fixed 32 mm drop previously bent both knees by about 33 degrees in curls.
standing_heights = []
for s, side in SIDES.items():
    delta = head["mixamorig:" + side + "UpLeg"] - hip0
    a, b = L[s, "thigh"], L[s, "shin"]
    reach2 = a*a + b*b + 2*a*b*math.cos(math.radians(6))
    horizontal2 = (delta.x-s*.16)**2 + delta.y**2
    standing_heights.append(ankle_z-delta.z+math.sqrt(reach2-horizontal2))
stand_z = min(standing_heights)
if args.exercise == "rdl":
    # The hip-hinge trajectory needs its own knee-flexion reserve; the quiet
    # standing height cannot reach its forward/backward hip offsets.
    stand_z = min(ankle_z + L[s, "thigh"] + L[s, "shin"] for s in SIDES) - 0.032
# Position the high bar against the actual posterior upper-trap surface.
bar_anchor_local = (
    squat_bar_anchor(character, args.sex, scale) if args.exercise == "squat" else None
)
bar_rest_offset = (
    (rig.matrix_world @ bar_anchor_local - hip0) if bar_anchor_local else None
)
if args.exercise == "squat":
    R0 = rx(-0.20)
    hip_y = 0.035 - (R0 @ bar_rest_offset).y
    heights = []
    for sign, side in SIDES.items():
        delta = R0 @ (head["mixamorig:" + side + "UpLeg"] - hip0)
        horizontal = (delta.x - sign * 0.18) ** 2 + (hip_y + delta.y) ** 2
        reach = L[sign, "thigh"] + L[sign, "shin"] - 0.015
        heights.append(ankle_z - delta.z + math.sqrt(reach * reach - horizontal))
    stand_z = min(heights)
contact_errors = []
length_errors = []
pose_records = []
extension = ((LibraryMotionV7(globals()) if LIBRARY_EXERCISES[args.exercise].get("audit_version") == 7 else LibraryMotionV6(globals()) if LIBRARY_EXERCISES[args.exercise].get("audit_version") == 6 else LibraryMotion(globals())) if args.exercise in LIBRARY_EXERCISES else
             PlanMotion(globals()) if args.exercise in PLAN_EXERCISES else None)


def pose(f):
    bpy.context.scene.frame_set(f)
    if extension and args.view == "motion":
        extension.pose(f)
        return
    d = depth(f)
    static = args.view != "motion"
    if static:
        hip = hip0.copy()
        R = Matrix.Identity(4)
    elif args.exercise == "squat":
        R = rx(-(0.20 + 0.35 * d))
        bar_offset = R @ bar_rest_offset
        hip = Vector((0, 0.035 - bar_offset.y, stand_z - 0.37 * d))
    elif args.exercise == "bench":
        hip = Vector((0, 0.23, 0.57))
        R = rx(math.pi / 2)
    else:
        hip = Vector((0, -0.1, 0.565))
        R = rx(-(0.16 - 0.14 * d))
    # Keep torso, neck and shoulder girdle coherent, with analytic limb solves.
    for name in [
        b.name
        for b in rig.data.bones
        if not any(
            x in b.name for x in ["UpLeg", "Leg", "Foot", "ToeBase", "ForeArm", "Hand"]
        )
        and (not b.name.endswith("Arm"))
    ]:
        if name == "Root":
            continue
        setbone(name, hip + R @ (head[name] - hip0), R, f)
    if not static and args.exercise in ["squat", "bench"]:
        bar = (
            hip + R @ bar_rest_offset
            if args.exercise == "squat"
            else Vector(
                (
                    0,
                    -0.23 + 0.10 * d,
                    (1.065 if args.sex == "male" else 1.025)
                    - (0.34 if args.sex == "male" else 0.295) * d,
                )
            )
        )
        BAR.location = bar
        BAR.keyframe_insert("location", frame=f)
        BAR.rotation_euler.x = -(0.20 + 0.35 * d) if args.exercise == "squat" else 0
        BAR.keyframe_insert("rotation_euler", frame=f)
    elif not static:
        handle = Vector((0, 0.505 - 0.215 * d, 0.94 - 0.085 * d))
        HANDLE.location = handle
        HANDLE.keyframe_insert("location", frame=f)
        a = handle + Vector((0, 0.09, 0.10))
        b = Vector((0, 1.36, 0.40))
        CABLE.location = (a + b) / 2
        CABLE.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
        CABLE.scale.z = (b - a).length
        CABLE.keyframe_insert("location", frame=f)
        CABLE.keyframe_insert("rotation_euler", frame=f)
        CABLE.keyframe_insert("scale", frame=f)
    frame_contacts = []
    for s, side in SIDES.items():
        n = lambda part: "mixamorig:" + side + part
        hj = hip + R @ (head[n("UpLeg")] - hip0)
        shoulder = hip + R @ (head[n("Arm")] - hip0)
        arm_parent = R
        if not static and args.exercise == "row":
            clavicle = hip + R @ (head[n("Shoulder")] - hip0)
            arm_parent = R @ Matrix.Rotation(s * (0.22 * (1 - d) - 0.04 * d), 4, "Z")
            setbone(n("Shoulder"), clavicle, arm_parent, f)
            shoulder = clavicle + arm_parent @ (head[n("Arm")] - head[n("Shoulder")])
        if static:
            for part in ["UpLeg", "Leg", "Foot", "ToeBase", "Arm", "ForeArm", "Hand"]:
                setbone(n(part), head[n(part)], Matrix.Identity(4), f)
            pose_fingers(rig, hand_chains, hand_centers, side, f, closed=False)
            continue
        if args.exercise == "squat":
            ankle = Vector((s * 0.18, 0, ankle_z))
            goal = bar + Vector((s * 0.37, 0, 0))
            hand_dir = R @ Vector((0, -0.30, 0.954))
            epole = bar + R @ Vector((s * 0.48, -0.12, -0.27))
            kpole = Vector((s * 0.27, 1, 0.45))
            footR = Matrix.Rotation(-s * 0.08, 4, "Z")
        elif args.exercise == "bench":
            ankle = Vector((s * 0.27, 0.63, ankle_z))
            goal = bar + Vector((s * 0.39, 0, 0))
            hand_dir = Vector((0, 0, 1))
            epole = Vector((s * 0.53, -0.02, 0.48))
            kpole = Vector((s * 0.29, 0.80, 0.48))
            footR = Matrix.Identity(4)
        else:
            ankle = Vector((s * 0.17, 0.60, 0.275))
            goal = handle + Vector((s * 0.085, 0, 0))
            hand_dir = Vector((0, 1, 0))
            epole = Vector((s * 0.52, -0.42, 0.89))
            kpole = Vector((s * 0.18, 0.25, 1.0))
            footR = rx(math.radians(25))
        knee = ik(hj, ankle, L[s, "thigh"], L[s, "shin"], kpole)
        orient(n("UpLeg"), hj, knee, (1, 0, 0), f)
        orient(n("Leg"), knee, ankle, (1, 0, 0), f)
        setbone(n("Foot"), ankle, footR, f)
        setbone(
            n("ToeBase"),
            ankle + footR @ (head[n("ToeBase")] - head[n("Foot")]),
            footR,
            f,
        )
        # Align the actual hand-local shaft axis (X) with the equipment.
        if args.exercise == "row":
            basis = Matrix(((0, -1, 0), (0, 0, -1), (1, 0, 0))).to_4x4()
        else:
            basis = Matrix(((-s, 0, 0), (0, s, 0), (0, 0, -1))).to_4x4()
            if args.exercise == "squat":
                basis = R @ basis
        handR = basis @ rig.matrix_world.to_quaternion().to_matrix().to_4x4().inverted()
        wrist = goal - handR @ grip_offsets[s]
        elbow = ik(shoulder, wrist, L[s, "upper"], L[s, "fore"], epole)
        rotations = arm_rotations(
            tail[n("Arm")] - head[n("Arm")],
            tail[n("ForeArm")] - head[n("ForeArm")],
            elbow - shoulder,
            wrist - elbow,
            arm_parent,
        )
        for (part, a), delta in zip([("Arm", shoulder), ("ForeArm", elbow)], rotations):
            setbone(n(part), a, delta, f)
        setbone(n("Hand"), wrist, handR, f)
        pose_forearm_twist(rig, side, f)
        pose_fingers(rig, hand_chains, hand_centers, side, f)
        actual_matrix = rig.matrix_world @ rig.pose.bones[n("Hand")].matrix
        actual_grip = (
            actual_matrix
            @ rest[n("Hand")].inverted()
            @ (head[n("Hand")] + grip_offsets[s])
        )
        frame_contacts.append((actual_grip - goal).length)
        for a, b, length in [
            (hj, knee, L[s, "thigh"]),
            (knee, ankle, L[s, "shin"]),
            (shoulder, elbow, L[s, "upper"]),
            (elbow, wrist, L[s, "fore"]),
        ]:
            length_errors.append(abs((b - a).length - length))
        contact_errors.extend(frame_contacts)
    pose_records.append(
        {
            "frame": f,
            "hips": list(hip),
            "depth": d,
            "contact_error": max(frame_contacts, default=0),
        }
    )


for f in range(1, frame_count + 2) if args.view == "motion" else [1, frame_count + 1]:
    pose(f)
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = frame_count
scene.render.fps = 24
# Linear baked transforms avoid interpolation overshoot between solved poses.
for action in bpy.data.actions:
    for layer in action.layers:
        for strip in layer.strips:
            for slot in action.slots:
                try:
                    bag = strip.channelbag(slot)
                except (RuntimeError, TypeError):
                    continue
                if bag:
                    for curve in bag.fcurves:
                        for point in curve.keyframe_points:
                            point.interpolation = "LINEAR"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 960 if args.view == "motion" else 360
scene.render.resolution_y = 800 if args.view == "motion" else 540
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.film_transparent = True
scene.world = bpy.data.worlds.new("Soft studio")
scene.world.use_nodes = True
bg = next(n for n in scene.world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs[0].default_value = (0.78, 0.80, 0.74, 1)
bg.inputs[1].default_value = 0.35
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
for name, pos, power, size in [
    ("Key", (3, 4, 6), 500, 5),
    ("Fill", (-3, 2, 3), 300, 4),
    ("Rim", (1, -4, 5), 500, 3),
]:
    l = bpy.data.lights.new(name, "AREA")
    l.energy = power
    l.shape = "DISK"
    l.size = size
    o = bpy.data.objects.new(name, l)
    scene.collection.objects.link(o)
    o.location = pos
    o.rotation_euler = (
        (Vector((0, 0, 0.9)) - o.location).to_track_quat("-Z", "Y").to_euler()
    )
camdata = bpy.data.cameras.new("Camera")
cam = bpy.data.objects.new("Camera", camdata)
scene.collection.objects.link(cam)
scene.camera = cam
camdata.type = "ORTHO"
if args.view != "motion":
    cam.location = (0, 6 if args.view == "front" else -6, 1)
    target = Vector((0, 0, 0.9))
    camdata.ortho_scale = 2.05
else:
    stage_radius, stage_y = (1.26, 0.46) if args.exercise == "row" else (1.08, 0)
    if extension:
        position, look_at, ortho, stage_radius, stage_y = extension.camera()
        cam.location = position
        target = Vector(look_at)
        camdata.ortho_scale = ortho
    elif args.exercise == "squat":
        cam.location = (3.7, 5, 2.7)
        target = Vector((0, 0.02, 0.78))
        camdata.ortho_scale = 2.75
    elif args.exercise == "bench":
        cam.location = (3.4, 3.5, 3.4)
        target = Vector((0, -0.08, 0.50))
        camdata.ortho_scale = 2.82
    else:
        cam.location = (3.6, -4.6, 2.9)
        target = Vector((0, 0.46, 0.58))
        camdata.ortho_scale = 3.05
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=96,
        radius=stage_radius,
        depth=0.026,
        location=(0, stage_y, -0.027),
    )
    finish(bpy.context.object, "Studio stage", BASE)
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
scene["exercise"] = args.exercise
scene["sex"] = args.sex
scene[
    "source_character"
] = f"docs/character-assets/muscle-overlay-v1/{args.sex}/greek-{args.sex}-muscles.blend"
scene["muscle_regions"] = ",".join(active)
scene["review_status"] = "Visual prototype; professional movement review pending"
scene.frame_set(1)
first = {b.name: b.matrix.copy() for b in rig.pose.bones}
scene.frame_set(frame_count + 1)
seam = max(
    max(abs(a - b) for ra, rb in zip(first[p.name], p.matrix) for a, b in zip(ra, rb))
    for p in rig.pose.bones
)
checks = {
    "frames_checked": frame_count + 1,
    "max_limb_length_error_m": max(length_errors, default=0),
    "max_grip_target_error_m": max(contact_errors, default=0),
    "loop_matrix_error": seam,
    "shoulder_refinement": shoulder_report,
    "squat_bar_anchor_local": list(bar_anchor_local) if bar_anchor_local else None,
    "rest_joint_calibration": "wrists and ankles corrected in animation copies",
    "muscles": active,
    "pose_records": pose_records,
}
if args.view == "motion":
    (OUT / "motion-checks.json").write_text(json.dumps(checks, indent=2) + "\n")
assert (
    seam < 1e-5
    and max(length_errors, default=0) < 1e-5
    and max(contact_errors, default=0) < 1e-4
)
if args.view == "motion":
    scene.frame_set(1)
    bpy.context.view_layer.update()
    checks["finger_bones"] = 30
    if not (extension and extension.open) and args.exercise != "squat":
        # The generated hands contain long triangles spanning the grip cavity.
        # Subdivide only the hand surface before its skin-space contact corrective;
        # UVs and interpolated bone weights survive, and the actual faces clear steel.
        bm = bmesh.new()
        bm.from_mesh(character.data)
        deform = bm.verts.layers.deform.active
        hand_groups = {g.index for g in character.vertex_groups if "Hand" in g.name}
        hand_verts = {
            v
            for v in bm.verts
            if sum(w for i, w in v[deform].items() if i in hand_groups) > 0.65
        }
        edges = [e for e in bm.edges if all(v in hand_verts for v in e.verts)]
        bmesh.ops.subdivide_edges(bm, edges=edges, cuts=3, use_grid_fill=True)
        bm.to_mesh(character.data)
        bm.free()
        character.data.update()
    if extension and extension.config.get("contact_recipe") == "preserve_thickness":
        from grip_surface import refine_cavity
        checks["grip_surface_refinement"] = refine_cavity(character, extension.grips, extension.SIDES)
    checks["contact_corrective"] = (
        None
        if extension and extension.open
        else add_contact_clearance(
            rig,
            character,
            hand_centers,
            radius_world=0.017 if args.exercise == "calf_raise" else 0.0155,
            preserve_thickness=((extension and extension.config.get("contact_recipe") == "preserve_thickness")
                or (args.sex == "male" and args.exercise == "pushdown")
                or (args.sex == "female" and args.exercise in ("pec_fly", "reverse_fly"))),
        )
    )
    if extension and extension.config.get("unilateral"):
        inactive = "Right" if extension.config["unilateral"] == "Left" else "Left"
        character.data.shape_keys.key_blocks[inactive + "_Grip_Clearance"].value = 0
        checks["contact_corrective"][inactive]["disabled_unloaded_hand"] = True
    (OUT / "motion-checks.json").write_text(json.dumps(checks, indent=2) + "\n")
scene["deformation_rig_version"] = RIG_VERSION
scene["ankle_calibration"] = json.dumps(ankle_report)
if extension and args.view == "motion":
    extension.finish()
    scene.eevee.taa_render_samples = 32
    fit_plan_camera(scene)
# Flat presses keep their previously calibrated shoulder skinning: their
# forward-reaching arms need different axillary clearance from overhead lifts.
if args.view == "motion" and args.exercise not in (
    "squat", "dead_bug", "bench", "db_bench_press", "neutral_bench_press", "single_bench_press"
):
    from shoulder_blend import bake as bake_shoulder_blend
    # Forward-facing neutral grips have less axillary clearance on this male
    # sculpture. Retain more DQ volume there rather than compressing the seam.
    shoulder_strength = 0.5 if args.sex == "male" and args.exercise in (
        "seated_alternate_press", "seated_neutral_press", "standing_neutral_press",
        "single_neutral_press"
    ) else 1.0
    checks["shoulder_blend"] = bake_shoulder_blend(
        scene, character, rig, strength=shoulder_strength
    )
    (OUT / "motion-checks.json").write_text(json.dumps(checks, indent=2) + "\n")
if args.view == "motion" and args.exercise != "squat":
    from fit_contacts import fit_contacts

    fit_contacts(scene, character, args.exercise)
    from equipment_refit import refit
    refit(scene, args.exercise)
    if extension:
        fit_plan_camera(scene)
if args.view == "motion" and extension and extension.config.get("unilateral"):
    from active_side_camera import aim as aim_active_side
    aim_active_side(scene, extension.config["unilateral"])
scene.frame_set(args.frame if args.view == "motion" else 1)
if args.view == "motion":
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(DELIVER / f"{args.exercise}.blend"))
if args.no_render:
    pass
elif args.preview or args.view != "motion":
    scene.render.filepath = str(
        OUT
        / (
            f"motion-{args.frame:04d}.png"
            if args.view == "motion"
            else f"{args.view}.png"
        )
    )
    bpy.ops.render.render(write_still=True)
else:
    if args.exercise != "squat":
        from collision_audit import audit_scene
        from deformation_gate import require_deformation_pass

        if args.exercise in LIBRARY_EXERCISES:
            from library_gate import require_scene_pass
            require_scene_pass(args.sex, args.exercise, root=args.output_root)
        else:
            require_deformation_pass(args.sex, args.exercise, root=args.output_root)

        failures = audit_scene(scene, list(range(1, frame_count + 2)))
        assert not failures, f"Collision gate failed: {failures[:5]}"
    (OUT / "frames").mkdir(exist_ok=True)
    scene.render.filepath = str(OUT / "frames/frame-")
    bpy.ops.render.render(animation=True)
    (OUT / "render-source.json").write_text(
        json.dumps(
            {
                "sha256": hashlib.sha256(
                    (DELIVER / f"{args.exercise}.blend").read_bytes()
                ).hexdigest()
            }
        )
        + "\n"
    )
