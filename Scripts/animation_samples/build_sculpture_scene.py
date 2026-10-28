"""Animate the selected skinned sculptures with original two-bone motion solves.

Local Blender only. Keeps source character assets intact; writes v2 samples.
"""
import argparse, json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from exercise_catalog import EXERCISES, PRIMARY_MUSCLES

P = argparse.ArgumentParser()
P.add_argument("--exercise", choices=list(EXERCISES), required=True)
P.add_argument("--sex", choices=["male", "female"], default="male")
P.add_argument("--preview", action="store_true")
P.add_argument("--frame", type=int, default=61)
P.add_argument("--view", choices=["motion", "front", "back"], default="motion")
args = P.parse_args(sys.argv[sys.argv.index("--") + 1 :])
OUT = ROOT / f"build/animation-samples-v2/{args.sex}/{args.exercise}"
OUT.mkdir(parents=True, exist_ok=True)
DELIVER = ROOT / f"docs/animation-samples-v2/{args.sex}"
DELIVER.mkdir(parents=True, exist_ok=True)
source = (
    ROOT
    / f"docs/character-assets/muscle-overlay-v1/{args.sex}/greek-{args.sex}-muscles.blend"
)
bpy.ops.wm.open_mainfile(filepath=str(source))
rig = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
character = next(
    o
    for o in bpy.context.scene.objects
    if o.type == "MESH"
    and any(m.type == "ARMATURE" and m.object == rig for m in o.modifiers)
)
for o in list(bpy.context.scene.objects):
    if o not in [rig, character]:
        bpy.data.objects.remove(o, do_unlink=True)
# Weld coincident import seams before weighting fingers. UVs are face-corner
# data and remain intact; connected vertices also restore smooth knuckle normals.
import bmesh

bm = bmesh.new()
bm.from_mesh(character.data)
bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=0.000001)
bm.to_mesh(character.data)
bm.free()
character.data.update()
for poly in character.data.polygons:
    poly.use_smooth = True
character.data.normals_split_custom_set([(0, 0, 0)] * len(character.data.loops))
rig.animation_data_clear()
rig.data.display_type = "OCTAHEDRAL"
rig.show_in_front = True
# Correct obvious automatic-rig endpoint placements in the animation COPY.
bpy.context.view_layer.objects.active = rig
rig.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
for side in ["Left", "Right"]:
    b = rig.data.edit_bones
    wrist = b["mixamorig:" + side + "Hand"].head.copy()
    wrist.z = 0.488 if args.sex == "male" else 0.490
    b["mixamorig:" + side + "ForeArm"].tail = wrist
    b["mixamorig:" + side + "Hand"].head = wrist
    b["mixamorig:" + side + "Hand"].tail = Vector((wrist.x + 0.030, wrist.y, 0.424))
    ankle = b["mixamorig:" + side + "Foot"].head.copy()
    ankle.z = 0.065
    b["mixamorig:" + side + "Leg"].tail = ankle
    b["mixamorig:" + side + "Foot"].head = ankle
    toe = Vector((0.043, ankle.y, 0.025))
    b["mixamorig:" + side + "Foot"].tail = toe
    b["mixamorig:" + side + "ToeBase"].head = toe
    b["mixamorig:" + side + "ToeBase"].tail = Vector((0.085, ankle.y, 0.022))
bpy.ops.object.mode_set(mode="OBJECT")
# Reweight distal regions to the calibrated joints in the animation copy.
# The original generated weights treated much of the foot as lower leg.
for vertex in character.data.vertices:
    p = vertex.co
    kind = (
        "Foot"
        if p.z < 0.130
        else ("Hand" if p.z < 0.490 and abs(p.y) > 0.195 else None)
    )
    if not kind:
        continue
    side = "Left" if p.y > 0 else "Right"
    blend = (
        max(0, min(1, (0.130 - p.z) / 0.050))
        if kind == "Foot"
        else max(0, min(1, (0.49 - p.z) / 0.025))
    )
    if blend <= 0:
        continue
    weights = [(g.group, g.weight) for g in vertex.groups]
    for group_index, weight in weights:
        character.vertex_groups[group_index].add(
            [vertex.index], weight * (1 - blend), "REPLACE"
        )
    group = character.vertex_groups["mixamorig:" + side + kind]
    old = next((w for i, w in weights if i == group.index), 0)
    group.add([vertex.index], old * (1 - blend) + blend, "REPLACE")
