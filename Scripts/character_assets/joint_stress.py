"""Reproducible isolated joint ROM clips from the shared character binding."""
import argparse, sys, math, json, hashlib
from pathlib import Path
import bpy
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from prepare_athlete import prepare_character
from deformation_rig import pose_forearm_twist

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--sex", choices=["male", "female"], required=True)
p.add_argument("--output-root", type=Path, default=ROOT)
p.add_argument("--render", action="store_true")
a = p.parse_args(sys.argv[sys.argv.index("--") + 1 :])
out = a.output_root / "docs/character-assets/deformation-rig-v2" / a.sex
out.mkdir(parents=True, exist_ok=True)
work = a.output_root / "build/joint-stress" / a.sex
work.mkdir(parents=True, exist_ok=True)
rig, body, centers, chains, shoulder, ankle, scale = prepare_character(a.sex)
s = bpy.context.scene
s["sex"] = a.sex
for key in [
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
]:
    rig[key] = 0.0
rig.update_tag()
bpy.context.view_layer.update()
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str((out / "athlete.blend").resolve()))
s.render.engine = "BLENDER_EEVEE"
s.eevee.taa_render_samples = 24
s.render.resolution_x = 640
s.render.resolution_y = 640
s.render.resolution_percentage = 100
s.render.image_settings.file_format = "PNG"
s.render.film_transparent = False
s.world = bpy.data.worlds.new("Joint test world")
s.world.use_nodes = True
background = s.world.node_tree.nodes.new("ShaderNodeBackground")
output = s.world.node_tree.nodes.new("ShaderNodeOutputWorld")
s.world.node_tree.links.new(background.outputs[0], output.inputs[0])
background.inputs[0].default_value = (0.78, 0.78, 0.74, 1)
background.inputs[1].default_value = 0.7
for loc, energy, size in [((3, 4, 6), 650, 5), ((-4, 0, 3), 350, 4)]:
    data = bpy.data.lights.new("Area", "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new("Area", data)
    s.collection.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = (
        (Vector((0, 0, 1)) - obj.location).to_track_quat("-Z", "Y").to_euler()
    )
data = bpy.data.cameras.new("Joint Camera")
cam = bpy.data.objects.new("Joint Camera", data)
s.collection.objects.link(cam)
s.camera = cam
data.type = "ORTHO"


def camera(target, view, zoom):
    cam.location = target + Vector(view)
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.ortho_scale = zoom


cases = [
    ("neutral", None, 0),
    ("elbow_flex", "ForeArm", 120),
    ("forearm_twist", "ForeArm", 70),
    ("shoulder_raise", "Arm", 100),
    ("hip_flex", "UpLeg", 90),
    ("knee_flex", "Leg", 120),
    ("ankle_flex", "Foot", 50),
    ("toe_flex", "ToeBase", 40),
]
span = 32
s.frame_start = 1
s.frame_end = len(cases) * span
s.render.fps = 24
for ci, (case, part, degrees) in enumerate(cases):
    for fi in range(span):
        frame = ci * span + fi + 1
        s.frame_set(frame)
        for bone in rig.pose.bones:
            bone.matrix_basis = Matrix.Identity(4)
            bone.rotation_mode = "QUATERNION"
        bpy.context.view_layer.update()
        amount = math.sin(math.pi * fi / (span - 1)) ** 2
        if part:
            for side, sign in [("Left", 1), ("Right", -1)]:
                bone = rig.pose.bones[
                    "mixamorig:" + side + ("Hand" if case == "forearm_twist" else part)
                ]
                angle = math.radians(degrees) * amount
                old = (bone.bone.tail_local - bone.bone.head_local).normalized()
                if case == "elbow_flex":
                    axis = old.cross(Vector((1, 0, 0))).normalized()
                elif case == "forearm_twist":
                    fore = rig.data.bones["mixamorig:" + side + "ForeArm"]
                    axis = (fore.tail_local - fore.head_local).normalized()
                    angle *= sign
                elif case == "shoulder_raise":
                    axis = Vector((1, 0, 0))
                    angle *= sign
                else:
                    axis = Vector((0, 1, 0))
                    angle *= -1 if case in ["hip_flex", "ankle_flex"] else 1
                matrix = Matrix.Rotation(angle, 4, axis) @ bone.bone.matrix_local
                matrix.translation = bone.bone.head_local
                bone.matrix = matrix
                bpy.context.view_layer.update()
        for side in ["Left", "Right"]:
            pose_forearm_twist(rig, side)
        for bone in rig.pose.bones:
            bone.keyframe_insert("location", frame=frame)
            bone.keyframe_insert("rotation_quaternion", frame=frame)
# Rest-to-rest loops; both end states of every segment are neutral.
camera(Vector((0, 0, 0.93)), (-3, 5, 2.0), 2.2)
bpy.ops.wm.save_as_mainfile(filepath=str((out / "joint-stress.blend").resolve()))
records = []
for ci, (case, part, angle) in enumerate(cases):
    frame = ci * span + span // 2
    s.frame_set(frame)
    if part:
        b = rig.pose.bones["mixamorig:Left" + part]
        target = rig.matrix_world @ b.head
        zoom = 0.70 if part in ["ForeArm", "Foot", "ToeBase"] else 1.15
    else:
        target = Vector((0, 0, 0.95))
        zoom = 2.1
    for view, direction in [
        ("front", (-2, 4, 1)),
        ("side", (-4, 0, 1)),
        ("back", (2, -4, 1)),
    ]:
        camera(target, direction, zoom)
        s.render.filepath = str(work / f"{case}-{view}.png")
        bpy.ops.render.render(write_still=True)
    records.append(dict(case=case, peak_frame=frame, angle_degrees=angle))
if a.render:
    camera(Vector((0, 0, 0.93)), (-3, 5, 2.0), 2.2)
    (work / "frames").mkdir(exist_ok=True)
    for frame in range(1, s.frame_end + 1):
        s.frame_set(frame)
        s.render.filepath = str(work / f"frames/frame-{frame:04d}.png")
        bpy.ops.render.render(write_still=True)
(out / "tests.json").write_text(
    json.dumps(
        dict(
            cases=records,
            baseline_sha256=hashlib.sha256(
                (out / "athlete.blend").read_bytes()
            ).hexdigest(),
            note="ROM stress poses, not exercise technique references. Visual review is separate.",
        ),
        indent=2,
    )
    + "\n"
)
