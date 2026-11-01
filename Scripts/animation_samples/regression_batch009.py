"""Mutate real candidate scenes in memory to check motion/support gate failures."""
import argparse,json,sys
from pathlib import Path
import bpy
from mathutils import Quaternion,Vector
sys.path.insert(0,str(Path(__file__).parent))
from library_audit_v9 import inspect
from library_exercises import LIBRARY_EXERCISES
from library_gate import digest,validator_hashes
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--sex',required=True);p.add_argument('--exercise',required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);c=LIBRARY_EXERCISES[a.exercise];assert c['audit_version']==9
source=a.root/f'docs/animation-library/{a.sex}/{a.exercise}.blend';sha=digest(source);results=[]
controls=[('upper_arm_swing','curl_elbow_moved'),('seat_removed','missing_bench_support'),('wrong_grip','grip_or_wrist')]
if c.get('thigh_support'):controls.append(('support_leg_displaced','arm_thigh_support_missing'))
else:controls.append(('one_arm_waiting','bilateral_desynchronized'))
for mutation,expected in controls:
 bpy.ops.wm.open_mainfile(filepath=str(source.resolve()));s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');config=c
 if mutation=='wrong_grip':config=dict(c,grip='pronated')
 elif mutation=='seat_removed':bpy.data.objects.remove(s.objects['Bench leg -0.83'],do_unlink=True)
 else:
  s.frame_set(61)
  if mutation=='upper_arm_swing':
   b=rig.pose.bones['mixamorig:LeftArm'];b.rotation_quaternion=Quaternion(Vector((1,0,0)),.65)@b.rotation_quaternion
  elif mutation=='support_leg_displaced':
   b=rig.pose.bones['mixamorig:LeftUpLeg'];b.rotation_quaternion=Quaternion(Vector((0,1,0)),.70)@b.rotation_quaternion
  else:
   s.frame_set(1);b=rig.pose.bones['mixamorig:RightForeArm'];q=b.rotation_quaternion.copy();s.frame_set(61);b.rotation_quaternion=q
  b.keyframe_insert('rotation_quaternion',frame=61);bpy.context.view_layer.update()
 result=inspect(s,config,[1,31,61,91,121]);hits=[v for v in result['failures'] if v['check']==expected];assert hits,(mutation,result['failures'])
 results.append(dict(mutation=mutation,expectedRejection=expected,matchedFailures=hits))
assert digest(source)==sha
(source.parent/f'{a.exercise}-regression.json').write_text(json.dumps(dict(status='passed',sceneSHA256=sha,validatorSHA256=validator_hashes(a.exercise),controls=results,sourceUnchanged=True),indent=2)+'\n')
print('PASS four real-scene negative controls',a.sex,a.exercise,flush=True)
