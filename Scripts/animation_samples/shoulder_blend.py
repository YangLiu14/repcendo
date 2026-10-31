"""Bake a local DQ-to-linear correction at the torso/shoulder weight boundary.

The Armature remains DQ. Pure arm, elbow, wrist and finger weights are retained;
only the mixed shoulder-girdle surface uses the linear target. This addresses
DQ's large-rotation bulge without smoothing the mesh or moving bone targets.
Every generated scene still requires collision/deformation and visual review.
"""
import hashlib
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from skin_matrix import blend_rigid

VERSION='shoulder-blend-1'


def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1)
    return t*t*(3-2*t)


def bake(scene,body,rig,step=4,strength=1.0):
    if not 0 < strength <= 1:
        raise ValueError('Shoulder blend strength must be in (0, 1]')
    if body.get('shoulder_blend_version'):
        raise ValueError('Shoulder blend already baked')
    rest=np.array([v.co[:] for v in body.data.vertices]);z=rest[:,2];y=np.abs(rest[:,1])
    weights=[];mask=[]
    for v in body.data.vertices:
        row=[(body.vertex_groups[g.group].name,g.weight) for g in v.groups
             if g.weight>0 and body.vertex_groups[g.group].name in rig.data.bones
             and rig.data.bones[body.vertex_groups[g.group].name].use_deform]
        weights.append(row)
        trunk=sum(w for n,w in row if n.startswith('mixamorig:Spine'))
        girdle=sum(w for n,w in row if n.endswith('Shoulder'))
        upper=sum(w for n,w in row if n.endswith('Arm'))
        mask.append(float(smooth(.001,.025,max(trunk*(girdle+upper),girdle*upper))))
    mask=np.array(mask)*smooth(.58,.63,z)*(1-smooth(.81,.85,z))*smooth(.015,.035,y)*(1-smooth(.18,.21,y))
    mask *= strength
    ids=np.flatnonzero(mask>1e-6)
    end=scene.frame_end
    assert end%step==0
    corrections=[];maximum=0
    for frame in range(1,end+1,step):
        scene.frame_set(frame)
        matrices={p.name:p.matrix@p.bone.matrix_local.inverted() for p in rig.pose.bones}
        delta=np.zeros_like(rest)
        for i in ids:
            row=weights[i];dq=blend_rigid(matrices,row);point=Vector(rest[i]);linear=Vector((0,0,0));total=sum(w for _,w in row)
            for name,w in row:linear+=(matrices[name]@point)*(w/total)
            delta[i]=(dq.to_3x3().transposed()@(linear-dq@point))*float(mask[i])
        maximum=max(maximum,float(np.linalg.norm(delta,axis=1).max()))
        corrections.append((frame,delta))
    if not body.data.shape_keys:body.shape_key_add(name='Basis')
    for frame,delta in corrections:
        key=body.shape_key_add(name=f'ShoulderBlend.{frame:03d}')
        key.data.foreach_set('co',(rest+delta).ravel())
        values={1:0.,end+1:0.,frame:1.}
        if frame>1:values[frame-step]=0.
        if frame+step<=end+1:values[frame+step]=0.
        if frame==1:values.update({1:1.,end+1:1.,end+1-step:0.})
        for f,value in sorted(values.items()):key.value=value;key.keyframe_insert('value',frame=f)
    action=body.data.shape_keys.animation_data.action
    for layer in action.layers:
        for strip in layer.strips:
            for slot in action.slots:
                bag=strip.channelbag(slot)
                if bag:
                    for curve in bag.fcurves:
                        for k in curve.keyframe_points:k.interpolation='LINEAR'
    body['shoulder_blend_version']=VERSION
    body['shoulder_blend_strength']=strength
    body['shoulder_blend_recipe_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    scene.frame_set(1)
    return dict(version=VERSION,strength=strength,vertices=len(ids),samples=len(corrections),maxModelDisplacement=maximum,requiresFullFrameAndVisualReview=True)
