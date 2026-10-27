"""Build editable surface muscle illustrations, UV atlases and a skinned GLB.

These are approximate superficial muscle regions, NOT dissected anatomy.
All positions, skin groups and rig bones remain those of the selected sculptures.
"""
import argparse, json, math, sys
from pathlib import Path
from collections import Counter
import bpy
import numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from inspect_character import import_character, studio, aim, inspect
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/character-assets/muscle-overlay-v1'
GROUPS=[('marble','白色雕塑'),('pectoralis_major','胸大肌'),('deltoid_anterior','三角肌前束'),
 ('deltoid_lateral','三角肌中束'),('deltoid_posterior','三角肌后束'),('biceps_brachii','肱二头肌'),
 ('triceps_brachii','肱三头肌'),('forearm_flexors','前臂屈肌群'),('forearm_extensors','前臂伸肌群'),
 ('rectus_abdominis','腹直肌'),('external_oblique','腹外斜肌'),('trapezius','斜方肌'),
 ('latissimus_dorsi','背阔肌'),('gluteus_maximus','臀大肌'),('quadriceps','股四头肌群'),
 ('hamstrings','腘绳肌群'),('gastrocnemius','腓肠肌'),('tibialis_anterior','胫骨前肌')]
PRESETS={'all':list(range(1,len(GROUPS))), 'chest':[1], 'back':[11,12], 'legs':[13,14,15,16],
         'press':[1,2,6], 'row':[4,5,11,12], 'squat':[13,14], 'marble':[]}

def clamp(v):return max(0,min(1,v))
def smooth(v):v=clamp(v);return v*v*(3-2*v)
def polygon_distance(p,poly):
    x,y=p;inside=False;dist=1e3
    for i,a in enumerate(poly):
        b=poly[(i+1)%len(poly)]
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:inside=not inside
        ab=Vector((b[0]-a[0],b[1]-a[1]));ap=Vector((x-a[0],y-a[1]))
        t=clamp(ap.dot(ab)/max(ab.length_squared,1e-10))
        dist=min(dist,(ap-ab*t).length)
    return dist if inside else -dist

