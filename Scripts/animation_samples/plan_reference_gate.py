"""Scene-bound human-reference review for the original plan and three samples.

This complements collision/deformation gates. Numerical continuity checks do
not approve a human movement; the separate, hash-bound visual decision does.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from exercise_catalog import EXERCISES
from plan_exercises import PLAN_EXERCISES

ROOT = Path(__file__).resolve().parents[2]
CATALOG = {**EXERCISES, **PLAN_EXERCISES}
PHASES = ('preparation', 'lifting', 'peak', 'return')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def specification_digest(name):
    return hashlib.sha256(json.dumps(CATALOG[name], sort_keys=True).encode()).hexdigest()


def folder(root, sex, name):
    collection = 'animation-plan-v3' if name in PLAN_EXERCISES else 'animation-samples-v2'
    return root / 'docs' / collection / sex


def load_reference(name):
    path = ROOT / 'docs/motion-references' / (name + '.json')
    try:
        ref = json.loads(path.read_text())
        assert ref['schemaVersion'] == 1 and ref['status'] == 'reviewed'
        assert ref['profile'] == 'plan_visual_reference_v1'
        assert ref['exercise'] == name and ref['exerciseId'] == CATALOG[name]['id']
        assert ref['specificationSHA256'] == specification_digest(name)
        assert all(ref['variant'][k] for k in ('equipment', 'posture', 'grip', 'support'))
        sources = {s['id']: s for s in ref['sources']}
        assert sources and len(sources) == len(ref['sources'])
        for source in sources.values():
            assert source['publisher'].strip() and source['url'].startswith('https://')
            assert source['kind'] in ('human_video', 'human_photo') and source['accessedOn']
            assert source['use']['mode'] == 'public_player_observation'
            assert source['use']['redistributeMedia'] is False and source['use']['notes'].strip()
        assert len(ref['observations']) == 4
        assert {p['phase'] for p in ref['observations']} == set(PHASES)
        assert all(p['sourceId'] in sources and p['locator'].strip() and p['observed'].strip()
                   for p in ref['observations'])
        assert ref['decisions'].strip() and ref['reviewer'].strip() and ref['reviewedOn']
    except (OSError, KeyError, TypeError, ValueError, AssertionError) as error:
        raise RuntimeError(f'{name}: missing or incomplete plan motion reference') from error
    return ref, digest(path)


def require_pass(sex, name, root=ROOT, visual=True):
    ref, reference_sha = load_reference(name)
    base = folder(root, sex, name)
    scene = base / f'{name}.blend'
    count = CATALOG[name].get('frames', 120)
    frames = list(range(1, count + 2))
    try:
        audit = json.loads((base / f'{name}-reference-audit.json').read_text())
        assert audit['status'] == 'passed' and audit['failures'] == []
        assert audit['sceneSHA256'] == digest(scene)
        assert audit['checkerSHA256'] == digest(__file__)
        assert audit['specificationSHA256'] == specification_digest(name)
        assert audit['referenceSHA256'] == reference_sha and audit['frames'] == frames
        if visual:
            review = json.loads((base / f'{name}-reference-review.json').read_text())
            assert review['status'] == 'accepted' and review['notes'].strip()
            assert review['sceneSHA256'] == digest(scene) and review['referenceSHA256'] == reference_sha
            assert {'main', 'front', 'side'}.issubset(review['views'])
            assert len(review['comparisons']) == 4
            assert {p['phase'] for p in review['comparisons']} == set(PHASES)
            expected = ([61,91,1,31] if name == 'incline_press' else
                        [1,25,49,73] if name == 'dead_bug' else [1,31,61,91])
            assert {p['phase']: p['frame'] for p in review['comparisons']} == dict(zip(PHASES, expected))
            assert review['evidence'] and all(digest(root / p) == sha for p, sha in review['evidence'].items())
            for p in review['comparisons']:
                assert p['frame'] in review['frames'] and p['frame'] in frames and p['notes'].strip()
                assert any(o['phase'] == p['phase'] and o['sourceId'] == p['sourceId']
                           and o['locator'] == p['locator'] for o in ref['observations'])
    except (OSError, KeyError, TypeError, ValueError, AssertionError) as error:
        raise RuntimeError(f'{sex}/{name}: missing, failed or stale plan reference evidence') from error
    return audit


def inspect(scene, name):
    """Check the authored cycle, preserving the separate human-review boundary."""
    import bpy
    from mathutils import Vector
    rig = next(o for o in scene.objects if o.type == 'ARMATURE')
    names = [b.name for b in rig.data.bones if b.name.startswith('mixamorig:')
             and not any(x in b.name for x in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky'))]
    first, previous, samples, failures = {}, {}, [], []
    frames = list(range(1, scene.frame_end + 2))
    for f in frames:
        scene.frame_set(f)
        if name in ('row', 'cable_crunch', 'leg_press', 'pulldown', 'straight_pulldown', 'dead_bug'):
            hips = rig.matrix_world @ rig.pose.bones['mixamorig:Hips'].head
            first.setdefault('hips', hips.copy())
            if (hips-first['hips']).length > .005:
                failures.append(dict(frame=f, check='support_pelvis_drift'))
            grips = ([scene.objects['Cable handle'].matrix_world.translation.copy()]
                     if name == 'row' else
                     [scene.objects['Grip.'+side].matrix_world.translation.copy()
                      for side in ('Left','Right')] if name == 'cable_crunch' else [])
            center = sum(grips, Vector())/len(grips) if grips else hips
            first.setdefault('grip_center', center.copy())
            if name == 'row' and f == 1+scene.frame_end//2:
                if center.z-hips.z > .28 or center.y-hips.y > .30:
                    failures.append(dict(frame=f, check='row_not_to_abdomen'))
                if (center-first['grip_center']).length < .28:
                    failures.append(dict(frame=f, check='row_short_stroke'))
            if name == 'cable_crunch':
                spine = rig.pose.bones['mixamorig:Spine2']
                up = (rig.matrix_world.to_3x3()
                      @ (spine.matrix @ spine.bone.matrix_local.inverted()).to_3x3()
                      @ Vector((0,0,1))).normalized()
                lean = math.degrees(math.atan2(up.y, up.z))
                head = rig.matrix_world @ rig.pose.bones['mixamorig:Head'].head
                if max((g-head).length for g in grips) > .36:
                    failures.append(dict(frame=f, check='crunch_hands_far_from_head'))
                if (f in (1, scene.frame_end+1) and not 25 <= lean <= 45
                        or f == 1+scene.frame_end//2 and not 55 <= lean <= 80):
                    failures.append(dict(frame=f, check='crunch_thorax_range', lean=lean))
        # Shared sled/pelvis leaves unequal imported limb lengths with different
        # flexion: selected visuals use 20–36° at press top and 18–38° in RDL.
        # The 40° envelope is an authored regression bound, not a clinical limit.
        if name in ('leg_press', 'rdl'):
            for side in ('Left', 'Right'):
                h, k, a = [rig.matrix_world @ rig.pose.bones['mixamorig:'+side+b].head
                           for b in ('UpLeg', 'Leg', 'Foot')]
                knee_flex = math.degrees((k-h).angle(a-k))
                if name == 'rdl' and not 10 <= knee_flex <= 40:
                    failures.append(dict(frame=f, side=side, check='rdl_not_soft_knee', degrees=knee_flex))
                if name == 'leg_press' and (
                        f in (1, scene.frame_end+1) and not 10 <= knee_flex <= 40
                        or f == 1+scene.frame_end//2 and not 75 <= knee_flex <= 115):
                    failures.append(dict(frame=f, side=side, check='leg_press_knee_range', degrees=knee_flex))
                if name == 'rdl':
                    first.setdefault(side+'_foot', a.copy())
                    if (a-first[side+'_foot']).length > .005:
                        failures.append(dict(frame=f, side=side, check='rdl_foot_drift'))
            if name == 'rdl' and f == 1+scene.frame_end//2:
                spine = rig.pose.bones['mixamorig:Spine2']
                up = (rig.matrix_world.to_3x3() @ (spine.matrix @ spine.bone.matrix_local.inverted()).to_3x3() @ Vector((0,0,1))).normalized()
                lean = math.degrees(math.atan2(up.y, up.z))
                if not 55 <= lean <= 70:
                    failures.append(dict(frame=f, check='rdl_incomplete_hinge', degrees=lean))
        for bone_name in names:
            bone = rig.pose.bones[bone_name]
            head, tail = rig.matrix_world @ bone.head, rig.matrix_world @ bone.tail
            rotation = (rig.matrix_world @ bone.matrix).to_quaternion().normalized()
            if not all(math.isfinite(v) for v in (*head, *tail, *rotation)):
                failures.append(dict(frame=f, bone=bone_name, check='non_finite_pose'))
                continue
            length = (tail-head).length
            first.setdefault(bone_name, (head.copy(), tail.copy(), length))
            if abs(length-first[bone_name][2]) > 1e-4:
                failures.append(dict(frame=f, bone=bone_name, check='bone_length_changed'))
            if bone_name in previous:
                distance = max((head-previous[bone_name][0]).length, (tail-previous[bone_name][1]).length)
                angle = math.degrees(2*math.acos(min(1, abs(rotation.dot(previous[bone_name][2])))))
                if distance > .10 or angle > 35:
                    failures.append(dict(frame=f, bone=bone_name, check='pose_discontinuity', distance=distance, angle=angle))
            if f == frames[-1] and max((head-first[bone_name][0]).length, (tail-first[bone_name][1]).length) > 1e-4:
                failures.append(dict(frame=f, bone=bone_name, check='cycle_not_closed'))
            previous[bone_name] = (head.copy(), tail.copy(), rotation.copy())
        for side in ('Left', 'Right'):
            arm, fore, hand = [rig.pose.bones['mixamorig:'+side+p] for p in ('Arm', 'ForeArm', 'Hand')]
            shoulder, elbow, wrist = [rig.matrix_world @ b.head for b in (arm, fore, hand)]
            u, v = (elbow-shoulder).normalized(), (wrist-elbow).normalized()
            sample = dict(frame=f, side=side, shoulderElevationDegrees=math.degrees(u.angle(Vector((0,0,-1)))),
                          elbowFlexionDegrees=math.degrees(u.angle(v)))
            samples.append(sample)
            flexion = sample['elbowFlexionDegrees']
            elevation = sample['shoulderElevationDegrees']
            at_start = f in (1, scene.frame_end+1)
            at_peak = f == 1+scene.frame_end//2
            if name == 'row' and at_start and flexion > 40:
                failures.append(dict(frame=f, side=side, check='row_incomplete_reach', degrees=flexion))
            if name == 'pushdown' and (elevation > 25 or not 8 <= flexion <= 105
                    or at_start and not 95 <= flexion <= 105 or at_peak and flexion > 20):
                failures.append(dict(frame=f, side=side, check='pushdown_arm_range'))
            if name == 'straight_pulldown' and not 10 <= flexion <= 20:
                failures.append(dict(frame=f, side=side, check='straight_pulldown_bending_elbow', degrees=flexion))
            if name == 'pulldown' and (at_start and not 15 <= flexion <= 30
                    or at_peak and not 95 <= flexion <= 120):
                failures.append(dict(frame=f, side=side, check='pulldown_arm_range', degrees=flexion))
            if name == 'curl':
                elevation, flexion = sample['shoulderElevationDegrees'], sample['elbowFlexionDegrees']
                if not (0 <= elevation <= 25 and 10 <= flexion <= 125):
                    failures.append(dict(frame=f, side=side, check='curl_envelope'))
                if f in (1, scene.frame_end+1) and flexion > 30:
                    failures.append(dict(frame=f, side=side, check='curl_incomplete_return'))
                if f == 1+scene.frame_end//2 and not 100 <= flexion <= 120:
                    failures.append(dict(frame=f, side=side, check='curl_incomplete_peak'))
    return frames, samples, failures


def main():
    import bpy
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=ROOT)
    p.add_argument('--sex', required=True, choices=['male', 'female'])
    p.add_argument('--exercise', required=True, choices=list(CATALOG))
    a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    ref, sha = load_reference(a.exercise)
    base = folder(a.root, a.sex, a.exercise)
    source = base / f'{a.exercise}.blend'
    source_sha = digest(source)
    bpy.ops.wm.open_mainfile(filepath=str(source.resolve()))
    scene = bpy.context.scene
    assert scene.frame_end == CATALOG[a.exercise].get('frames', 120)
    frames, samples, failures = inspect(scene, a.exercise)
    assert digest(source) == source_sha
    output = dict(status='failed' if failures else 'passed', sceneSHA256=source_sha,
                  referenceSHA256=sha, specificationSHA256=specification_digest(a.exercise),
                  checkerSHA256=digest(__file__), frames=frames, samples=samples, failures=failures)
    (base / f'{a.exercise}-reference-audit.json').write_text(json.dumps(output, indent=2)+'\n')
    print(json.dumps(dict(exercise=a.exercise, sex=a.sex, frames=len(frames), failures=len(failures))))
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
