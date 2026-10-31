"""Human-reference preflight and scene-bound publication checks.

Legacy compatibility is frozen to exact scene + specification hashes. It never
allows a new bake without a reviewed reference. No function approves a review.
"""
import hashlib
import json
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from library_exercises import LIBRARY_EXERCISES

ROOT = Path(__file__).resolve().parents[2]
REFERENCES = ROOT / 'docs/motion-references'
PHASES = {'preparation', 'lifting', 'peak', 'return'}
PROFILE = 'upright_row_shoulder_height_v1'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def spec_digest(name):
    return hashlib.sha256(json.dumps(LIBRARY_EXERCISES[name], sort_keys=True).encode()).hexdigest()


def load_reference(name):
    path = REFERENCES / (name + '.json')
    try:
        ref = json.loads(path.read_text())
        c = LIBRARY_EXERCISES[name]
        assert ref['schemaVersion'] == 1 and ref['status'] == 'reviewed'
        assert ref['exercise'] == name and ref['exerciseId'] == c['id']
        assert ref['specificationSHA256'] == spec_digest(name)
        posture = ('supine' if c.get('press_type') == 'flat' else
                   'inclined' if c.get('press_type') == 'incline' else
                   'seated' if c.get('seated') else 'standing')
        assert ref['variant'] == dict(equipment=c.get('equipment','dumbbell'), posture=posture,
                                      loadedSides=[c['unilateral']] if c.get('unilateral') else ['Left','Right'], grip=c['grip'])
        assert ref['profile'] in (PROFILE, 'visual_reference_v1')
        if c['family'] == 'upright_row':
            assert ref['profile'] == PROFILE
        sources = {s['id']:s for s in ref['sources']}
        assert len(sources) == len(ref['sources']) and sources
        for s in sources.values():
            assert s['publisher'].strip() and s['url'].startswith('https://')
            assert s['accessedOn'] and s['use']['mode'] == 'public_player_observation'
            assert s['use']['redistributeMedia'] is False and s['use']['notes'].strip()
        stages = ref['observations']
        assert {p['phase'] for p in stages} == PHASES
        for p in stages:
            assert sources[p['sourceId']]['kind'] in ('human_video', 'human_photo')
            assert p['locator'].strip() and p['observed'].strip()
        assert ref['reviewer'].strip() and ref['reviewedOn'] and ref['decisions'].strip()
    except (OSError, ValueError, KeyError, TypeError, AssertionError) as e:
        raise RuntimeError(f'{name}: missing, pending, mismatched or incomplete human motion reference') from e
    return ref, digest(path)


def is_legacy(sex, name, scene):
    try:
        entry = json.loads((REFERENCES/'legacy-scenes.json').read_text())['scenes'][f'{sex}/{name}']
        return entry == dict(sceneSHA256=digest(scene), specificationSHA256=spec_digest(name))
    except (OSError, ValueError, KeyError):
        return False


def requires_audit(sex, name, root=ROOT):
    return not is_legacy(sex, name, root/f'docs/animation-library/{sex}/{name}.blend')


def row_violations(samples, frames, sides):
    """Numerical envelope selected for this demonstration, not human ROM limits."""
    failures = []
    if [(x.get('frame'),x.get('side')) for x in samples] != [(f,s) for f in frames for s in sides]:
        return ['incomplete_or_duplicate_samples']
    keys = ('elevation','elbowFlexion','wristBend','upperForward','foreDown',
            'foreInward','elbowAboveWrist','wristBelowShoulder','wristForward','elbowOutward')
    peak = 1 + (frames[-1]-1)//2
    for x in samples:
        if not all(isinstance(x.get(k),(int,float)) and math.isfinite(x[k]) for k in keys):
            failures.append(dict(frame=x.get('frame'),side=x.get('side'),check='non_finite_sample'))
            continue
        if not (0 <= x['elevation'] <= 90 and 0 <= x['elbowFlexion'] <= 145 and x['wristBend'] <= 15
                and x['upperForward'] >= -.02 and x['elbowOutward'] > 0):
            failures.append(dict(frame=x['frame'],side=x['side'],check='joint_envelope'))
        if x['frame']==peak and not (75<=x['elevation']<=90 and 90<=x['elbowFlexion']<=145
                and x['foreDown']>.2 and x['foreInward']>.35 and x['elbowAboveWrist']>.08
                and .08<x['wristBelowShoulder']<.28 and .08<x['wristForward']<.5):
            failures.append(dict(frame=x['frame'],side=x['side'],check='reference_peak'))
    return failures