class Anatomy:
    def __init__(self,rig,sex,obj):
        self.sex=sex
        self.bones={b.name.replace('mixamorig:',''):(rig.matrix_world@b.head_local,rig.matrix_world@b.tail_local) for b in rig.data.bones}
        self.arm_centers={}
        for side in ['Left','Right']:
            a,b=self.bones[side+'Arm'];axis=(b-a).normalized();length=(b-a).length
            fw=Vector((1,0,0));fw=(fw-axis*fw.dot(axis)).normalized()
            gid=obj.vertex_groups['mixamorig:'+side+'Arm'].index;depth=[]
            for vertex in obj.data.vertices:
                if sum(g.weight for g in vertex.groups if g.group==gid)>.4:
                    q=obj.matrix_world@vertex.co-a;t=q.dot(axis)/length
                    if .35<t<.85:depth.append(q.dot(fw))
            self.arm_centers[side]=float(np.mean(np.percentile(depth,[5,95])))

    def regions(self,point):
        x,y,z=point;ay=abs(y);sgn=1 if y>=0 else -1;side='Left' if sgn>0 else 'Right'
        dz=.006 if self.sex=='female' else 0
        zz=z-dz
        out={}
        def add(i,weight,u,v):
            if weight>0 and weight>out.get(i,(0,0,0))[0]:out[i]=(clamp(weight),u,v)
        def poly(i,shape,gate,uv):
            if gate:
                d=polygon_distance((ay,zz),shape)
                add(i,smooth(d/.006),*uv)
        # Anterior thorax: fan converges laterally toward the proximal humerus.
        poly(1,[(.007,.760),(.047,.775),(.088,.766),(.113,.741),(.093,.709),(.066,.693),(.012,.699)],
             x>.026,(math.atan2(zz-.745,ay-.123)*1.6,(math.hypot(ay-.123,zz-.745))/.11))
        # Rectus is a series of paired segments with a retained white linea alba.
        if x>.024 and ay<.042:
            for bottom,top in [(.568,.595),(.599,.628),(.632,.661),(.665,.689)]:
                d=polygon_distance((ay,zz),[(.005,bottom),(.032,bottom+.003),(.036,top-.005),(.031,top),(.005,top)])
                add(9,smooth(d/.004),y/.07,zz/.11)
        poly(10,[(.044,.670),(.080,.688),(.094,.655),(.077,.610),(.067,.567),(.043,.573)],
             x>.005,((ay+zz)*9,(zz-ay)*9))
        # Superficial posterior torso; do not label deep rhomboids as exposed.
        poly(11,[(.004,.802),(.029,.790),(.103,.756),(.079,.725),(.037,.693),(.006,.647)],
             x<-.020,((ay+zz)*10,(zz-ay)*10))
        poly(12,[(.038,.697),(.083,.734),(.115,.718),(.105,.678),(.082,.613),(.062,.577),(.018,.601)],
             x<-.025,(math.atan2(zz-.728,ay-.13)*1.6,math.hypot(ay-.13,zz-.728)/.14))
        poly(13,[(.011,.539),(.063,.552),(.106,.529),(.118,.492),(.099,.457),(.048,.443),(.014,.466)],
             x<-.028,((ay-zz)*8,(ay+zz)*8))
        # Bone-relative coordinates adapt masks to each character's arms and legs.
        def bonecoords(part):
            a,b=self.bones[side+part];axis=(b-a);length=axis.length;axis.normalize()
            q=Vector(point)-a;t=q.dot(axis)/length
            forward=Vector((1,0,0));forward=(forward-axis*forward.dot(axis)).normalized()
            outward=axis.cross(forward).normalized()*sgn
            if outward.y*sgn<0:outward=-outward
            return t,q.dot(forward)-(self.arm_centers[side] if part=='Arm' else 0),q.dot(outward),length
        t,f,l,length=bonecoords('Arm')
        if -.12<t<1.02 and ay>.09:
            radial=math.sqrt(f*f+l*l)
            if radial<.075:
                cap=smooth((.45-t)/.13)*smooth((t+.13)/.08)
                # Three deltoid portions divide the shoulder cap by surface angle.
                if f>.014:add(2,cap*smooth((f-.010)/.014),l/.075,t*2)
                elif f<-.014:add(4,cap*smooth((-f-.010)/.014),l/.075,t*2)
                elif l>.01:add(3,cap*smooth((l-.008)/.018),f/.06,t*2)
                belly=smooth((t-.32)/.12)*smooth((.94-t)/.15)
                if f>.012:add(5,belly*smooth((f-.01)/.014),l/.065,t*1.6)
                if f<-.010:add(6,belly*smooth((-f-.008)/.016),l/.075,t*1.5)
        t,f,l,length=bonecoords('ForeArm')
        if .08<t<.86 and ay>.135 and math.hypot(f,l)<.052:
            w=smooth((t-.08)/.15)*smooth((.86-t)/.22)
            if f>.009:add(7,w*smooth((f-.006)/.012),l/.05,t*2)
            if f<-.008:add(8,w*smooth((-f-.006)/.012),l/.05,t*2)
        t,f,l,length=bonecoords('UpLeg')
        if .12<t<.96 and math.hypot(f,l)<.09:
            # Leave patella and tendons pale; segmented quad silhouettes suggest
            # rectus femoris and visible vasti without claiming a deep cross-section.
            if f>.016:
                shapes=[((l/.029)**2+((t-.48)/.34)**2),(((l-.030)/.021)**2+((t-.50)/.38)**2),(((l+.026)/.020)**2+((t-.68)/.24)**2)]
                w=max(smooth((1-v)/.28) for v in shapes)*smooth((f-.012)/.015)
                add(14,w,l/.075,t*1.8)
            if f<-.020:
                w=smooth((t-.15)/.15)*smooth((.93-t)/.18)*smooth((-f-.015)/.02)
                w*=smooth((abs(l)-.002)/.008) # two posterior bellies
                add(15,w,l/.07,t*1.8)
        t,f,l,length=bonecoords('Leg')
        if .08<t<.82 and math.hypot(f,l)<.100:
            if f<-.012:
                v=((abs(l)-.015)/.020)**2+((t-.30)/.28)**2
                add(16,smooth((1-v)/.25)*smooth((-f-.008)/.014),l/.065,t*2)
            if f>.008 and l>0:
                v=((l-.016)/.019)**2+((t-.46)/.34)**2
                add(17,smooth((1-v)/.3)*smooth((f-.005)/.015),l/.04,t*2)
        return out
    def sample(self,p,group=None):
        r=self.regions(p)
        if group is not None:return r.get(group,(0,0,0))
        if not r:return 0,(0,0,0)
        # Stronger interior masks win at shoulder/torso transitions.
        group=max(r,key=lambda g:r[g][0])
        return group,r[group]

