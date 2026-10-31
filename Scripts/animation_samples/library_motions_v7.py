"""Reference-matched seated unilateral curl and sequential kickback."""
import math
from mathutils import Vector
from library_motions import LibraryMotion
from library_motions_v6 import LibraryMotionV6
from plan_motions import unit


class LibraryMotionV7(LibraryMotionV6):
    def arm(self, s, d, t):
        if self.config['family'] == 'curl':
            return LibraryMotion.arm(self, s, d, t)
        # A full repetition returns to the bent-elbow rest before switching.
        active = (t < .5 and s == -1) or (t >= .5 and s == 1)
        d = math.sin(2*math.pi*t)**2 if active else 0
        side = self.SIDES[s]
        shoulder = self.joint('mixamorig:'+side+'Arm')
        u = unit((s*.42, -1, -.12))
        # Keep the female sculpture's wider hip clear on both waiting sides.
        downward = Vector((s*.25 if self.args.sex == 'female' else 0,0,-1))
        downward = (downward-u*downward.dot(u)).normalized()
        flex = math.radians(90-82*d)
        v = u*math.cos(flex)+downward*math.sin(flex)
        axis = s*v.cross(Vector((-s,0,0)))
        elbow = shoulder+u*self.L[s,'upper']
        wrist = elbow+v*self.L[s,'fore']
        handR,basis = self.hand_rotation(axis,v)
        p = 'mixamorig:'+side+'Hand'
        forward = (handR@(self.tail[p]-self.head[p])).normalized()
        align = forward.rotation_difference(v).to_matrix().to_4x4()
        handR,basis = align@handR,align@basis
        self.apply_arm(s,shoulder,elbow,wrist,handR,basis,wrist+handR@self.grip_offsets[s])
