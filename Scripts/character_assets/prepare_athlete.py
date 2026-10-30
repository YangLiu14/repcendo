"""Build the versioned neutral athlete binding used by every exercise scene.

Keeps source meshes intact. The CLI also saves neutral .blend baselines so joint
stress tests use exactly the same weights and rest bones as motion generation.
"""
import sys, math, json, argparse, hashlib
from pathlib import Path
import bpy, bmesh
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(Path(__file__).parent), str(ROOT / "Scripts/animation_samples")]
from deformation_rig import (
    calibrate_ankle_weights,
    calibrate_hinge_weights,
    install_forearm_twist,
    VERSION as RIG_VERSION,
)
from hand_rig import install as install_hands
from shoulder_rig import refine_upper_back


def prepare_character(sex, root=ROOT):
    source = (
        root
        / f"docs/character-assets/muscle-overlay-v1/{sex}/greek-{sex}-muscles.blend"
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
        wrist.z = 0.488 if sex == "male" else 0.490
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
        kind = "Hand" if p.z < 0.490 and abs(p.y) > 0.195 else None
        if not kind:
            continue
        side = "Left" if p.y > 0 else "Right"
        blend = max(0, min(1, (0.49 - p.z) / 0.025))
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

    ankle_report = calibrate_ankle_weights(character, rig)
    calibrate_hinge_weights(character, rig, sex)
    for modifier in character.modifiers:
        if modifier.type == "ARMATURE":
            modifier.use_deform_preserve_volume = True
    # Rig real finger chains; retain the original sculpture mesh and textures.
    sys.path.insert(0, str(root / "Scripts/character_assets"))

    hand_centers, hand_chains = install_hands(rig, character, sex)
    install_forearm_twist(character, rig)

    shoulder_report = refine_upper_back(character, sex)
    # Upright model +X front -> scene +Y front, height around 1.78 m.
    scale = 1.82 if sex == "male" else 1.76
    rig.matrix_world = Matrix.Rotation(math.pi / 2, 4, "Z") @ Matrix.Diagonal(
        (scale, scale, scale, 1)
    )
    bpy.context.view_layer.update()
    for bone in rig.pose.bones:
        bone.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    rig["source_character_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    rig["binding_recipe_sha256"] = hashlib.sha256(
        Path(__file__).read_bytes()
    ).hexdigest()
    return (
        rig,
        character,
        hand_centers,
        hand_chains,
        shoulder_report,
        ankle_report,
        scale,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sex", choices=["male", "female"], required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    rig, body, centers, chains, shoulder, ankle, scale = prepare_character(a.sex)
    bpy.context.scene["sex"] = a.sex
    bpy.context.scene["deformation_rig_version"] = RIG_VERSION
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
    a.output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(a.output.resolve()))
