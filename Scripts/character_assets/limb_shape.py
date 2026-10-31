"""Localized, rest-space sculpture corrections; topology, UVs and feet stay intact."""
import numpy as np
from mathutils import Vector
VERSION = 'limb-contour-1'


def smooth(a, b, x):
    t = np.clip((x-a)/(b-a), 0, 1)
    return t*t*(3-2*t)


def displacement(points, rig, sex):
    """Reduce round calf lobes and soften patellar protrusion with smooth falloffs.

    Coordinates are the original normalized character space (+X anterior).
    No smoothing modifier or animation-dependent scale is introduced.
    """
    p=np.asarray(points,dtype=float);d=np.zeros_like(p);z=p[:,2]
    for side,sign in [('Left',1),('Right',-1)]:
        knee=rig.data.bones['mixamorig:'+side+'Leg'].head_local
        ankle=rig.data.bones['mixamorig:'+side+'Foot'].head_local
        t=np.clip((z-ankle.z)/(knee.z-ankle.z),0,1)
        cx=ankle.x+(knee.x-ankle.x)*t
        cy=ankle.y+(knee.y-ankle.y)*t
        own=(p[:,1]*sign>0)
        band=smooth(.105,.145,z)*(1-smooth(.235,.275,z))*own
        belly=np.exp(-((z-.203)/.044)**2)*band
        # Preserve the anterior shin and the Achilles/ankle silhouette.
        posterior=1-smooth(-.006,.025,p[:,0]-cx)
        d[:,1]-=(p[:,1]-cy)*belly*(.18 if sex=='male' else .09)
        d[:,0]-=(p[:,0]-cx)*belly*posterior*(.14 if sex=='male' else .07)
        # Broad, low-amplitude correction, fading before thigh clothing.
        cap=np.exp(-((z-knee.z)/.027)**2)*smooth(.018,.045,p[:,0]-knee.x)*own
        cap*=smooth(.225,.25,z)*(1-smooth(.315,.34,z))
        d[:,0]-=cap*(.004 if sex=='male' else .002)
    return d


def apply(body,rig,sex):
    if body.get('limb_shape_version'):
        raise ValueError('Limb contour correction already applied')
    original=np.array([v.co[:] for v in body.data.vertices]);delta=displacement(original,rig,sex)
    if body.data.shape_keys:
        for key in body.data.shape_keys.key_blocks:
            for v,d in zip(key.data,delta):v.co+=Vector(d)
    else:
        for v,d in zip(body.data.vertices,delta):v.co+=Vector(d)
    body.data.update();body['limb_shape_version']=VERSION
    return dict(version=VERSION,vertices=int(np.sum(np.linalg.norm(delta,axis=1)>1e-8)),maxDisplacement=float(np.max(np.linalg.norm(delta,axis=1))))
