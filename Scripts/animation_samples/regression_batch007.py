"""In-memory counterexamples on real batch007 scenes; never saves a scene."""
import argparse,json,sys
from pathlib import Path
import bpy
from mathutils import Quaternion,Vector
sys.path.insert(0,str(Path(__file__).parent))
from library_audit_v7 import inspect
from library_exercises import LIBRARY_EXERCISES
from library_gate import digest,validator_hashes
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--sex',required=True);p.add_argument('--exercise',required=True);p.add_argument('--previous-root',type=Path)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);c=LIBRARY_EXERCISES[a.exercise];assert c['audit_version']==7
source=a.root/f'docs/animation-library/{a.sex}/{a.exercise}.blend';sha=digest(source)
previous=None
if a.previous_root:
 old=a.previous_root/f'docs/animation-library/{a.sex}/{a.exercise}.blend'
 bpy.ops.wm.open_mainfile(filepath=str(old));s=bpy.context.scene
 prior=inspect(s,c,list(range(1,s.frame_end+2)))
 check='free_arm_flared' if c['family']=='curl' else 'kickback_upper_arm_flared'
 hits=[x for x in prior['failures'] if x['check']==check];assert hits
 previous=dict(sceneSHA256=digest(old),expectedRejection=check,matchedFailures=hits)
bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
if c['family']=='kickback':
 s.frame_set(145);b=rig.pose.bones['mixamorig:RightForeArm'];q=b.rotation_quaternion.copy()
 s.frame_set(49);b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=49)
 expected='inactive_arm_extended';mutation='Right forearm is extended during the left-side repetition (frame 49).'
else:
 s.frame_set(61);b=rig.pose.bones['mixamorig:LeftArm'];b.rotation_quaternion=Quaternion(Vector((1,0,0)),.65)@b.rotation_quaternion;b.keyframe_insert('rotation_quaternion',frame=61)
 expected='curl_elbow_moved';mutation='Loaded upper arm swings at peak (frame 61), instead of retaining a fixed elbow.'
bpy.context.view_layer.update()
result=inspect(s,c,list(range(1,s.frame_end+2)));hits=[v for v in result['failures'] if v['check']==expected]
assert hits,(expected,result['failures']);assert digest(source)==sha
out=dict(status='passed',sceneSHA256=sha,validatorSHA256=validator_hashes(a.exercise),mutation=mutation,expectedRejection=expected,matchedFailures=hits,sourceUnchanged=True,previousRejectedCandidate=previous)
(source.parent/f'{a.exercise}-regression.json').write_text(json.dumps(out,indent=2)+'\n');print('Rejected real-scene counterexample',expected,flush=True)