# Rig real finger chains; retain the original sculpture mesh and textures.
sys.path.insert(0, str(ROOT / "Scripts/character_assets"))
from hand_rig import install as install_hands, pose_fingers, add_contact_clearance

hand_centers, hand_chains = install_hands(rig, character, args.sex)
from shoulder_rig import refine_upper_back, squat_bar_anchor

shoulder_report = refine_upper_back(character, args.sex)
# Upright model +X front -> scene +Y front, height around 1.78 m.
scale = 1.82 if args.sex == "male" else 1.76
rig.matrix_world = Matrix.Rotation(math.pi / 2, 4, "Z") @ Matrix.Diagonal(
    (scale, scale, scale, 1)
)
bpy.context.view_layer.update()
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
active = PRIMARY_MUSCLES[args.exercise]
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
                (s * 0.085, 0, 0.065),
                0.014,
                STEEL,
                HANDLE,
            )
            cylinder("V handle", (s * 0.085, 0, 0), (0, 0.09, 0), 0.013, STEEL, HANDLE)
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


def pose(f):
    bpy.context.scene.frame_set(f)
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
                    - (0.34 if args.sex == "male" else 0.31) * d,
                )
            )
        )
        BAR.location = bar
        BAR.keyframe_insert("location", frame=f)
        BAR.rotation_euler.x = -(0.20 + 0.35 * d) if args.exercise == "squat" else 0
        BAR.keyframe_insert("rotation_euler", frame=f)
    elif not static:
        handle = Vector((0, 0.505 - 0.405 * d, 0.94 - 0.085 * d))
        HANDLE.location = handle
        HANDLE.keyframe_insert("location", frame=f)
        a = handle + Vector((0, 0.09, 0))
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
            epole = Vector((s * 0.40, -0.42, 0.89))
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
        normal = (elbow - shoulder).cross(wrist - elbow).normalized()
        # Match the rest elbow plane, avoiding uncontrolled humeral twist.
        rest_normal = (
            (head[n("ForeArm")] - head[n("Arm")])
            .cross(head[n("Hand")] - head[n("ForeArm")])
            .normalized()
        )
        for part, a, b in [("Arm", shoulder, elbow), ("ForeArm", elbow, wrist)]:
            delta = (
                frame(b - a, normal)
                @ frame(tail[n(part)] - head[n(part)], rest_normal).inverted()
            )
            if part == "Arm" and args.exercise == "squat":
                # The almost-straight source elbow plane is not a reliable humeral twist
                # reference. Preserve the shoulder's anatomical swing without a 180° roll.
                old_dir = tail[n(part)] - head[n(part)]
                new_dir = R.inverted() @ (b - a)
                delta = R @ old_dir.rotation_difference(new_dir).to_matrix().to_4x4()
            setbone(n(part), a, delta, f)
        setbone(n("Hand"), wrist, handR, f)
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


for f in range(1, 122) if args.view == "motion" else [1, 121]:
    pose(f)
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 120
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
    if args.exercise == "squat":
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
        radius=1.08 if args.exercise != "row" else 1.26,
        depth=0.026,
        location=(0, 0.46 if args.exercise == "row" else 0, -0.027),
    )
    finish(bpy.context.object, "Studio stage", BASE)
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
scene["exercise"] = args.exercise
scene["sex"] = args.sex
scene["source_character"] = str(source.relative_to(ROOT))
scene["muscle_regions"] = ",".join(active)
scene["review_status"] = "Visual prototype; professional movement review pending"
scene.frame_set(1)
first = {b.name: b.matrix.copy() for b in rig.pose.bones}
scene.frame_set(121)
seam = max(
    max(abs(a - b) for ra, rb in zip(first[p.name], p.matrix) for a, b in zip(ra, rb))
    for p in rig.pose.bones
)
checks = {
    "frames_checked": 121,
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
    checks["contact_corrective"] = add_contact_clearance(rig, character, hand_centers)
    (OUT / "motion-checks.json").write_text(json.dumps(checks, indent=2) + "\n")
scene.frame_set(args.frame if args.view == "motion" else 1)
if args.view == "motion":
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(DELIVER / f"{args.exercise}.blend"))
if args.preview or args.view != "motion":
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
    (OUT / "frames").mkdir(exist_ok=True)
    scene.render.filepath = str(OUT / "frames/frame-")
    bpy.ops.render.render(animation=True)