def new_image(name,size,noncolor=False):
    image=bpy.data.images.new(name,width=size,height=size,alpha=False)
    if noncolor:image.colorspace_settings.name='Non-Color'
    return image

def bake(mesh,mats,image,kind='EMIT'):
    bpy.ops.object.select_all(action='DESELECT');mesh.select_set(True);bpy.context.view_layer.objects.active=mesh
    for mat in mats:
        node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=image;node.label='Bake target';mat.node_tree.nodes.active=node
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=1
    scene.render.bake.margin=6;scene.render.bake.use_clear=True
    bpy.ops.object.bake(type=kind)
    image.filepath_raw=str(image_path(image.name));image.file_format='PNG';image.save()
    return image
CURRENT_OUT=None
def image_path(name):return CURRENT_OUT/'textures'/f'{name}.png'

def build(sex,size):
    global CURRENT_OUT
    out=BASE/sex;CURRENT_OUT=out;(out/'textures').mkdir(parents=True,exist_ok=True)
    source=ROOT/f'docs/character-assets/greek-athletes-v1/{sex}/greek-{sex}-rigged.glb'
    meshes,lo,hi=import_character(source);obj=meshes[0];mesh=obj.data
    rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');rig.show_in_front=True
    reference=inspect(meshes,lo,hi,source)
    assert all(m['unweightedVertices']==0 for m in reference['meshes'])
    original=obj.active_material;original.name='Original_Marble'
    old_nodes=original.node_tree.nodes
    old_bsdf=next(n for n in old_nodes if n.type=='BSDF_PRINCIPLED')
    base_links=list(old_bsdf.inputs['Base Color'].links)
    base_image=base_links[0].from_node.image if base_links else None
    normal_nodes=[n for n in old_nodes if n.type=='TEX_IMAGE' and n.image and n.image.colorspace_settings.name=='Non-Color']
    fiber=bpy.data.images.load(str(BASE/'shared/fiber-albedo.png'))
    for image in bpy.data.images:
        if image==base_image:
            image.filepath_raw=str(out/'textures/marble-basecolor.png');image.file_format='PNG';image.save()
    anatomy=Anatomy(rig,sex,obj)
    points=[obj.matrix_world@v.co for v in mesh.vertices]
    faces=[];muscle_uv=mesh.uv_layers.new(name='MuscleFiberUV')
    fade=mesh.color_attributes.new(name='MuscleCoverage',type='FLOAT_COLOR',domain='CORNER')
    group_attr=mesh.attributes.new(name='muscle_id',type='INT',domain='FACE')
    for face in mesh.polygons:
        center=sum((points[i] for i in face.vertices),Vector())/len(face.vertices)
        group,(_,u,v)=anatomy.sample(center)
        # Exclude tiny slivers instead of producing isolated red fragments.
        if group and anatomy.sample(center,group)[0]<.06:group=0
        faces.append(group);group_attr.data[face.index].value=group
        for loop_index in face.loop_indices:
            p=points[mesh.loops[loop_index].vertex_index]
            coverage,fu,fv=anatomy.sample(p,group) if group else (0,0,0)
            muscle_uv.data[loop_index].uv=(fu,fv)
            fade.data[loop_index].color=(coverage,coverage,coverage,1)
    counts=Counter(faces)
    materials=[];emissions=[]
    for i,(key,label) in enumerate(GROUPS):
        mat=bpy.data.materials.new(f'Muscle_{i:02d}_{key}');mat.use_nodes=True
        n=mat.node_tree.nodes;n.clear();links=mat.node_tree.links
        output=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission');links.new(em.outputs[0],output.inputs['Surface'])
        uv=n.new('ShaderNodeUVMap');uv.uv_map='UVMap'
        marble=n.new('ShaderNodeTexImage');marble.image=base_image;links.new(uv.outputs[0],marble.inputs['Vector'])
        if i:
            fiberuv=n.new('ShaderNodeUVMap');fiberuv.uv_map='MuscleFiberUV'
            tex=n.new('ShaderNodeTexImage');tex.image=fiber;tex.extension='REPEAT';links.new(fiberuv.outputs[0],tex.inputs['Vector'])
            attr=n.new('ShaderNodeVertexColor');attr.layer_name='MuscleCoverage'
            mix=n.new('ShaderNodeMixRGB');links.new(attr.outputs['Color'],mix.inputs[0]);links.new(marble.outputs['Color'],mix.inputs[1]);links.new(tex.outputs['Color'],mix.inputs[2])
            links.new(mix.outputs[0],em.inputs[0])
        else:links.new(marble.outputs['Color'],em.inputs[0])
        materials.append(mat);emissions.append(em)
    mesh.materials.clear()
    for mat in materials:mesh.materials.append(mat)
    for face,g in zip(mesh.polygons,faces):face.material_index=g
    # Bake to the character's ORIGINAL UVs, not the orientation helper layer.
    mesh.uv_layers.active_index=0
    for layer in mesh.uv_layers:layer.active_render=(layer.name=='UVMap')
    albedo=bake(obj,materials,new_image('muscle-albedo',size))
    for i,em in enumerate(emissions):
        for link in list(em.inputs[0].links):em.id_data.links.remove(link)
        em.inputs[0].default_value=(i/255,i/255,i/255,1)
    ids=bake(obj,materials,new_image('muscle-id',size,True))
    for i,em in enumerate(emissions):
        if i:
            attr=em.id_data.nodes.new('ShaderNodeVertexColor');attr.layer_name='MuscleCoverage'
            em.id_data.links.new(attr.outputs['Color'],em.inputs[0])
        else:em.inputs[0].default_value=(0,0,0,1)
    coverage=bake(obj,materials,new_image('muscle-coverage',size,True))
    ids_data=np.array(ids.pixels[:],dtype=np.float32).reshape(-1,4)
    coverage_data=np.array(coverage.pixels[:],dtype=np.float32).reshape(-1,4)
    id_values=np.rint(ids_data[:,0]*255).astype(np.int32)
    (out/'textures/masks').mkdir(exist_ok=True)
    for i,(key,_) in enumerate(GROUPS):
        if not i:continue
        mask=new_image('mask-'+key,size,True)
        pixels=np.zeros((size*size,4),dtype=np.float32);pixels[:,3]=1
        values=(id_values==i)*coverage_data[:,0]
        pixels[:,:3]=values[:,None]
        mask.pixels.foreach_set(pixels.ravel())
        mask.filepath_raw=str(out/'textures/masks'/f'{i:02d}-{key}.png');mask.file_format='PNG';mask.save()
        bpy.data.images.remove(mask)
    # Restore physically shaded materials. Same UV atlas, separate named groups.
    for i,mat in enumerate(materials):
        n=mat.node_tree.nodes;n.clear();links=mat.node_tree.links
        output=n.new('ShaderNodeOutputMaterial');bsdf=n.new('ShaderNodeBsdfPrincipled')
        bsdf.inputs['Roughness'].default_value=.62;links.new(bsdf.outputs[0],output.inputs['Surface'])
        uv=n.new('ShaderNodeUVMap');uv.uv_map='UVMap'
        tex=n.new('ShaderNodeTexImage');tex.image=albedo;links.new(uv.outputs[0],tex.inputs['Vector']);links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
        if i:
            fiberuv=n.new('ShaderNodeUVMap');fiberuv.uv_map='MuscleFiberUV'
            fib=n.new('ShaderNodeTexImage');fib.image=fiber;links.new(fiberuv.outputs[0],fib.inputs['Vector'])
            bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.0008
            links.new(fib.outputs['Color'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bsdf.inputs['Normal'])
    normals=bake(obj,materials,new_image('muscle-normal',size,True),'NORMAL')
    # Keep a standard glTF-friendly shader: all maps use original UVs only.
    for i,mat in enumerate(materials):
        n=mat.node_tree.nodes;n.clear();links=mat.node_tree.links
        output=n.new('ShaderNodeOutputMaterial');bsdf=n.new('ShaderNodeBsdfPrincipled');bsdf.inputs['Roughness'].default_value=.62
        links.new(bsdf.outputs[0],output.inputs[0]);tex=n.new('ShaderNodeTexImage');tex.image=albedo;links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
        normal=n.new('ShaderNodeTexImage');normal.image=normals;nm=n.new('ShaderNodeNormalMap');links.new(normal.outputs['Color'],nm.inputs['Color']);links.new(nm.outputs['Normal'],bsdf.inputs['Normal'])
        mat['muscle_id']=i;mat['display_name']=GROUPS[i][1]
    mesh.uv_layers.remove(muscle_uv)
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=obj
    bpy.ops.export_scene.gltf(filepath=str(out/f'greek-{sex}-muscles.glb'),export_format='GLB',use_selection=True,export_animations=False,export_skins=True,export_extras=True)
    # Add editable enable switches after export; Blender drivers are not glTF.
    for i,mat in enumerate(materials):
        if not i:continue
        key=GROUPS[i][0];rig[key]=1.0;rig.id_properties_ui(key).update(min=0,max=1,description=GROUPS[i][1]+' display opacity')
        n=mat.node_tree.nodes;links=mat.node_tree.links;bsdf=next(n for n in n if n.type=='BSDF_PRINCIPLED')
        color=bsdf.inputs['Base Color'].links[0].from_node
        marble=n.new('ShaderNodeTexImage');marble.image=base_image
        mix=n.new('ShaderNodeMixRGB');links.new(marble.outputs['Color'],mix.inputs[1]);links.new(color.outputs['Color'],mix.inputs[2]);links.new(mix.outputs[0],bsdf.inputs['Base Color'])
        driver=mix.inputs[0].driver_add('default_value').driver;v=driver.variables.new();v.name='show';v.type='SINGLE_PROP';v.targets[0].id=rig;v.targets[0].data_path=f'["{key}"]';driver.expression='show'
        nm=next(node for node in n if node.type=='NORMAL_MAP');d=nm.inputs['Strength'].driver_add('default_value').driver;v=d.variables.new();v.name='show';v.type='SINGLE_PROP';v.targets[0].id=rig;v.targets[0].data_path=f'["{key}"]';d.expression='show'
    camera,center,span=studio(lo,hi);bpy.context.scene.view_settings.look='AgX - Medium High Contrast'
    camera.data.ortho_scale=span*1.17
    for preset,groups in PRESETS.items():
        if preset not in ['all','chest','back','legs','press','squat']:continue
        for i,(key,_) in enumerate(GROUPS):
            if i:rig[key]=float(i in groups)
        rig.update_tag();bpy.context.view_layer.update()
        views={'front':(1,0,.015),'back':(-1,0,.015)} if preset in ['all','legs'] else {'front':(1,0,.015)}
        if preset=='back':views={'back':(-1,0,.015)}
        for view,direction in views.items():
            camera.location=center+Vector(direction)*span*3;aim(camera,center)
            bpy.context.scene.render.filepath=str(out/f'{preset}-{view}.png');bpy.ops.render.render(write_still=True)
    for i,(key,_) in enumerate(GROUPS):
        if i:rig[key]=1.0
    rig.update_tag();bpy.context.view_layer.update()
    camera.location=center+Vector((1,.45,.02))*span*3;aim(camera,center)
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(out/f'greek-{sex}-muscles.blend'))
    report={'sex':sex,'source':str(source.relative_to(ROOT)),'vertices':len(mesh.vertices),'triangles':sum(len(p.vertices)-2 for p in mesh.polygons),'rigNodes':len(rig.data.bones),'unweightedVertices':reference['meshes'][0]['unweightedVertices'],
            'groups':[{'id':i,'key':key,'name':label,'faces':counts[i]} for i,(key,label) in enumerate(GROUPS)],
            'textureSize':size,'presets':PRESETS,'representation':'approximate surface-region illustration; not volumetric anatomical muscles'}
    (out/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    assert all(counts[i]>0 for i in range(len(GROUPS))),str(counts)
    print('MUSCLE_ASSET',json.dumps(report,ensure_ascii=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--sex',choices=['male','female'],required=True);parser.add_argument('--size',type=int,default=2048)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);build(args.sex,args.size)
