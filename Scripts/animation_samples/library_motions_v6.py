"""Batch 006: fixed-elbow extensions, bent-arm raises and elbow-led rows."""
import math
from mathutils import Vector, Matrix
from library_motions import LibraryMotion
from plan_motions import unit


class LibraryMotionV6(LibraryMotion):
    def equipment(self):
        super().equipment()
        if self.seated:
            # Flat bench: long pad, longitudinal beam, two end supports and feet.
            import bpy
            for name in ('Seat pedestal','Seat base'):
                bpy.data.objects.remove(self.items.pop(name), do_unlink=True)
            pad=self.items['Seat cushion']
            pad.location.y=-.32
            pad.scale.y *= 3.25
            self.block('Bench longitudinal frame',(0,-.32,.35),(.09,1.12,.10))
            for y in (-.83,.16):
                self.block('Bench leg '+str(y),(0,y,.20),(.12,.14,.32))
                self.block('Bench foot '+str(y),(0,y,.04),(.60,.24,.08))

    def leg(self,s,d,t):
        if not (self.seated and self.config['family']=='kickback'):
            return super().leg(s,d,t)
        side=self.SIDES[s];prefix='mixamorig:'+side
        hip=self.joint(prefix+'UpLeg');a,b=self.L[s,'thigh'],self.L[s,'shin']
        ankle=Vector((s*.42,.58,self.ankle_z));footR=Matrix.Identity(4)
        knee=self.ik(hip,ankle,a,b,hip+Vector((s*.45,1,-.2)))
        self.orient(prefix+'UpLeg',hip,knee,(1,0,0),self.f)
        self.orient(prefix+'Leg',knee,ankle,(1,0,0),self.f)
        self.setbone(prefix+'Foot',ankle,footR,self.f)
        toe=ankle+footR@(self.head[prefix+'ToeBase']-self.head[prefix+'Foot'])
        self.setbone(prefix+'ToeBase',toe,footR,self.f)
        self.length_errors.extend([abs((knee-hip).length-a),abs((ankle-knee).length-b)])
        self.pose_data[side]=dict(hip=hip,knee=knee,ankle=ankle,footR=footR)

    def arm(self,s,d,t):
        c=self.config
        if c.get('unilateral') and self.SIDES[s]!=c['unilateral']:
            if not self.seated:
                return super().arm(s,d,t)
            shoulder=self.joint('mixamorig:'+self.SIDES[s]+'Arm')
            u=unit((s*.75,.10,-1));v=unit((s*.65,.10,-1))
            elbow=shoulder+u*self.L[s,'upper'];wrist=elbow+v*self.L[s,'fore']
            handR,basis=self.hand_rotation(Vector((0,1,0)),v)
            self.open=True
            try:self.apply_arm(s,shoulder,elbow,wrist,handR,basis,wrist)
            finally:self.open=False
            return
        side=self.SIDES[s]
        if c['family']=='overhead_raise':
            sn='mixamorig:'+side+'Shoulder';sp,sr=self.body[sn]
            sr=sr@Matrix.Rotation(-s*.40*d,4,'Y')
            self.setbone(sn,sp,sr,self.f);self.body[sn]=(sp,sr)
        shoulder=self.joint('mixamorig:'+side+'Arm')
        if c['family']=='kickback':
            # Upper arm remains beside the hinged torso; elbow alone extends.
            u=unit((s*.70,-1,-.12))
            clearance = 1.0 if self.seated else (.25 if self.args.sex == 'female' and s == 1 else 0)
            downward=Vector((s*clearance,0,-1));downward=(downward-u*downward.dot(u)).normalized()
            flex=math.radians(90-82*d)
            v=u*math.cos(flex)+downward*math.sin(flex)
            palm=Vector((-s,0,0));axis=s*v.cross(palm)
        elif c['family']=='bent_lateral':
            angle=.28+1.25*d
            u=unit((s*math.sin(angle),0,-math.cos(angle)))
            v=Vector((0,1,0))
            palm=Vector((0,0,-1));axis=s*v.cross(palm)
        elif c['family']=='overhead_raise':
            angle=.48+2.47*d
            u=unit((s*.32,math.sin(angle),-math.cos(angle)))
            v=unit((s*.16,math.sin(angle+.04),-math.cos(angle+.04)))
            axis=Vector((-s,0,0))
        elif c['family']=='upright_row':
            # Shoulder-height demonstration envelope, not a human ROM limit.
            # Reference observations and stage comparisons: motion-references/.
            angle=.26+1.20*d
            u=unit((s*math.sin(angle),.24,-math.cos(angle)))
            v=unit((-s*(.10+.65*d),.60+.25*d,-1+.50*d))
            axis=Vector((-s,0,0))
        else:
            raise ValueError('Unknown v6 family')
        elbow=shoulder+u*self.L[s,'upper'];wrist=elbow+v*self.L[s,'fore']
        handR,basis=self.hand_rotation(axis,v)
        p='mixamorig:'+side+'Hand';forward=(handR@(self.tail[p]-self.head[p])).normalized()
        align=forward.rotation_difference(v).to_matrix().to_4x4()
        handR,basis=align@handR,align@basis
        target=wrist+handR@self.grip_offsets[s]
        self.apply_arm(s,shoulder,elbow,wrist,handR,basis,target)
