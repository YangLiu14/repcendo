"""Flatten localized breast-tip protrusions beneath the sculpted band.

Works from the immutable Tripo downloads, keeping topology, UVs and skin groups.
Outputs separate refined GLBs. No cloud regeneration or credit spending.
Run with Blender --background --python-exit-code 1 --python this_file.
"""
import sys,json,math
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from inspect_character import import_character, studio, aim
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/character-assets/greek-athletes-v1/female'
OUT=BASE/'refined'
OUT.mkdir(parents=True,exist_ok=True)

def refine(stage):
    meshes,lo,hi=import_character(BASE/stage/'model.glb')
    results=[]
    for obj in meshes:
        mesh=obj.data
        original_loop_normals=[tuple(n.vector) for n in mesh.corner_normals]
        original=np.array([list(obj.matrix_world@v.co) for v in mesh.vertices])
        # Normalize source and rig to the same floor-centered coordinates.
        offset=np.array([(lo.x+hi.x)*.5,(lo.y+hi.y)*.5,lo.z])
        normalized=original-offset
        influence=np.zeros(len(original))
        for cy,cz in [(-.043,.706),(.046,.711)]:
            radius=np.sqrt(((normalized[:,1]-cy)/.038)**2+((normalized[:,2]-cz)/.035)**2)
            feather=np.clip((1.35-radius)/.65,0,1)
            feather=feather*feather*(3-2*feather)
            influence=np.maximum(influence,feather)
        influence[normalized[:,0]<=.045]=0
        # glTF splits vertices at UV seams. Relax a welded adjacency graph,
        # then map positions back without altering any mesh indices or UVs.
        _, first, mapping=np.unique(np.round(original,6),axis=0,return_index=True,return_inverse=True)
        welded=original[first].copy()
        adjacency=[set() for _ in welded]
        for edge in mesh.edges:
            a,b=(int(mapping[i]) for i in edge.vertices)
            if a!=b:adjacency[a].add(b);adjacency[b].add(a)
        strength=influence[first]
        active=np.flatnonzero(strength>0)
        neighbors={int(i):np.array(sorted(adjacency[i]),dtype=int) for i in active}
        for _ in range(12):
            updated=welded.copy()
            for i in active:
                ids=neighbors[int(i)]
                if len(ids):updated[i]+=.5*strength[i]*(welded[ids].mean(axis=0)-welded[i])
            welded=updated
        points=original.copy()
        changed=influence>0
        points[changed]=welded[mapping[changed]]
        inverse=obj.matrix_world.inverted()
        for vertex,point in zip(mesh.vertices,points):vertex.co=inverse@Vector(point)
        displacement=np.linalg.norm(points-original,axis=1)
        mesh.update()
        mesh.calc_loop_triangles()
        local=np.array([list(v.co) for v in mesh.vertices])
        normals=np.zeros((len(welded),3))
        for triangle in mesh.loop_triangles:
            ids=list(triangle.vertices)
            normal=np.cross(local[ids[1]]-local[ids[0]],local[ids[2]]-local[ids[0]])
            for i in ids:normals[mapping[i]]+=normal
        norms=np.linalg.norm(normals,axis=1)
        normals/=np.maximum(norms[:,None],1e-12)
        loop_normals=[tuple(normals[mapping[loop.vertex_index]]) if influence[loop.vertex_index]>0
                      else original_loop_normals[loop.index] for loop in mesh.loops]
        mesh.normals_split_custom_set(loop_normals)
        mesh.update()
        results.append({'mesh':obj.name,'verticesBefore':len(mesh.vertices),
                        'changedVertices':int(np.count_nonzero(displacement>1e-7)),
                        'maxWorldDisplacement':float(displacement.max()),
                        'region':'two localized front breast-band patches',
                        'topologyUVAndSkinGroupsPreserved':True})
    bpy.ops.object.select_all(action='DESELECT')
    for obj in meshes:obj.select_set(True)
    for obj in bpy.context.scene.objects:
        if obj.type=='ARMATURE':obj.select_set(True)
    bpy.context.view_layer.objects.active=meshes[0]
    target=OUT/f'{stage}.glb'
    bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_selection=True,
                              export_animations=False,export_skins=True)
    if stage=='rig':
        cam,center,span=studio(lo,hi)
        center=Vector((.045,0,.685));cam.data.ortho_scale=.30
        for name,direction in [('front',(1,0,0)),('side',(0,1,0)),('oblique',(1,1,0))]:
            cam.location=center+Vector(direction)*2;aim(cam,center)
            bpy.context.scene.render.filepath=str(OUT/f'chest-{name}.png')
            bpy.ops.render.render(write_still=True)
    return results
report={stage:refine(stage) for stage in ['source','rig']}
(OUT/'refinement.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
