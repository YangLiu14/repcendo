"""Real Blender scene mutations must fail independently of report metadata."""
import sys,argparse
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).parent))
from verify_equipment_refit import inspect
parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2]);args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []);r=args.root.resolve()
p=r/'docs/animation-plan-v3/male/leg_press.blend'
bpy.ops.wm.open_mainfile(filepath=str(p));s=bpy.context.scene
assert inspect(s)[0]==[]
o=s.objects['Sled guide -1'];o.keyframe_insert('location',frame=1);o.location.z+=.02;o.keyframe_insert('location',frame=61)
assert any('fixed_drift' in f for f in inspect(s)[0])
bpy.ops.wm.open_mainfile(filepath=str(p));s=bpy.context.scene;o=s.objects['Sled footplate'];s.frame_set(61);o.location.y+=.02;o.keyframe_insert('location',frame=61)
assert any('slide_error' in f for f in inspect(s)[0])
p=r/'docs/animation-plan-v3/male/pushdown.blend';bpy.ops.wm.open_mainfile(filepath=str(p));s=bpy.context.scene;assert inspect(s)[0]==[]
o=s.objects['EQ selected plate 0'];o.animation_data_clear();o.location.z=.13
assert any('cable_error' in f for f in inspect(s)[0])
print('PASS: actual drifting rail, off-axis footplate and static load rejected; two originals accepted')
