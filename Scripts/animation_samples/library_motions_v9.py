"""Reference-matched seated curls; thighs support the concentration-curl arm."""
import math
from mathutils import Vector, Matrix
from library_motions_v6 import LibraryMotionV6
from plan_motions import unit
from deformation_rig import pose_forearm_twist

class LibraryMotionV9(LibraryMotionV6):
    def leg(self,s,d,t):
        if not self.config.get('thigh_support'):return super().leg(s,d,t)
        side=self.SIDES[s];prefix='mixamorig:'+side
        hip=self.joint(prefix+'UpLeg');a,b=self.L[s,'thigh'],self.L[s,'shin']
        ankle=Vector((s*.34,.35,self.ankle_z));footR=Matrix.Identity(4)
        knee=self.ik(hip,ankle,a,b,hip+Vector((s*.60,1,-.2)))
        self.orient(prefix+'UpLeg',hip,knee,(1,0,0),self.f)
        self.orient(prefix+'Leg',knee,ankle,(1,0,0),self.f)
        self.setbone(prefix+'Foot',ankle,footR,self.f)
        self.setbone(prefix+'ToeBase',ankle+footR@(self.head[prefix+'ToeBase']-self.head[prefix+'Foot']),footR,self.f)
        self.length_errors.extend([abs((knee-hip).length-a),abs((ankle-knee).length-b)])
        self.pose_data[side]=dict(hip=hip,knee=knee,ankle=ankle,footR=footR)

    def arm(self,s,d,t):
        side=self.SIDES[s];shoulder=self.joint('mixamorig:'+side+'Arm')
        supported=self.config.get('thigh_support')
        if supported:
            # Individual upper-arm placement preserves bone lengths.
            u=unit((s*.23,-.02,-1)) if self.args.sex=="female" else unit((s*.06,.12,-1))
        else:u=unit((s*.45,.12,-1))
        elbow=shoulder+u*self.L[s,'upper']
        if supported and side!='Left':
            target=self.pose_data[side]['knee']+Vector((-.22,.03,.07 if self.args.sex=="female" else .10))
            elbow=self.ik(shoulder,target,self.L[s,'upper'],self.L[s,'fore'],shoulder+Vector((s*.5,-.15,-.4)))
            v=(target-elbow).normalized()
            axis=Vector((-s,0,0))
        else:
            forward=Vector((0 if supported else s*.55,1,0));forward=(forward-u*forward.dot(u)).normalized()
            flex=math.radians((25+93*d) if supported else (18+92*d));v=u*math.cos(flex)+forward*math.sin(flex)
            axis=Vector((s,0,0))
        wrist=elbow+v*self.L[s,'fore']
        hand_direction=(v*.6+Vector((0,0,-1))*.4).normalized() if supported and side!='Left' else v
        handR,basis=self.hand_rotation(axis,hand_direction)
        p='mixamorig:'+side+'Hand';forward=(handR@(self.tail[p]-self.head[p])).normalized()
        align=forward.rotation_difference(hand_direction).to_matrix().to_4x4();handR,basis=align@handR,align@basis
        self.open=bool(supported and side!='Left')
        try:self.apply_arm(s,shoulder,elbow,wrist,handR,basis,wrist if self.open else wrist+handR@self.grip_offsets[s])
        finally:self.open=False
        if supported and side!='Left':
            # Shared free-hand default follows the forearm. Here the reference
            # rests the forearm on the thigh with a relaxed hanging hand.
            self.setbone(p,wrist,handR,self.f)
            pose_forearm_twist(self.rig,side,self.f)
            self.pose_fingers(self.rig,self.hand_chains,self.hand_centers,side,self.f,closed=False)
