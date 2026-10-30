"""Bake local, pose-space shoulder corrections for the Greek dead-bug scenes.

The original Armature still drives the body. A local surface solve supplies
corrective shape keys; it does not change the source sculpture, UVs, skeleton,
motion, or hand targets. Volume guides keep surface relaxation from collapsing
the upper arms. These guides are calibrated assets, not anatomical simulation.

Requires SciPy in build/deformation-python (see animation-pipeline.md).
Publication still requires all-frame deformation/collision and visual reviews.
"""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [
    str(Path(__file__).parent),
    str(
        Path(
            os.environ.get(
                "REPCENDO_DEFORMATION_MODULES", ROOT / "build/deformation-python"
            )
        )
    ),
    str(ROOT / "Scripts/character_assets"),
]

import bpy
import numpy as np
from mathutils import Vector
from scipy.interpolate import CubicSpline

from shoulder_volume import ShoulderVolume
from shoulder_contacts import ShoulderContacts
from skin_matrix import blend_rigid


def coordinates(body):
    evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    points = np.empty(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get("co", points)
    evaluated.to_mesh_clear()
    return points.reshape(-1, 3)


def linearize_keys(body):
    action = body.data.shape_keys.animation_data.action
    for layer in action.layers:
        for strip in layer.strips:
            for slot in action.slots:
                bag = strip.channelbag(slot)
                if bag:
                    for curve in bag.fcurves:
                        for point in curve.keyframe_points:
                            point.interpolation = "LINEAR"


def bake_contacts(scene, body, rig, rest, weights, contacts, sex):
    # Check contact on the evaluated, interpolated result at every frame, not
    # merely at the sparse volume-solve samples. Bake only nonzero responses.
    contact_keys = []
    max_contact_shift = 0.0
    for frame in range(1, scene.frame_end + 1):
        scene.frame_set(frame)
        current = coordinates(body)
        try:
            target, movement = contacts.separate(current)
        except RuntimeError as error:
            raise RuntimeError(f"{sex}/dead_bug frame {frame}: {error}") from error
        if movement < 1e-8:
            continue
        max_contact_shift = max(max_contact_shift, movement)
        changed = np.flatnonzero(np.linalg.norm(target - current, axis=1) > 1e-9)
        matrices = {
            b.name: b.matrix @ b.bone.matrix_local.inverted() for b in rig.pose.bones
        }
        downstream = [
            m for m in body.modifiers if m.type != "ARMATURE" and m.show_viewport
        ]
        try:
            for m in downstream:
                m.show_viewport = False
            bpy.context.view_layer.update()
            raw_skin = coordinates(body)
        finally:
            for m in downstream:
                m.show_viewport = True
            bpy.context.view_layer.update()
        delta = np.zeros_like(rest)
        for index in changed:
            matrix = blend_rigid(matrices, weights[index])
            delta[index] = matrix.to_3x3().transposed() @ Vector(
                target[index] - raw_skin[index]
            )
        contact_keys.append((frame, delta))
        print("SHOULDER_CONTACT", sex, frame, movement, flush=True)
    for frame, delta in contact_keys:
        key = body.shape_key_add(name=f"ShoulderContact.{frame:03d}")
        key.data.foreach_set("co", (rest + delta).ravel())
        values = {1: 0.0, 193: 0.0, frame - 1: 0.0, frame: 1.0, frame + 1: 0.0}
        if frame == 1:
            values.update({193: 1.0, 192: 0.0})
        for f, value in sorted(values.items()):
            if f < 1:
                continue
            key.value = value
            key.keyframe_insert("value", frame=f)
    return contact_keys, max_contact_shift


def bake(source, destination, step=8):
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(source.resolve()))
    scene = bpy.context.scene
    if scene.get("exercise") != "dead_bug" or scene.frame_end != 192:
        raise ValueError("Only the calibrated 192-frame dead-bug motion is supported")
    sex = scene["sex"]
    rig = next(o for o in scene.objects if o.type == "ARMATURE")
    body = next(
        o
        for o in scene.objects
        if o.type == "MESH" and any(m.type == "ARMATURE" for m in o.modifiers)
    )
    if body.data.shape_keys:
        raise ValueError(
            "Bake from the uncorrected scene; existing shape keys are not overwritten"
        )
    modifier = next(m for m in body.modifiers if m.type == "ARMATURE")
    if not modifier.use_deform_preserve_volume:
        raise ValueError("Inverse corrections require the calibrated DQ binding")
    if not np.allclose(np.array(body.matrix_world), np.array(rig.matrix_world)):
        raise ValueError("Unexpected mesh/armature coordinate spaces")
    rest = np.array([v.co[:] for v in body.data.vertices])
    edges = np.array([e.vertices[:] for e in body.data.edges])
    names = ["mixamorig:" + n for n in ["Spine2", "LeftArm", "RightArm"]]
    bones = np.array(
        [
            [rig.data.bones[n].head_local[:], rig.data.bones[n].tail_local[:]]
            for n in names
        ]
    )
    solver = ShoulderVolume(rest, edges, bones, sex)
    contacts = ShoulderContacts(body, solver.free, sex)
    weights = [
        [
            (body.vertex_groups[g.group].name, g.weight)
            for g in v.groups
            if g.weight > 0
            and body.vertex_groups[g.group].name in rig.data.bones
            and rig.data.bones[body.vertex_groups[g.group].name].use_deform
        ]
        for v in body.data.vertices
    ]
    samples = list(range(1, scene.frame_end + 1, step))
    if scene.frame_end % step:
        raise ValueError("Sample step must divide the closed cycle")
    solver_hash = hashlib.sha256(
        Path(__file__).with_name("shoulder_volume.py").read_bytes()
    ).hexdigest()
    inverse_hash = hashlib.sha256(
        (ROOT / "Scripts/character_assets/skin_matrix.py").read_bytes()
    ).hexdigest()
    cache_key = hashlib.sha256(
        (
            "inverse-dq-1"
            + source_hash
            + solver_hash
            + inverse_hash
            + bpy.app.version_string
        ).encode()
    ).hexdigest()
    cache = ROOT / "build/shoulder-corrective-cache" / cache_key
    cache.mkdir(parents=True, exist_ok=True)
    corrections = []
    for frame in samples:
        cached = cache / f"{frame:03d}.npy"
        if cached.exists():
            correction = np.load(cached)
            if correction.shape != rest.shape or not np.isfinite(correction).all():
                raise ValueError(f"Invalid corrective cache: {cached}")
            corrections.append(correction)
            continue
        scene.frame_set(frame)
        current = coordinates(body)
        matrices = {
            b.name: b.matrix @ b.bone.matrix_local.inverted() for b in rig.pose.bones
        }
        target = solver.solve(current.copy(), np.array([matrices[n] for n in names]))
        # Solve above the floor, then leave the existing mat contact modifier
        # responsible for support. Inverse-skin the correction before that layer.
        downstream = [
            m for m in body.modifiers if m.type != "ARMATURE" and m.show_viewport
        ]
        try:
            for m in downstream:
                m.show_viewport = False
            bpy.context.view_layer.update()
            raw_skin = coordinates(body)
        finally:
            for m in downstream:
                m.show_viewport = True
            bpy.context.view_layer.update()
        correction = np.zeros_like(rest)
        for index in solver.f:
            matrix = blend_rigid(matrices, weights[index])
            correction[index] = matrix.to_3x3().transposed() @ Vector(
                target[index] - raw_skin[index]
            )
        corrections.append(correction)
        temporary = cached.with_suffix(".tmp")
        with temporary.open("wb") as stream:
            np.save(stream, correction)
        temporary.replace(cached)
        print("SHOULDER", sex, frame, flush=True)
    if sex == "female":
        # Preserve the source drapery at the left anterior shoulder while that
        # arm is vertical. The surface-volume solve otherwise pulls a cloth
        # fold into the axilla. Release this local protection during overhead
        # reach, using the same calibrated phase as the dead-bug motion.
        distance = np.linalg.norm(rest - np.array([0.034, 0.086, 0.748]), axis=1)
        cloth = np.exp(-((distance / 0.07) ** 4))
        for i, frame in enumerate(samples):
            phase = (frame - 1) / scene.frame_end
            reach = np.sin(2 * np.pi * phase) ** 2 if phase < 0.5 else 0.0
            t = np.clip((reach - 0.35) / 0.5, 0.0, 1.0)
            protection = 1 - t * t * (3 - 2 * t)
            corrections[i] = corrections[i] * (1 - cloth * protection)[:, None]
    body.shape_key_add(name="Basis")
    # Periodic cardinal interpolation gives a smooth, closed correction track.
    # Bake its values at every exported frame; small negative basis coefficients
    # are intentional cubic interpolation, not negative skinning weights.
    knots = samples + [scene.frame_end + 1]
    identity = np.eye(len(samples))
    values = CubicSpline(knots, np.vstack([identity, identity[0]]), bc_type="periodic")(
        np.arange(1, scene.frame_end + 2)
    )
    for i, (frame, correction) in enumerate(zip(samples, corrections)):
        key = body.shape_key_add(name=f"ShoulderVolume.{frame:03d}")
        key.data.foreach_set("co", (rest + correction).ravel())
        key.slider_min = -1
        key.slider_max = 2
        for f, value in enumerate(values[:, i], start=1):
            key.value = float(value)
            key.keyframe_insert("value", frame=f)
    contact_keys, max_contact_shift = bake_contacts(
        scene, body, rig, rest, weights, contacts, sex
    )
    linearize_keys(body)
    scene.frame_set(1)
    body["shoulder_corrective_version"] = ShoulderVolume.VERSION
    body["shoulder_corrective_source_sha256"] = source_hash
    destination.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(destination.resolve()))
    report = dict(
        version=ShoulderVolume.VERSION,
        source_sha256=source_hash,
        scene_sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
        samples=samples,
        interpolated_frames=193,
        changed_vertices=len(solver.f),
        max_iterations=solver.max_iterations,
        contact_frames=[f for f, _ in contact_keys],
        max_contact_shift_m=max_contact_shift,
        key_interpolation="LINEAR",
        status="baked_requires_validation_and_visual_review",
        solver_sha256=solver_hash,
        contact_solver_sha256=hashlib.sha256(
            Path(__file__).with_name("shoulder_contacts.py").read_bytes()
        ).hexdigest(),
    )
    destination.with_name("dead_bug-shoulder-corrective.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--step", type=int, default=8)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    bake(args.scene, args.output, args.step)
