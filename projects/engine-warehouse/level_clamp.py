"""Ideal locating-pin/clamp constraint for kinematic warehouse playback."""
from fanuc_kinematics import np,fk,Rotation

class LevelClamp:
    def __init__(self,position,yaw,frame):
        if frame.opening>1e-5:raise ValueError('Clamp is not closed')
        p,r=fk(frame.q,(0,0,0))
        self.offset=r.T@(np.asarray(position)-p)
        self.orientation=r.T@Rotation.from_euler('z',yaw,degrees=True).as_matrix()
        self.yaw=float(yaw);self.max_tilt=0.

    def sample(self,frame):
        if frame.opening>1e-5:raise ValueError('Clamp opened before seating')
        p,r=fk(frame.q,(0,0,0));rotation=r@self.orientation
        tilt=float(np.degrees(np.arccos(np.clip(rotation[2,2],-1,1))))
        if tilt>.25:raise ValueError(f'Engine tilt {tilt:.3f} deg exceeds 0.25 deg')
        self.max_tilt=max(self.max_tilt,tilt)
        raw=float(np.degrees(np.arctan2(rotation[1,0],rotation[0,0])))
        self.yaw=raw+360*round((self.yaw-raw)/360)
        return tuple(float(v) for v in p+r@self.offset),self.yaw

    def seat(self,frame):
        position,yaw=self.sample(frame)
        error=float(np.linalg.norm(np.asarray(position)-frame.payload))
        yaw_error=abs((yaw-frame.yaw+180)%360-180)
        if error>.005 or yaw_error>.25:raise ValueError(f'Engine is not aligned with rack seat: {error*1000:.2f} mm, {yaw_error:.3f} deg')
        return position,yaw,error
