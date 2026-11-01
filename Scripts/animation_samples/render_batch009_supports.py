"""Render actual arm/thigh support closeups; never accepts the scene."""
import bpy,json,sys,argparse
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from library_gate import digest
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--sex',required=True);p.add_argument('--exercise',choices=['concentration_curl'],required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
source=a.root/f'docs/animation-library/{a.sex}/concentration_curl.blend';sha=digest(source)
bpy.ops.wm.open_mainfile(filepath=str(source.resolve()));s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
s.render.resolution_x=s.render.resolution_y=480;s.render.resolution_percentage=100;s.eevee.taa_render_samples=16
out=a.root/f'build/animation-library/{a.sex}/concentration_curl/support-review';out.mkdir(parents=True,exist_ok=True)
frames=[1,31,61,91]
for f in frames:
 s.frame_set(f)
 for view,part,offset in [('left_support','LeftForeArm',(1.5,4,1.5)),('right_forearm','RightForeArm',(4,3,3))]:
  target=rig.matrix_world@rig.pose.bones['mixamorig:'+part].head
  s.camera.location=target+Vector(offset);s.camera.rotation_euler=(target-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=.55
  s.render.filepath=str((out/f'{view}-{f:03d}.png').resolve());bpy.ops.render.render(write_still=True)
(out/'source.json').write_text(json.dumps(dict(sceneSHA256=sha,views=['left_support','right_forearm'],frames=frames),indent=2)+'\n')
