"""Original articulated exercise mannequins. Run with Blender's Python.

No third-party mesh, motion, texture, photograph, or dataset media is used.
Orange surfaces are schematic muscle regions, not anatomical segmentation.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--exercise', choices=['squat', 'bench', 'row'], required=True)
parser.add_argument('--view', choices=['motion', 'front', 'back'], default='motion')
parser.add_argument('--preview', action='store_true')
parser.add_argument('--frame', type=int, default=61)
parser.add_argument('--engine', default='BLENDER_WORKBENCH')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
OUT = ROOT / 'build/animation-samples' / args.exercise
OUT.mkdir(parents=True, exist_ok=True)
DELIVER = ROOT / 'docs/animation-samples'
DELIVER.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version=0


def material(name, color, metallic=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = .5
    p.inputs['Metallic'].default_value = metallic
    return m


SKIN = material('Porcelain / original mannequin', (.69, .73, .71))
MUSCLE = material('Inactive surface panels', (.73, .77, .75))
ORANGE = material('Primary muscle region / schematic', (1, .24, .065))
JOINT = material('Articulations', (.42, .48, .46))
DARK = material('Equipment / graphite', (.075, .11, .10))
STEEL = material('Bar / satin steel', (.43, .49, .48), .6)
PAD = material('Upholstery', (.18, .23, .21))
BASE = material('Studio platform', (.86, .87, .83))


def finish(obj, name, mat, parent=None):
    obj.name = name
    obj.data.materials.append(mat)
    if parent:
        obj.parent = parent
    if hasattr(obj.data, 'polygons'):
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj


def empty(name):
    o = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(o)
    o.rotation_mode = 'QUATERNION'
    return o


def ellipsoid(name, pos, scale, mat=SKIN, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=20, location=pos)
    o = finish(bpy.context.object, name, mat, parent)
    o.scale = scale
    return o


def cube(name, pos, scale, mat=DARK, bevel=.025, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    o = finish(bpy.context.object, name, mat, parent)
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        b = o.modifiers.new('Soft manufactured edges', 'BEVEL')
        b.width = bevel
        b.segments = 3
        o.modifiers.new('Weighted normals', 'WEIGHTED_NORMAL')
    return o


def cylinder(name, a, b, radius, mat, parent=None):
    a, b = Vector(a), Vector(b)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=radius, depth=(b-a).length,
                                      location=(a+b)/2)
    o = finish(bpy.context.object, name, mat, parent)
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = (b-a).to_track_quat('Z', 'Y')
    bevel = o.modifiers.new('Machined edge', 'BEVEL')
    bevel.width = min(.008, radius * .18)
    bevel.segments = 2
    o.modifiers.new('Weighted normals', 'WEIGHTED_NORMAL')
    return o


def mesh(name, vertices, faces, mat, parent):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    return finish(obj, name, mat, parent)


def surface(name, rings, mat, parent, segments=48):
    verts = [(rx*math.cos(a*2*math.pi/segments), ry*math.sin(a*2*math.pi/segments), z)
             for z, rx, ry in rings for a in range(segments)]
    faces = [(r*segments+a, r*segments+(a+1)%segments,
              (r+1)*segments+(a+1)%segments, (r+1)*segments+a)
             for r in range(len(rings)-1) for a in range(segments)]
    faces += [tuple(reversed(range(segments))),
              tuple((len(rings)-1)*segments+a for a in range(segments))]
    return mesh(name, verts, faces, mat, parent)


TORSO_RINGS = [(0,.155,.105),(.07,.14,.10),(.14,.13,.095),(.23,.17,.11),
               (.33,.215,.125),(.40,.225,.12),(.46,.195,.09),(.50,.11,.07)]


def radii_at(z):
    for (a,x,y),(b,u,v) in zip(TORSO_RINGS,TORSO_RINGS[1:]):
        if a <= z <= b:
            t=(z-a)/(b-a)
            return x+(u-x)*t,y+(v-y)*t
    return TORSO_RINGS[0][1:]


def torso_panel(name, cx, cz, rx, rz, front, mat, parent, tilt=0):
    # Elliptical patch follows the actual curved torso surface.
    def point(r, angle):
        u=r*rx*math.cos(angle); v=r*rz*math.sin(angle)
        x=cx+u+tilt*v; z=cz+v
        w,d=radii_at(z)
        y=front*(d*math.sqrt(max(.02,1-(x/w)**2))+.004)
        return (x,y,z)
    n=40; verts=[point(0,0)]
    for r in [.25,.5,.75,1]:
        verts += [point(r,a*2*math.pi/n) for a in range(n)]
    faces=[(0,1+a,1+(a+1)%n) for a in range(n)]
    for ring in range(3):
        p=1+ring*n; q=p+n
        faces += [(p+a,q+a,q+(a+1)%n,p+(a+1)%n) for a in range(n)]
    if front==1:
        faces=[tuple(reversed(f)) for f in faces]
    return mesh(name,verts,faces,mat,parent)


def glute_panel(side,parent):
    def point(r,a):
        x=side*.079+r*.069*math.cos(a)
        z=-.008+r*.095*math.sin(a)
        y=-.115*math.sqrt(max(.01,1-(x/.175)**2-(z/.13)**2))-.004
        return (x,y,z)
    n=40;verts=[point(0,0)]
    for r in [.25,.5,.75,1]:
        verts += [point(r,a*2*math.pi/n) for a in range(n)]
    faces=[(0,1+a,1+(a+1)%n) for a in range(n)]
    for k in range(3):
        p=1+k*n;q=p+n
        faces += [(p+a,q+a,q+(a+1)%n,p+(a+1)%n) for a in range(n)]
    return mesh('Gluteus maximus surface region',verts,faces,ORANGE,parent)


BODY=empty('Body | hip-to-shoulder frame')
surface('Torso',TORSO_RINGS,SKIN,BODY)
PELVIS=empty('Pelvis')
ellipsoid('Pelvic shell',(0,0,0),(.175,.115,.13),SKIN,PELVIS)
for s in [-1,1]:
    label='L' if s<0 else 'R'
    if args.exercise=='squat':
        glute_panel(s,PELVIS)
    if args.exercise=='bench':
        torso_panel('Pectoralis major '+label,s*.108,.372,.09,.072,1,ORANGE,BODY,tilt=s*.10)
    if args.exercise=='row':
        torso_panel('Latissimus dorsi region '+label,s*.135,.24,.050,.13,-1,ORANGE,BODY,tilt=s*.24)
        torso_panel('Interscapular region '+label,s*.065,.405,.050,.063,-1,ORANGE,BODY,tilt=s*.20)

cylinder('Neck',(0,0,.485),(0,0,.57),.054,SKIN,BODY)
ellipsoid('Head',(0,0,.655),(.085,.085,.112),SKIN,BODY)
ellipsoid('Face orientation / nose',(0,.079,.651),(.020,.019,.028),SKIN,BODY)


def segment(name, radius, quad=False):
    root=empty(name)
    profile=[(0,.68),(.08,.9),(.23,1.05),(.45,1),(.7,.85),(.92,.66),(1,.62)]
    surface(name+' shell',[(z,radius*r,radius*r*.90) for z,r in profile],SKIN,root)
    if quad and args.exercise=='squat':
        # Surface patches stay on the anterior thigh instead of protruding.
        def point(r,a,center):
            z=.49+r*.36*math.sin(a)
            angle=center+r*(.30 if center else .34)*math.cos(a)
            for (za,ra),(zb,rb) in zip(profile,profile[1:]):
                if za<=z<=zb:
                    rad=radius*(ra+(rb-ra)*(z-za)/(zb-za))+.003
                    break
            return (rad*math.sin(angle),rad*.90*math.cos(angle)+.002,z)
        for center in [-.70,0,.70]:
            n=40;verts=[point(0,0,center)]
            for r in [.25,.5,.75,1]:
                verts += [point(r,a*2*math.pi/n,center) for a in range(n)]
            faces=[(0,1+a,1+(a+1)%n) for a in range(n)]
            for k in range(3):
                p=1+k*n;q=p+n
                faces += [(p+a,q+a,q+(a+1)%n,p+(a+1)%n) for a in range(n)]
            mesh('Quadriceps surface region',verts,[tuple(reversed(f)) for f in faces],ORANGE,root)
    return root


PARTS={}
JOINTS={}
FEET={}
HANDS={}
for s in [-1,1]:
    for name,radius in [('thigh',.09),('shin',.06),('upper_arm',.059),('forearm',.047)]:
        PARTS[s,name]=segment(f'{s:+d} {name}',radius,quad=name=='thigh')
    for name,radius in [('knee',.055),('elbow',.044),('shoulder',.073),('wrist',.033)]:
        JOINTS[s,name]=ellipsoid(f'{s:+d} {name}',(0,0,0),(radius,)*3,
                               SKIN if name=='shoulder' else JOINT)
    FEET[s]=empty(f'{s:+d} Foot')
    cube('Training shoe',(0,.067,-.025),(.11,.24,.085),SKIN,.035,FEET[s])
    cube('Sole',(0,.067,-.061),(.115,.245,.022),JOINT,.009,FEET[s])
    HANDS[s]=ellipsoid(f'{s:+d} Grip',(0,0,0),(.041,.048,.048),SKIN)


def set_pose(obj, pos, quat=None, scale=None, frame=None):
    obj.location=pos
    if quat is not None:
        obj.rotation_mode='QUATERNION'; obj.rotation_quaternion=quat
    if scale is not None:
        obj.scale=scale
    if frame is not None:
        obj.keyframe_insert('location',frame=frame)
        if quat is not None: obj.keyframe_insert('rotation_quaternion',frame=frame)
        if scale is not None: obj.keyframe_insert('scale',frame=frame)


def frame_quat(up, forward):
    z=Vector(up).normalized()
    y=Vector(forward); y=(y-z*y.dot(z)).normalized()
    x=y.cross(z).normalized()
    return Matrix((x,y,z)).transposed().to_quaternion()


def bone(obj, a,b,forward,frame):
    a,b=Vector(a),Vector(b)
    set_pose(obj,a,frame_quat(b-a,forward),(1,1,(b-a).length),frame)


def ik(a,b,l1,l2,pole):
    a,b,pole=Vector(a),Vector(b),Vector(pole)
    delta=b-a; d=delta.length; axis=delta.normalized()
    if d > l1+l2+.002 or d < abs(l1-l2)-.002:
        raise ValueError(f'Unreachable limb: {d:.4f}, lengths {l1}, {l2}')
    along=(l1*l1-l2*l2+d*d)/(2*d)
    height=math.sqrt(max(0,l1*l1-along*along))
    bend=pole-a; bend=(bend-axis*bend.dot(axis)).normalized()
    return a+axis*along+bend*height


BAR=empty('Barbell / animated with grip')
if args.exercise in ['squat','bench'] and args.view=='motion':
    cylinder('Bar shaft',(-.94,0,0),(.94,0,0),.013,STEEL,BAR)
    for s in [-1,1]:
        cylinder('Sleeve',(s*.60,0,0),(s*.93,0,0),.024,STEEL,BAR)
        for x,r,w in [(.70,.15,.055),(.77,.125,.045)]:
            cylinder('Weight plate',(s*(x-w/2),0,0),(s*(x+w/2),0,0),r,DARK,BAR)
            cylinder('Plate hub',(s*(x-w/2-.004),0,0),(s*(x+w/2+.004),0,0),.045,STEEL,BAR)
        cylinder('Collar',(s*.81,0,0),(s*.84,0,0),.035,ORANGE,BAR)

HANDLE=empty('Close-grip cable handle')
CABLE=None
if args.exercise=='row' and args.view=='motion':
    for s in [-1,1]:
        cylinder('Handle',(s*.09,0,-.055),(s*.09,0,.055),.016,STEEL,HANDLE)
        cylinder('V handle arm',(s*.09,0,0),(0,.09,0),.012,STEEL,HANDLE)
    CABLE=cylinder('Cable',(0,0,0),(0,0,1),.004,DARK)
    cube('Seat',(0,-.10,.42),(.42,.42,.10),PAD)
    for y in [-.23,.03]:
        cube('Seat legs',(0,y,.22),(.32,.06,.40),DARK,.015)
    cube('Machine rail',(0,.68,.045),(.52,2.0,.09),DARK)
    cube('Pulley tower',(0,1.62,.60),(.37,.23,1.1),DARK)
    for i in range(8):
        cube('Weight stack',(0,1.47,.12+i*.055),(.29,.19,.04),STEEL,.005)
    cylinder('Low pulley',(-.07,1.40,.40),(.07,1.40,.40),.075,STEEL)
    plate=cube('Foot support',(0,.86,.18),(.62,.29,.055),PAD)
    plate.rotation_euler.x=math.radians(32)

if args.exercise=='bench' and args.view=='motion':
    cube('Flat bench',(0,-.12,.40),(.28,1.38,.11),PAD,.045)
    for y in [-.60,.35]:
        cube('Bench leg',(0,y,.20),(.075,.09,.35),DARK)
        cube('Bench foot',(0,y,.035),(.50,.11,.07),DARK)


def depth(t):
    if t<.06 or t>.94:return 0
    if t<.46:return .5-.5*math.cos(math.pi*(t-.06)/.4)
    if t<.54:return 1
    return .5+.5*math.cos(math.pi*(t-.54)/.4)


def pose(f):
    d=depth((f-1)/120)
    static=args.view!='motion'
    if static:
        hip=Vector((0,0,.98)); up=Vector((0,0,1)); forward=Vector((0,1,0))
    elif args.exercise=='squat':
        angle=.06+.54*d
        up=Vector((0,math.sin(angle),math.cos(angle))); forward=Vector((0,math.cos(angle),-math.sin(angle)))
        hip=Vector((0,.03-.475*math.sin(angle)+.08*math.cos(angle),.985-.465*d))
    elif args.exercise=='bench':
        hip=Vector((0,.23,.58)); up=Vector((0,-1,0)); forward=Vector((0,0,1))
    else:
        angle=.18-.15*d
        up=Vector((0,math.sin(angle),math.cos(angle))); forward=Vector((0,math.cos(angle),-math.sin(angle)))
        hip=Vector((0,-.1,.58))
    q=frame_quat(up,forward)
    set_pose(BODY,hip,q,frame=f)
    pq=q if args.exercise=='bench' and not static else frame_quat((0,0,1),(0,1,0))
    set_pose(PELVIS,hip,pq,frame=f)
    shoulders=hip+up*.455
    if not static and args.exercise=='squat':
        bar=hip+up*.475-forward*.08
        set_pose(BAR,bar,frame=f)
    elif not static and args.exercise=='bench':
        bar=Vector((0,-.23+.14*d,1.118-.408*d))
        set_pose(BAR,bar,frame=f)
    elif not static:
        handle=Vector((0,.54-.46*d,.95-.10*d))
        set_pose(HANDLE,handle,frame=f)
        a=handle+Vector((0,.09,0)); b=Vector((0,1.40,.40))
        set_pose(CABLE,(a+b)/2,(b-a).to_track_quat('Z','Y'),(1,1,(b-a).length),f)
    for s in [-1,1]:
        h=hip+Vector((s*.135,0,0))
        sh=shoulders+Vector((s*.217,0,0))
        if static:
            ankle=Vector((s*.15,0,.09))
            wrist=Vector((s*.39,0,.94))
            epole=(s*.6,.02,1.18); kpole=(s*.16,1,.5)
        elif args.exercise=='squat':
            ankle=Vector((s*.18,0,.09)); wrist=bar+Vector((s*.40,0,0))
            epole=(s*.55,-.4,shoulders.z-.27); kpole=(s*.25,1,.4)
        elif args.exercise=='bench':
            ankle=Vector((s*.27,.69,.09)); wrist=bar+Vector((s*.43,0,0))
            epole=(s*.43,-.04,.40); kpole=(s*.24,1,.5)
        else:
            ankle=Vector((s*.18,.66,.24)); wrist=handle+Vector((s*.09,0,0))
            epole=(s*.42,-.7,.88); kpole=(s*.16,.3,1.1)
        knee=ik(h,ankle,.46,.44,kpole)
        elbow=ik(sh,wrist,.30,.28,epole)
        bone(PARTS[s,'thigh'],h,knee,(0,1,0),f)
        bone(PARTS[s,'shin'],knee,ankle,(0,1,0),f)
        bone(PARTS[s,'upper_arm'],sh,elbow,forward,f)
        bone(PARTS[s,'forearm'],elbow,wrist,forward,f)
        for n,p in [('knee',knee),('elbow',elbow),('shoulder',sh),('wrist',wrist)]:
            set_pose(JOINTS[s,n],p,frame=f)
        set_pose(HANDS[s],wrist,q,frame=f)
        # Feet stay planted; ankle is the pivot for the row foot support.
        footq=frame_quat((0,-.45,.893),(0,.893,.45)) if args.exercise=='row' and not static else frame_quat((0,0,1),(s*.14,1,0))
        set_pose(FEET[s],ankle,footq,frame=f)


for f in range(1,122):
    pose(f)

scene=bpy.context.scene
scene.frame_start=1;scene.frame_end=120;scene.render.fps=24
scene.render.engine=args.engine
scene.render.resolution_x=960 if args.view=='motion' else 360
scene.render.resolution_y=800 if args.view=='motion' else 540
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGBA'
scene.render.film_transparent=True
scene.world=bpy.data.worlds.new('Studio world')
scene.world.color=(.5,.5,.5)
scene.view_settings.view_transform='Standard'
if args.engine=='BLENDER_WORKBENCH':
    sh=scene.display.shading
    sh.light='STUDIO';sh.studio_light='paint.sl';sh.color_type='MATERIAL'
    sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH'
    sh.curvature_ridge_factor=1.25;sh.curvature_valley_factor=1.05
    sh.show_specular_highlight=True;sh.show_object_outline=False
    scene.display.render_aa='16'
else:
    for name,pos,power,size in [('Key',(3,4,6),650,5),('Fill',(-3,2,3),400,4),('Rim',(1,-4,5),750,3)]:
        light=bpy.data.lights.new(name,'AREA');light.energy=power;light.shape='DISK';light.size=size
        o=bpy.data.objects.new(name,light);bpy.context.collection.objects.link(o);o.location=pos
        o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()

camdata=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',camdata)
bpy.context.collection.objects.link(cam);scene.camera=cam
camdata.type='ORTHO';camdata.lens=48
if args.view!='motion':
    cam.location=(0,6 if args.view=='front' else -6,1.0)
    target=Vector((0,0,.94));camdata.ortho_scale=2.05
else:
    if args.exercise=='squat':
        cam.location=(3.6,5,2.65);target=Vector((0,0,.76));camdata.ortho_scale=2.70
    elif args.exercise=='bench':
        cam.location=(3.4,3.7,3.2);target=Vector((0,-.04,.55));camdata.ortho_scale=2.65
    else:
        cam.location=(3.5,-4.7,2.85);target=Vector((0,.5,.55));camdata.ortho_scale=3.15
    bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=1.08 if args.exercise!='row' else 1.28,
                                      depth=.026,location=(0,.50 if args.exercise=='row' else 0,-.027))
    finish(bpy.context.object,'Studio platform',BASE)
cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
scene['description']='Original Repcendo stylized motion study; muscle regions are schematic, not activation data.'
scene['exercise']=args.exercise
scene['provenance']='Procedural original geometry and animation; no Gym visual media or derived motion used.'
scene['review_status']='Visual prototype; not professionally reviewed exercise instruction.'
scene.frame_set(args.frame if args.view=='motion' else 1)
# Machine-readable checks on the baked native transforms; no visual claims.
if args.view=='motion':
    errors=[]
    for f in range(1,122):
        scene.frame_set(f)
        for s in [-1,1]:
            for part,length in [('thigh',.46),('shin',.44),('upper_arm',.30),('forearm',.28)]:
                error=abs(PARTS[s,part].scale.z-length)
                if error>1e-5: errors.append([f,s,part,error])
    scene.frame_set(1)
    first={o.name:list(o.location) for o in [BODY,PELVIS,*PARTS.values(),*FEET.values(),BAR,HANDLE]}
    scene.frame_set(121)
    seam=max((o.location-Vector(first[o.name])).length for o in [BODY,PELVIS,*PARTS.values(),*FEET.values(),BAR,HANDLE])
    (OUT/'motion-checks.json').write_text(json.dumps({'frames_checked':121,'limb_length_errors':errors,'loop_position_error_m':seam,'review':'Numerical checks only; professional movement review pending'},indent=2))
    assert not errors and seam<1e-6
    scene.frame_set(args.frame)
if args.view=='motion':
    bpy.ops.wm.save_as_mainfile(filepath=str(DELIVER/f'{args.exercise}.blend'))
if args.preview or args.view!='motion':
    scene.render.filepath=str(OUT/(f'motion-{args.frame:04d}.png' if args.view=='motion' and args.frame!=61 else f'{args.view}.png'))
    bpy.ops.render.render(write_still=True)
else:
    scene.render.filepath=str(OUT/'frames'/'frame-')
    (OUT/'frames').mkdir(exist_ok=True)
    bpy.ops.render.render(animation=True)
