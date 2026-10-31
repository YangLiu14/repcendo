"""Compare real before/after scenes for the reported lateral rib-cage bulge.

These are character-specific regression measurements, not anatomical standards.
Requires the saved original scenes in build/limb-repair/baseline.
"""
import bpy,numpy as np
from pathlib import Path

def measure(path):
    bpy.ops.wm.open_mainfile(filepath=str(path.resolve()))
    scene=bpy.context.scene;scene.frame_set(61)
    rig=next(o for o in scene.objects if o.type=='ARMATURE')
    body=next(o for o in scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers))
    rest=np.array([v.co[:] for v in body.data.vertices])
    evaluated=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
    q=np.array([v.co[:] for v in mesh.vertices]);evaluated.to_mesh_clear()
    bone=rig.pose.bones['mixamorig:Spine2'];inv=np.array((bone.matrix@bone.bone.matrix_local.inverted()).inverted())
    q=q@inv[:3,:3].T+inv[:3,3]
    mask=(rest[:,2]>.63)&(rest[:,2]<.70)&(rest[:,1]>.06)&(rest[:,1]<.105)
    return float(np.percentile(np.maximum(0,q[:,1]-rest[:,1])[mask],95))

for sex in ['male','female']:
    before=measure(Path(f'build/limb-repair/baseline/{sex}-single_overhead_press.blend'))
    after=measure(Path(f'build/limb-repair/candidate/docs/animation-library/{sex}/single_overhead_press.blend'))
    assert before>.07,'Baseline no longer reproduces the reported bulge'
    assert after<before*.60,'Side-chest expansion must decrease by at least 40%'
    print('PASS',sex,'rib-cage expansion p95',before,'->',after)
