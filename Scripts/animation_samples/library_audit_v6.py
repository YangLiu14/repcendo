"""Batch 006 independent evaluated-surface, loading and motion intent checks."""
import math
import bpy
import numpy as np
from mathutils import Vector
from collision_audit import mesh_data


def inspect(scene, config, frames):
    assert config['audit_version']==6
    family=config['family']
    assert family in ('kickback','bent_lateral','overhead_raise','upright_row')
    rig=next(o for o in scene.objects if o.type=='ARMATURE')
    body=next(o for o in scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers))
    active=[config['unilateral']] if config.get('unilateral') else ['Left','Right']
    groups={g.index:g.name for g in body.vertex_groups}
    ids={};digits={};stable={}
    for side in active:
        prefix='mixamorig:'+side+'Hand'
        weights={v.index:sum(g.weight for g in v.groups if groups[g.group].startswith(prefix)) for v in body.data.vertices}
        ids[side]=[i for i,w in weights.items() if w>.65];stable[side]=[i for i,w in weights.items() if w>.9999]
        for digit in ('Thumb','Index','Middle','Ring','Pinky'):
            digits[side,digit]=[v.index for v in body.data.vertices if sum(g.weight for g in v.groups if groups[g.group].startswith(prefix+digit))>.7]
    failures=[];samples=[];supports=[];first={};maxfoot=loop=0
    def fail(check,**data):failures.append(dict(check=check,**data))
    if not body.get('limb_shape_report'):fail('missing_limb_refinement')
    if not body.get('shoulder_blend_version'):fail('missing_shoulder_recipe')
    expected={name for side in active for name in ('Grip shaft '+side,'Dumbbell plate '+side,'Dumbbell plate '+side+'.001')}
    actual={o.name for o in scene.objects if o.name.startswith(('Grip shaft','Dumbbell plate'))}
    if actual!=expected:fail('incorrect_loaded_sides',actual=sorted(actual))
    if config.get('unilateral'):
        keys=body.data.shape_keys.key_blocks
        if keys['Right_Grip_Clearance'].value!=0:fail('unloaded_hand_corrective')
    support_ids=[v.index for v in body.data.vertices if any(g.weight>.4 and any(n in groups[g.group] for n in ('Hips','UpLeg')) for g in v.groups)]
    feet=[v.index for v in body.data.vertices if v.co.z<.025]
    for f in frames:
        scene.frame_set(f);points,_=mesh_data(body,bpy.context.evaluated_depsgraph_get())
        if not np.isfinite(points).all():fail('non_finite_mesh',frame=f)
        first.setdefault('mesh',points.copy())
        maxfoot=max(maxfoot,float(np.linalg.norm(points[feet]-first['mesh'][feet],axis=1).max()))
        if f==scene.frame_end+1:loop=float(np.linalg.norm(points-first['mesh'],axis=1).max())
        trunk=np.array([tuple(rig.matrix_world@rig.pose.bones['mixamorig:'+p].head) for p in ('Hips','Spine','Spine1','Spine2','Head')]);first.setdefault('trunk',trunk.copy())
        if np.linalg.norm(trunk-first['trunk'],axis=1).max()>1e-4:fail('trunk_sway',frame=f)
        axis=Vector(trunk[3]-trunk[0]).normalized()
        if family=='kickback' and not (axis.y>.80 and .05<axis.z<.60):fail('missing_hip_hinge',frame=f,axis=list(axis))
        if family!='kickback' and axis.z<.97:fail('not_upright',frame=f)
        for obj in scene.objects:
            if obj.type=='MESH' and obj!=body:
                matrix=np.array(obj.matrix_local if obj.parent else obj.matrix_world)
                k='object:'+obj.name;first.setdefault(k,matrix.copy())
                if np.max(np.abs(matrix-first[k]))>1e-5:fail('nonrigid_or_moving_support',frame=f,object=obj.name)
        for side in active:
            for name in ('Grip shaft '+side,'Dumbbell plate '+side,'Dumbbell plate '+side+'.001'):
                if name in scene.objects and scene.objects[name].parent!=scene.objects.get('Grip.'+side):fail('detached_load',frame=f,object=name)
        if config.get('seated'):
            pad=scene.objects.get('Seat cushion')
            required=['Bench longitudinal frame','Bench leg -0.83','Bench leg 0.16','Bench foot -0.83','Bench foot 0.16']
            if pad is None or any(n not in scene.objects for n in required):fail('missing_bench_support',frame=f)
            else:
                inv=np.array(pad.matrix_world.inverted());local=points[support_ids]@inv[:3,:3].T+inv[:3,3]
                box=np.array([v.co[:] for v in pad.data.vertices]);lo,hi=box.min(0),box.max(0)
                inside=np.all((local[:,:2]>=lo[:2])&(local[:,:2]<=hi[:2]),axis=1)
                gap=float((local[inside,2].min()-hi[2])*pad.matrix_world.to_3x3().col[2].length) if inside.any() else 999
                supports.append(dict(frame=f,pad='Seat cushion',gap=gap))
                if not -.002<=gap<=.015:fail('seat_contact',frame=f,gap=gap)
                beam=scene.objects['Bench longitudinal frame']
                bottom=pad.location.z-pad.dimensions.z/2
                if abs(beam.location.z+beam.dimensions.z/2-bottom)>.001:
                    fail('bench_beam_detached',frame=f)
                for y in (-.83,.16):
                    leg=scene.objects['Bench leg '+str(y)];foot=scene.objects['Bench foot '+str(y)]
                    if abs(leg.location.z+leg.dimensions.z/2-bottom)>.001 or abs(leg.location.y-foot.location.y)>.001 or foot.location.z-foot.dimensions.z/2<-.001:
                        fail('bench_support_disconnected',frame=f)

        for side,s in [('Left',-1),('Right',1)]:
            prefix='mixamorig:'+side
            positions=np.array([tuple(rig.matrix_world@rig.pose.bones[prefix+p].head) for p in ('Arm','ForeArm','Hand','HandIndex3','HandPinky3')])
            first.setdefault('arm:'+side,positions.copy())
            if side not in active:
                if np.linalg.norm(positions-first['arm:'+side],axis=1).max()>1e-4:fail('unloaded_arm_moved',frame=f)
                continue
            arm=rig.pose.bones[prefix+'Arm'];fore=rig.pose.bones[prefix+'ForeArm'];hand=rig.pose.bones[prefix+'Hand']
            u=(rig.matrix_world.to_3x3()@(arm.tail-arm.head)).normalized();v=(rig.matrix_world.to_3x3()@(fore.tail-fore.head)).normalized();hv=(rig.matrix_world.to_3x3()@(hand.tail-hand.head)).normalized()
            flex=math.degrees(u.angle(v));elev=math.degrees(u.angle(Vector((0,0,-1))));bend=math.degrees(v.angle(hv))
            shoulder,elbow,wrist=[Vector(x) for x in positions[:3]]
            palm=(rig.matrix_world.to_3x3()@(hand.matrix@hand.bone.matrix_local.inverted()).to_3x3()@Vector((0,-1 if side=='Left' else 1,0))).normalized()
            if family=='kickback':intended=Vector((-s,0,0))
            elif family=='bent_lateral':intended=Vector((0,0,-1))
            else:intended=Vector((0,v.z,-v.y)).normalized()
            intended=(intended-v*intended.dot(v)).normalized()
            palm_dot=palm.dot(intended)
            grip=scene.objects['Grip.'+side];inv=np.array(grip.matrix_world.inverted());local=points@inv[:3,:3].T+inv[:3,3]
            radial=local[ids[side]][:,1:];radius=np.linalg.norm(radial,axis=1);near=radial[(radius>=.013)&(radius<=.026)]
            sectors=len(set((np.floor((np.arctan2(near[:,1],near[:,0])+np.pi)*12/(2*np.pi)).astype(int)%12).tolist()))
            gaps={digit:float(np.abs(np.linalg.norm(local[vertices][:,1:],axis=1)-.014).min()) for (s2,digit),vertices in digits.items() if s2==side}
            rel=local[stable[side]];first.setdefault('grip:'+side,rel.copy());drift=float(np.linalg.norm(rel-first['grip:'+side],axis=1).max())
            peak=f==1+scene.frame_end//2;low=f in (1,scene.frame_end+1)
            if family=='kickback':
                if np.linalg.norm(positions[1]-first['arm:'+side][1])>1e-4:fail('kickback_elbow_moved',frame=f,side=side)
                if u.y>-.8:fail('upper_arm_not_back',frame=f,side=side)
                if (low and not 80<=flex<=100) or (peak and not 3<=flex<=16):fail('extension_range',frame=f,side=side,flex=flex)
            elif family=='bent_lateral':
                if not 80<=flex<=100:fail('bent_arm_angle',frame=f,flex=flex)
                if peak and not (80<=elev<=100 and abs(u.x)>.95):fail('bent_lateral_peak',frame=f)
            elif family=='overhead_raise':
                if flex>20:fail('raise_elbow_bent',frame=f)
                if peak and not (elev>155 and wrist.z>shoulder.z+.40):fail('missing_overhead_range',frame=f)
                if f==1+scene.frame_end//4 and u.y<.8:fail('not_front_plane',frame=f)
            else:
                if peak and not (elbow.z>wrist.z+.10 and wrist.z>shoulder.z-.22 and flex>65):fail('upright_row_peak',frame=f,elbow=list(elbow),wrist=list(wrist),shoulder=list(shoulder),flex=flex)
                if low and flex>35:fail('row_return',frame=f,flex=flex)
            if low and family in ('bent_lateral','overhead_raise') and elev>40:fail('raise_return',frame=f)
            row=dict(frame=f,side=side,wristBend=bend,palmIntentDot=palm_dot,sectors=sectors,minSurfaceRadius=float(radius.min()),digitGaps=gaps,handDrift=drift,elbowFlexion=flex,elevation=elev)
            samples.append(row)
            if bend>15 or palm_dot<.8 or sectors<10 or radius.min()<.013 or max(gaps.values())>.008 or drift>1e-4:fail('grip_or_wrist',**row)
    if maxfoot>1e-4 or loop>1e-4:fail('foot_or_loop_drift',foot=maxfoot,loop=loop)
    return dict(failures=failures,samples=samples,supportSamples=supports,maxFootDrift=maxfoot,meshLoopError=loop)
