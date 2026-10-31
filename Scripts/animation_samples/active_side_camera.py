"""Keep the working arm on the camera side; inspect actual saved poses."""
import hashlib
import json
import math
from pathlib import Path

MIN_NEAR_DEPTH = .05


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def depth(camera_axis, active, inactive):
    return sum(d * (a - b) for d, a, b in zip(camera_axis, active, inactive))


def inspect(scene, side):
    from mathutils import Vector
    rig = next(o for o in scene.objects if o.type == 'ARMATURE')
    other = 'Right' if side == 'Left' else 'Left'
    previous = scene.frame_current
    rows = []
    for f in range(1, scene.frame_end + 2):
        scene.frame_set(f)
        axis = scene.camera.matrix_world.to_quaternion() @ Vector((0, 0, 1))
        points = [rig.matrix_world @ rig.pose.bones['mixamorig:' + s + 'Arm'].head for s in (side, other)]
        rows.append(dict(frame=f, workingShoulderNearDepth=depth(axis, *points)))
    scene.frame_set(previous)
    minimum = min(row['workingShoulderNearDepth'] for row in rows)
    return dict(activeSide=side, frames=[row['frame'] for row in rows], samples=rows,
                minimumNearDepth=minimum, passed=math.isfinite(minimum) and minimum > MIN_NEAR_DEPTH)


def aim(scene, side):
    """Reflect only the camera's viewing direction and position, never the image/body."""
    from mathutils import Vector
    from frame_plan_scene import fit
    if inspect(scene, side)['passed']:
        return
    camera = scene.camera
    forward = camera.matrix_world.to_quaternion() @ Vector((0, 0, -1))
    forward.x *= -1
    camera.location.x *= -1
    camera.rotation_mode = 'XYZ'
    camera.rotation_euler = forward.to_track_quat('-Z', 'Y').to_euler()
    scene.view_layers[0].update()
    fit(scene)
    if not inspect(scene, side)['passed']:
        raise RuntimeError('Working shoulder is not on the camera side; choose a new viewpoint')


def require_report(report, scene_path, side, frames):
    samples = report.get('samples', [])
    values = [r.get('workingShoulderNearDepth', float('nan')) for r in samples]
    if not (report.get('passed') is True and report.get('sceneSHA256') == digest(scene_path)
            and report.get('validatorSHA256') == digest(__file__)
            and report.get('activeSide') == side and report.get('frames') == frames
            and [r.get('frame') for r in samples] == frames and values
            and all(isinstance(v, (int, float)) and math.isfinite(v) and v > MIN_NEAR_DEPTH for v in values)
            and report.get('minimumNearDepth') == min(values)):
        raise RuntimeError('Missing, stale or far-side working-arm camera evidence')


def geometry_digest(scene):
    """Full-loop evaluated surfaces, including equipment, for camera-only migration."""
    import bpy
    import numpy as np
    from collision_audit import mesh_data
    result = hashlib.sha256()
    previous = scene.frame_current
    for f in range(1, scene.frame_end + 2):
        scene.frame_set(f)
        for obj in sorted((o for o in scene.objects if o.type == 'MESH'), key=lambda o: o.name):
            points, faces = mesh_data(obj, bpy.context.evaluated_depsgraph_get())
            result.update(obj.name.encode())
            result.update(np.asarray(points, dtype='<f8').tobytes())
            result.update(np.asarray(faces, dtype='<i8').tobytes())
    scene.frame_set(previous)
    return result.hexdigest()


def main():
    import argparse
    import sys
    import bpy
    from library_exercises import LIBRARY_EXERCISES
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['reframe', 'audit'])
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--sex', required=True, choices=['male', 'female'])
    p.add_argument('--exercise', required=True)
    a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
    folder = a.root / 'docs/animation-library' / a.sex
    path = folder / (a.exercise + '.blend')
    bpy.ops.wm.open_mainfile(filepath=str(path.resolve()))
    scene = bpy.context.scene
    side = LIBRARY_EXERCISES[a.exercise]['unilateral']
    if a.mode == 'reframe':
        before_sha = digest(path)
        before = geometry_digest(scene)
        old_camera = [list(row) for row in scene.camera.matrix_world]
        aim(scene, side)
        after = geometry_digest(scene)
        assert before == after, 'Camera adjustment changed evaluated geometry'
        bpy.ops.wm.save_as_mainfile(filepath=str(path.resolve()))
        proof = dict(originalSceneSHA256=before_sha, sceneSHA256=digest(path), geometryBefore=before,
                     geometryAfter=after, frames=list(range(1, scene.frame_end + 2)),
                     oldCamera=old_camera, newCamera=[list(row) for row in scene.camera.matrix_world])
        (folder / (a.exercise + '-camera-change.json')).write_text(json.dumps(proof, indent=2) + '\n')
    report = inspect(scene, side)
    # Negative control: the original opposite view must fail the same real-scene check.
    original = scene.camera.matrix_world.copy()
    from mathutils import Vector
    forward = scene.camera.matrix_world.to_quaternion() @ Vector((0, 0, -1))
    forward.x *= -1
    scene.camera.rotation_euler = forward.to_track_quat('-Z', 'Y').to_euler()
    scene.view_layers[0].update()
    opposite = inspect(scene, side)
    scene.camera.matrix_world = original
    assert not opposite['passed'], 'Opposite-side negative control unexpectedly passed'
    report.update(sceneSHA256=digest(path), validatorSHA256=digest(__file__), oppositeSideRejected=True)
    (folder / (a.exercise + '-camera.json')).write_text(json.dumps(report, indent=2) + '\n')
    require_report(report, path, side, list(range(1, scene.frame_end + 2)))
    print('PASS working-side camera and opposite-side negative control', a.sex, a.exercise, flush=True)


if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    main()
