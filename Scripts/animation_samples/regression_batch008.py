"""Real-scene negative controls for bilateral curl motion and grip; never saves."""
import argparse,json,sys
from pathlib import Path
import bpy
from mathutils import Quaternion,Vector
sys.path.insert(0,str(Path(__file__).parent))
from library_audit_v8 import inspect
from library_exercises import LIBRARY_EXERCISES
from library_gate import digest,validator_hashes
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--sex',required=True);p.add_argument('--exercise',required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);c=LIBRARY_EXERCISES[a.exercise];assert c['audit_version']==8
source=a.root/f'docs/animation-library/{a.sex}/{a.exercise}.blend';sha=digest(source);results=[]
for mutation,expected in [('upper_arm_swing','curl_elbow_moved'),('one_arm_waiting','bilateral_desynchronized'),('wrong_grip','grip_or_wrist')]:
 bpy.ops.wm.open_mainfile(filepath=str(source.resolve()));s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
 if mutation=='wrong_grip':
  config=dict(c,grip='pronated' if c['grip']=='supinated' else 'supinated')
 else:
  config=c
  if mutation=='upper_arm_swing':
   s.frame_set(61);b=rig.pose.bones['mixamorig:LeftArm'];b.rotation_quaternion=Quaternion(Vector((1,0,0)),.65)@b.rotation_quaternion
  else:
   s.frame_set(1);b=rig.pose.bones['mixamorig:RightForeArm'];q=b.rotation_quaternion.copy();s.frame_set(61);b.rotation_quaternion=q
  b.keyframe_insert('rotation_quaternion',frame=61);bpy.context.view_layer.update()
 result=inspect(s,config,[1,31,61,91,121]);hits=[v for v in result['failures'] if v['check']==expected];assert hits,(mutation,result['failures'])
 results.append(dict(mutation=mutation,expectedRejection=expected,matchedFailures=hits))
assert digest(source)==sha
(source.parent/f'{a.exercise}-regression.json').write_text(json.dumps(dict(status='passed',sceneSHA256=sha,validatorSHA256=validator_hashes(a.exercise),controls=results,sourceUnchanged=True),indent=2)+'\n')
print('PASS three real-scene negative controls',a.sex,a.exercise,flush=True)
