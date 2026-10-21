"""Ideal locating-pin/clamp constraint for kinematic warehouse playback."""
from fanuc_kinematics import np,fk,Rotation

class LevelClamp:
    def __init__(self,position,yaw,frame,roll=0.,pitch=0.):
        if frame.opening>1e-5:raise ValueError('Clamp is not closed')
        p,r=fk(frame.q,(0,0,0))
        self.offset=r.T@(np.asarray(position)-p)
        initial=Rotation.from_euler('xyz',[roll,pitch,yaw],degrees=True).as_matrix()
        self.orientation=r.T@initial
        self.tilt_limit=float(np.degrees(np.arccos(np.clip(initial[2,2],-1,1))))+.25
        self.roll=roll;self.pitch=pitch;self.tilt=0.
        self.yaw=float(yaw);self.max_tilt=0.

    def sample(self,frame):
        if frame.opening>1e-5:raise ValueError('Clamp opened before seating')
        p,r=fk(frame.q,(0,0,0));rotation=r@self.orientation
        tilt=float(np.degrees(np.arccos(np.clip(rotation[2,2],-1,1))))
        if tilt>self.tilt_limit:raise ValueError(f'Engine tilt {tilt:.3f} deg exceeds allowed pickup tilt')
        self.tilt=tilt
        self.roll,self.pitch,_=Rotation.from_matrix(rotation).as_euler('xyz',degrees=True)
        self.max_tilt=max(self.max_tilt,tilt)
        raw=float(np.degrees(np.arctan2(rotation[1,0],rotation[0,0])))
        self.yaw=raw+360*round((self.yaw-raw)/360)
        return tuple(float(v) for v in p+r@self.offset),self.yaw

    def seat(self,frame):
        position,yaw=self.sample(frame)
        if self.tilt>.25:raise ValueError(f'Engine not leveled at rack seat: {self.tilt:.3f} deg')
        error=float(np.linalg.norm(np.asarray(position)-frame.payload))
        yaw_error=abs((yaw-frame.yaw+180)%360-180)
        if error>.005 or yaw_error>.25:raise ValueError(f'Engine is not aligned with rack seat: {error*1000:.2f} mm, {yaw_error:.3f} deg')
        return position,yaw,error
