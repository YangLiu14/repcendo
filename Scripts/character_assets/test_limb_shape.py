"""Blender regression for bounded corrections and unchanged topology/UV/feet."""
import sys
from pathlib import Path
import numpy as np,bpy
sys.path.insert(0,str(Path(__file__).parent))
from prepare_athlete import prepare_character
from limb_shape import displacement,apply
for sex in ['male','female']:
 r,b,*_=prepare_character(sex,limb_refinement=False)
 p=np.array([v.co[:] for v in b.data.vertices]);d=displacement(p,r,sex)
 topology=[tuple(f.vertices) for f in b.data.polygons]
 uv=[tuple(v.uv) for v in b.data.uv_layers.active.data]
 weights=[[(g.group,g.weight) for g in v.groups] for v in b.data.vertices]
 report=apply(b,r,sex)
 after=np.array([v.co[:] for v in b.data.vertices])
 assert np.allclose(after,p+d,atol=1e-7)
 assert topology==[tuple(f.vertices) for f in b.data.polygons]
 assert uv==[tuple(v.uv) for v in b.data.uv_layers.active.data]
 assert weights==[[(g.group,g.weight) for g in v.groups] for v in b.data.vertices]
 assert np.isfinite(d).all()
 assert np.all(d[(p[:,2]<=.105)|(p[:,2]>=.34)]==0),'Feet or upper body moved'
 assert np.max(np.linalg.norm(d,axis=1))<.014,'Correction exceeded bounded contour edit'
 assert np.sum(np.linalg.norm(d,axis=1)>1e-8)>1000,'Correction missing'
 assert np.all(d[:,2]==0),'Leg length changed'
 try:apply(b,r,sex)
 except ValueError:pass
 else:raise AssertionError('Repeated correction must be rejected')
 print('PASS',sex,'bounded limb contour; feet/upper body/length preserved; repeat rejected')
