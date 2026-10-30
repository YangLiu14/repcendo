"""Read-only source scenes; render differential evidence only into build/."""
import sys,json,hashlib,time
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'build/deformation-research';OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'Scripts/animation_samples'))
from collision_audit import mesh_data
result={}
for name in ['rdl','cable_crunch']:
 source=ROOT/f'docs/animation-plan-v3/male/{name}.blend'
 bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.context.scene;s.frame_set(61)
 rig=next(o for o in s.objects if o.type=='ARMATURE');body=next(o for o in s.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers));arm=next(m for m in body.modifiers if m.type=='ARMATURE')
 rest=np.array([tuple(body.matrix_world@v.co) for v in body.data.vertices]);edges=np.array([tuple(e.vertices) for e in body.data.edges]);lengths=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1)
 joints=[rig.matrix_world@rig.data.bones['mixamorig:'+side+'ForeArm'].head_local for side in ['Left','Right']]
 region=np.array([min((body.matrix_world@v.co-j).length for j in joints)<.16 if name=='rdl' else v.co.z<.15 for v in body.data.vertices]);e=edges[np.all(region[edges],axis=1)&(lengths>1e-5)];l0=np.linalg.norm(rest[e[:,0]]-rest[e[:,1]],axis=1)
 labels={g.index:g.name for g in body.vertex_groups};sums=[]
 for v in body.data.vertices:
  sums.append(sum(g.weight for g in v.groups if labels[g.group] in rig.data.bones and rig.data.bones[labels[g.group]].use_deform))
 row=dict(sourceSHA256=hashlib.sha256(source.read_bytes()).hexdigest(),frame=61,vertices=len(rest),faces=len(body.data.polygons),triangles=sum(len(p.vertices)==3 for p in body.data.polygons),preserve_volume=arm.use_deform_preserve_volume,rig_scale=list(rig.scale),mesh_scale=list(body.scale),weight_sum_min=float(min(sums)),weight_sum_max=float(max(sums)),modifiers=[dict(name=m.name,type=m.type,iterations=getattr(m,'iterations',None),factor=getattr(m,'factor',None)) for m in body.modifiers],bones={})
 for side in ['Left','Right']:
  for part in ['Arm','ForeArm','Hand','Leg','Foot','ToeBase']:
   bone=rig.pose.bones['mixamorig:'+side+part]
   delta=bone.matrix@bone.bone.matrix_local.inverted();sv=np.linalg.svd(np.array(delta.to_3x3()),compute_uv=False)
   row['bones'][side+part]=dict(basis_scale=list(bone.scale),deform_singular_values=sv.tolist(),parent_tip_gap_m=(rig.matrix_world@bone.head-rig.matrix_world@bone.parent.tail).length if bone.parent else None)
 smooth=[m for m in body.modifiers if m.type=='SMOOTH'];original_dq=arm.use_deform_preserve_volume
 variants={};base=None
 for variant,relax,dq in [('current',True,original_dq),('no_smooth',False,original_dq),('dq_only',True,True),('no_smooth_dq',False,True)]:
  for m in smooth:m.show_viewport=relax;m.show_render=relax
  arm.use_deform_preserve_volume=dq;bpy.context.view_layer.update()
  p,t=mesh_data(body,bpy.context.evaluated_depsgraph_get());ratios=np.linalg.norm(p[e[:,0]]-p[e[:,1]],axis=1)/l0
  if base is None:base=p
  shift=np.linalg.norm(p-base,axis=1)
  variants[variant]=dict(region_edge_ratio_percentiles=np.percentile(ratios,[1,5,50,95,99]).tolist(),region_vertices=int(region.sum()),edge_count=len(e),displacement_from_current_region_max_mm=float(shift[region].max()*1000),displacement_from_current_region_mean_mm=float(shift[region].mean()*1000))
  # The same camera and light settings across variants: make anatomy visible.
  if name=='rdl':
   target=(rig.matrix_world@rig.pose.bones['mixamorig:LeftForeArm'].head)*.65+(rig.matrix_world@rig.pose.bones['mixamorig:LeftHand'].head)*.35
   s.camera.location=target+Vector((-2.5,3,1));s.camera.data.ortho_scale=.76
  else:
   target=(rig.matrix_world@rig.pose.bones['mixamorig:LeftFoot'].head)+Vector((0,-.05,.03))
   s.camera.location=target+Vector((-3,-2,1.3));s.camera.data.ortho_scale=.72
  s.camera.rotation_euler=(target-s.camera.location).to_track_quat('-Z','Y').to_euler();s.render.resolution_x=650;s.render.resolution_y=650;s.render.resolution_percentage=100;s.eevee.taa_render_samples=24;s.render.filepath=str(OUT/f'{name}-{variant}.png');bpy.ops.render.render(write_still=True)
 row['variants']=variants;result[name]=row;print(name,json.dumps(row),flush=True)
(OUT/'probe.json').write_text(json.dumps(result,indent=2)+'\n')
