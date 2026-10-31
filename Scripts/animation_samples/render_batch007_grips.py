"""Supplementary unobstructed grip views; writes evidence, never approval."""
import sys,argparse,json,hashlib
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from library_exercises import LIBRARY_EXERCISES
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--sex',required=True);p.add_argument('--exercise',required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);c=LIBRARY_EXERCISES[a.exercise];assert c['batch']=='007'
source=a.root/f'docs/animation-library/{a.sex}/{a.exercise}.blend';sha=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source.resolve()));scene=bpy.context.scene
folder=a.root/f'build/animation-library/{a.sex}/{a.exercise}/grip-review';folder.mkdir(parents=True,exist_ok=True)
sides=[c['unilateral']] if c.get('unilateral') else ['Left','Right'];frames=([1,25,49,73,97,121,145,169,31,61] if c.get("alternating") else [1,31,61])
scene.render.resolution_x=scene.render.resolution_y=480;scene.render.resolution_percentage=100;scene.eevee.taa_render_samples=16
for f in frames:
 scene.frame_set(f)
 for side in sides:
  target=scene.objects['Grip.'+side].matrix_world.translation.copy();s=-1 if side=='Left' else 1
  offset=Vector((s*4,-4 if c['family']=='kickback' else 4,2))
  scene.camera.location=target+offset;scene.camera.rotation_euler=(target-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.ortho_scale=.48
  scene.render.filepath=str((folder/f'{side}-{f:03d}.png').resolve());bpy.ops.render.render(write_still=True)
(folder/'source.json').write_text(json.dumps(dict(sceneSHA256=sha,sides=sides,frames=frames),indent=2)+'\n')
