"""Independent shape checks; collision success is not a deformation approval.

Automated checks detect known regression mechanisms. Surface strain is recorded
for review, not presented as an anatomical certification. Publication also needs
hash-matched multi-view visual review.
"""
import argparse, hashlib, json, math, sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector


def inspect(scene, frames):
    rig = next(o for o in scene.objects if o.type == "ARMATURE")
    body = next(
        o
        for o in scene.objects
        if o.type == "MESH"
        and any(m.type == "ARMATURE" and m.object == rig for m in o.modifiers)
    )
    failures = []
    labels = {g.index: g.name for g in body.vertex_groups}
    deform = {b.name for b in rig.data.bones if b.use_deform}
    for modifier in body.modifiers:
        if (
            modifier.type == "SMOOTH"
            and modifier.show_viewport
            and modifier.iterations >= 20
            and abs(modifier.factor) >= 0.5
        ):
            failures.append(
                dict(
                    check="destructive_joint_smoothing",
                    modifier=modifier.name,
                    iterations=modifier.iterations,
                )
            )
    for side in ["Left", "Right"]:
        ankle = rig.data.bones["mixamorig:" + side + "Foot"].head_local
        wrong = []
        for vertex in body.data.vertices:
            if vertex.co.z <= ankle.z + 0.035:
                continue
            weight = sum(
                g.weight
                for g in vertex.groups
                if labels[g.group]
                in ["mixamorig:" + side + "Foot", "mixamorig:" + side + "ToeBase"]
            )
            if weight > 0.15:
                wrong.append(vertex.index)
        if wrong:
            failures.append(
                dict(check="foot_drags_lower_shin", side=side, vertices=len(wrong))
            )
    sums = [
        sum(g.weight for g in v.groups if labels[g.group] in deform)
        for v in body.data.vertices
    ]
    if min(sums) < 0.999 or max(sums) > 1.001:
        failures.append(
            dict(
                check="deform_weight_normalization",
                minimum=min(sums),
                maximum=max(sums),
            )
        )
    maxima = dict(
        scale_error=0.0, elbow_axial_discontinuity_deg=0.0, frame_rotation_step_deg=0.0
    )
    previous = {}
    coords = np.array([tuple(body.matrix_world @ v.co) for v in body.data.vertices])
    edges = np.array([tuple(e.vertices) for e in body.data.edges])
    regions = {}
    surface = {}
    for side in ["Left", "Right"]:
        for part in ["Arm", "ForeArm", "UpLeg", "Leg", "Foot"]:
            key = side + part
            center = np.array(
                rig.matrix_world @ rig.data.bones["mixamorig:" + key].head_local
            )
            mask = np.linalg.norm(coords - center, axis=1) < 0.12
            selected = edges[np.all(mask[edges], axis=1)]
            lengths = np.linalg.norm(
                coords[selected[:, 0]] - coords[selected[:, 1]], axis=1
            )
            selected = selected[lengths > 1e-5]
            lengths = lengths[lengths > 1e-5]
            regions[key] = selected, lengths
            surface[key] = dict(
                min_p05=1.0,
                max_p95=1.0,
                compressed_frame=frames[0],
                stretched_frame=frames[0],
            )
    for frame in frames:
        scene.frame_set(frame)
        evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        if len(mesh.vertices) != len(coords):
            raise ValueError("Shape audit requires stable body topology")
        points = np.empty(len(mesh.vertices) * 3)
        mesh.vertices.foreach_get("co", points)
        points = points.reshape(-1, 3)
        transform = np.array(evaluated.matrix_world)
        points = points @ transform[:3, :3].T + transform[:3, 3]
        evaluated.to_mesh_clear()
        for key, (selected, lengths) in regions.items():
            if not len(selected):
                continue
            ratios = (
                np.linalg.norm(points[selected[:, 0]] - points[selected[:, 1]], axis=1)
                / lengths
            )
            low, high = np.percentile(ratios, [5, 95])
            if low < surface[key]["min_p05"]:
                surface[key].update(min_p05=float(low), compressed_frame=frame)
            if high > surface[key]["max_p95"]:
                surface[key].update(max_p95=float(high), stretched_frame=frame)
        for bone in rig.pose.bones:
            if not bone.bone.use_deform:
                continue
            delta = bone.matrix @ bone.bone.matrix_local.inverted()
            singular = np.linalg.svd(np.array(delta.to_3x3()), compute_uv=False)
            error = float(max(abs(singular - 1)))
            maxima["scale_error"] = max(maxima["scale_error"], error)
            if error > 0.005:
                failures.append(
                    dict(
                        check="nonrigid_bone_transform",
                        frame=frame,
                        bone=bone.name,
                        error=error,
                    )
                )
            rotation = bone.rotation_quaternion.copy()
            if bone.name in previous:
                diff = rotation.rotation_difference(previous[bone.name]).angle
                step = math.degrees(min(diff, 2 * math.pi - diff))
                maxima["frame_rotation_step_deg"] = max(
                    maxima["frame_rotation_step_deg"], step
                )
                if frames[-1] - frames[0] == len(frames) - 1 and step > 35:
                    failures.append(
                        dict(
                            check="rotation_jump",
                            frame=frame,
                            bone=bone.name,
                            degrees=step,
                        )
                    )
            previous[bone.name] = rotation
        for side in ["Left", "Right"]:
            upper = rig.pose.bones["mixamorig:" + side + "Arm"]
            fore = rig.pose.bones["mixamorig:" + side + "ForeArm"]
            parent = (
                upper.matrix.to_quaternion()
                @ upper.bone.matrix_local.to_quaternion().inverted()
            )
            rest = (fore.bone.tail_local - fore.bone.head_local).normalized()
            direction = (fore.tail - fore.head).normalized()
            transported = parent @ rest.rotation_difference(
                parent.inverted() @ direction
            )
            actual = (
                fore.matrix.to_quaternion()
                @ fore.bone.matrix_local.to_quaternion().inverted()
            )
            angle = transported.rotation_difference(actual).angle
            angle = math.degrees(min(angle, 2 * math.pi - angle))
            maxima["elbow_axial_discontinuity_deg"] = max(
                maxima["elbow_axial_discontinuity_deg"], angle
            )
            # Anatomical pronation is distributed along the forearm, not an abrupt
            # >75 degree roll at the proximal elbow seam of this calibrated rig.
            if angle > 75:
                failures.append(
                    dict(
                        check="elbow_axial_discontinuity",
                        frame=frame,
                        side=side,
                        degrees=angle,
                    )
                )
    alerts = [
        dict(region=key, **value)
        for key, value in surface.items()
        if value["min_p05"] < 0.4 or value["max_p95"] > 2.5
    ]
    # These are review hints, not an anatomical pass/fail threshold. Select the
    # two strongest excursions in addition to the standard cycle poses.
    strongest = sorted(
        alerts,
        key=lambda r: max(0.4 / max(r["min_p05"], 1e-8), r["max_p95"] / 2.5),
        reverse=True,
    )[:2]
    review_frames = sorted(
        set(
            [
                1,
                1 + scene.frame_end // 4,
                1 + scene.frame_end // 2,
                1 + 3 * scene.frame_end // 4,
            ]
            + [
                r[field]
                for r in strongest
                for field in ["compressed_frame", "stretched_frame"]
            ]
        )
    )
    return dict(
        failures=failures,
        metrics=maxima,
        frames=frames,
        weight_range=[min(sums), max(sums)],
        visual_review_required=True,
        surface_edge_ratios=surface,
        surface_alerts=alerts,
        review_frames=review_frames,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scene", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--frames", nargs="+", type=int)
    a = p.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    bpy.ops.wm.open_mainfile(filepath=str(a.scene.resolve()))
    s = bpy.context.scene
    result = inspect(s, a.frames or list(range(1, s.frame_end + 2)))
    result.update(
        scene_sha256=hashlib.sha256(a.scene.read_bytes()).hexdigest(),
        validator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        status="failed" if result["failures"] else "automated_checks_passed",
    )
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            dict(
                status=result["status"],
                failures=result["failures"][:8],
                metrics=result["metrics"],
            )
        )
    )
    if result["failures"]:
        raise SystemExit(1)
