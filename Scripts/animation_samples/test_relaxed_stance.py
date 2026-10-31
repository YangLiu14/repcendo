"""Regression: quiet standing exercises must not inherit a quarter-squat stance.

Run with Blender -- --scene path; intentionally rejects the old single curl.
"""
import argparse,sys,math,json
from pathlib import Path
import bpy
p=argparse.ArgumentParser();p.add_argument('--scene',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);bpy.ops.wm.open_mainfile(filepath=str(a.scene.resolve()))
r=next(o for o in bpy.data.objects if o.type=='ARMATURE');s=bpy.context.scene;values=[]
for f in [1,(s.frame_end//2)+1,s.frame_end+1]:
 s.frame_set(f)
 for side in ['Left','Right']:
  a=r.pose.bones['mixamorig:'+side+'UpLeg'];b=r.pose.bones['mixamorig:'+side+'Leg'];angle=math.degrees((a.tail-a.head).angle(b.tail-b.head));values.append(angle)
print(json.dumps(dict(minKneeFlexion=min(values),maxKneeFlexion=max(values))))
assert min(values)>=3 and max(values)<=15,'Relaxed standing knee must stay within 3–15 degrees'
