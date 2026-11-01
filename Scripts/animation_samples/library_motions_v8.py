"""Standing bilateral curls with reference-matched fixed upper arms and grip."""
import math
from functools import partial
from mathutils import Vector
from library_motions import LibraryMotion
from plan_motions import unit


class LibraryMotionV8(LibraryMotion):
    def __init__(self, env):
        super().__init__(env)
        if self.config['grip']=='pronated' and self.args.sex=='male':
            self.pose_fingers=partial(self.pose_fingers,thumb_clearance=.008)

    def arm(self,s,d,t):
        side=self.SIDES[s]
        shoulder=self.joint('mixamorig:'+side+'Arm')
        u=unit((s*.25,.25,-1))
        forward=Vector((s*.55,1,0));forward=(forward-u*forward.dot(u)).normalized()
        flex=math.radians(18+92*d)
        v=u*math.cos(flex)+forward*math.sin(flex)
        axis=Vector((s,0,0))*(1 if self.config['grip']=='supinated' else -1)
        elbow=shoulder+u*self.L[s,'upper'];wrist=elbow+v*self.L[s,'fore']
        handR,basis=self.hand_rotation(axis,v)
        p='mixamorig:'+side+'Hand';hand_forward=(handR@(self.tail[p]-self.head[p])).normalized()
        align=hand_forward.rotation_difference(v).to_matrix().to_4x4()
        handR,basis=align@handR,align@basis
        self.apply_arm(s,shoulder,elbow,wrist,handR,basis,wrist+handR@self.grip_offsets[s])
