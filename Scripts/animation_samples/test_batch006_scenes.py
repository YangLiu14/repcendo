"""Real-scene positive/negative controls; mutations stay in Blender memory."""
import argparse,sys,json
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).parent))
from library_exercises import LIBRARY_EXERCISES
from library_audit_v6 import inspect
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
records=[]
def check(name,sex='male',change=None):
    path=a.root/f'docs/animation-library/{sex}/{name}.blend'
    bpy.ops.wm.open_mainfile(filepath=str(path.resolve()));scene=bpy.context.scene
    if change:change(scene)
    return inspect(scene,LIBRARY_EXERCISES[name],[1,31,61,91,121])['failures']
def freeze(scene):
    scene.frame_set(1)
    rig=next(o for o in scene.objects if o.type=='ARMATURE');rig.animation_data_clear()
def move_idle(scene):
    scene.frame_set(61);rig=next(o for o in scene.objects if o.type=='ARMATURE')
    b=rig.pose.bones['mixamorig:RightForeArm'];b.location.x+=.05;b.keyframe_insert('location',frame=61)
def stretch(scene):
    o=scene.objects['Dumbbell plate Left'];o.keyframe_insert('scale',frame=1);o.scale.x*=1.5;o.keyframe_insert('scale',frame=61)
def remove_leg(scene):bpy.data.objects.remove(scene.objects['Bench leg -0.83'],do_unlink=True)
def remove_refinement(scene):
    body=next(o for o in scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers));del body['limb_shape_report']
def detach_beam(scene):scene.objects['Bench longitudinal frame'].location.z-=.03
for name,c in LIBRARY_EXERCISES.items():
    if c['batch']=='006':
        for sex in ['male','female']:
            errors=check(name,sex);assert not errors,(name,sex,errors[:2]);records.append(dict(name=name,sex=sex,positive=True,passed=True))
for name,change,expected in [
    ('db_kickback',freeze,'extension_range'),('overhead_front_raise',freeze,'missing_overhead_range'),
    ('single_kickback',move_idle,'unloaded_arm_moved'),('db_upright_row',stretch,'nonrigid_or_moving_support'),
    ('seated_kickback',remove_leg,'missing_bench_support'),('seated_kickback',detach_beam,'bench_beam_detached'),
    ('db_kickback',remove_refinement,'missing_limb_refinement')]:
    errors=check(name,change=change);assert expected in {e['check'] for e in errors},(name,expected,errors[:2]);records.append(dict(name=name,positive=False,rejected=True,expected=expected))
out=a.root/'docs/animation-library/batch-006-scene-controls.json';out.write_text(json.dumps(records,indent=2)+'\n')
print('PASS: 16 real scene controls and 7 rejected mutations')