def require_reference_pass(sex, name, root=ROOT, visual=True):
    folder = root/f'docs/animation-library/{sex}'
    scene = folder/f'{name}.blend'
    if is_legacy(sex, name, scene):
        return 'legacy_reference_review_pending'
    ref, sha = load_reference(name)
    try:
        a = json.loads((folder/f'{name}-reference-audit.json').read_text())
        frames = list(range(1,LIBRARY_EXERCISES[name].get('frames',120)+2))
        assert a['status']=='passed' and a['sceneSHA256']==digest(scene)
        assert a['referenceSHA256']==sha and a['specificationSHA256']==spec_digest(name)
        assert a['checkerSHA256']==digest(__file__) and a['frames']==frames
        assert a['profile']==ref['profile'] and a['failures']==[]
        if ref['profile']==PROFILE:
            assert not row_violations(a['samples'], frames, ref['variant']['loadedSides'])
        if visual:
            review = json.loads((folder/f'{name}-review.json').read_text())
            rr = review['motionReference']
            assert review['status']=='accepted' and review['sceneSHA256']==digest(scene)
            assert rr['referenceSHA256']==sha and rr['status']=='accepted' and rr['notes'].strip()
            assert {p['phase'] for p in rr['comparisons']}==PHASES
            assert len({p['frame'] for p in rr['comparisons']}) >= 4
            assert {'main','front','side'}.issubset(rr['views'])
            assert rr['evidence'] and all(review['evidence'].get(p)==h and digest(root/p)==h for p,h in rr['evidence'].items())
            for p in rr['comparisons']:
                assert p['frame'] in review['frames'] and p['notes'].strip()
                if ref['profile']==PROFILE:
                    assert p['frame']==dict(preparation=1,lifting=31,peak=61,**{'return':91})[p['phase']]
                assert any(o['phase']==p['phase'] and o['sourceId']==p['sourceId'] and o['locator']==p['locator'] for o in ref['observations'])
    except (OSError, ValueError, KeyError, TypeError, AssertionError) as e:
        raise RuntimeError(f'{sex}/{name}: missing, failed, partial or stale motion reference audit/review') from e
    return 'reference_checked'


def inspect(scene, ref, frames):
    import bpy
    from mathutils import Vector
    rig=next(o for o in scene.objects if o.type=='ARMATURE')
    samples=[]
    if ref['profile']==PROFILE:
        for f in frames:
            scene.frame_set(f)
            for side in ref['variant']['loadedSides']:
                sign=-1 if side=='Left' else 1
                p='mixamorig:'+side
                arm,fore,hand=[rig.pose.bones[p+x] for x in ('Arm','ForeArm','Hand')]
                shoulder,elbow,wrist=[rig.matrix_world@b.head for b in (arm,fore,hand)]
                u=(elbow-shoulder).normalized();v=(wrist-elbow).normalized()
                h=(rig.matrix_world.to_3x3()@(hand.tail-hand.head)).normalized()
                samples.append(dict(frame=f,side=side,elevation=math.degrees(u.angle(Vector((0,0,-1)))),
                    elbowFlexion=math.degrees(u.angle(v)),wristBend=math.degrees(v.angle(h)),
                    upperForward=u.y,foreDown=-v.z,foreInward=-sign*v.x,elbowAboveWrist=elbow.z-wrist.z,
                    wristBelowShoulder=shoulder.z-wrist.z,wristForward=wrist.y-shoulder.y,
                    elbowOutward=sign*(elbow.x-shoulder.x)))
        return samples,row_violations(samples,frames,ref['variant']['loadedSides'])
    return samples,[]


if __name__=='__main__':
    import argparse,sys,bpy
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--sex',choices=['male','female'],required=True)
    p.add_argument('--exercise',choices=list(LIBRARY_EXERCISES),required=True)
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    ref,sha=load_reference(a.exercise)
    folder=a.root/f'docs/animation-library/{a.sex}';scene=folder/f'{a.exercise}.blend'
    source_sha=digest(scene)
    bpy.ops.wm.open_mainfile(filepath=str(scene.resolve()))
    s=bpy.context.scene
    assert s['exercise']==a.exercise and s['sex']==a.sex
    assert s.frame_end==LIBRARY_EXERCISES[a.exercise].get('frames',120)
    frames=list(range(1,s.frame_end+2));samples,failures=inspect(s,ref,frames)
    assert digest(scene)==source_sha
    report=dict(status='failed' if failures else 'passed',sceneSHA256=source_sha,referenceSHA256=sha,
                specificationSHA256=spec_digest(a.exercise),checkerSHA256=digest(__file__),frames=frames,
                profile=ref['profile'],samples=samples,failures=failures)
    (folder/f'{a.exercise}-reference-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],failures=failures[:6])),flush=True)
    if failures:raise SystemExit(1)
