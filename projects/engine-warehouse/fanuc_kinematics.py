"""Numerical FK/IK for the official FANUC 210L link convention; kinematic only."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'.venv/asset-tools'))
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
OFFSETS=[(0,0,.67),(.312,0,0),(0,0,1.075),(0,0,.225),(1.73,0,0),(0,0,0)]
AXES=np.array([(0,0,1),(0,1,0),(0,-1,0),(-1,0,0),(0,-1,0),(-1,0,0)])
LOW=np.radians([-185,-60,-79,-360,-125,-360]);HIGH=np.radians([185,76,180,360,125,360])
IDLE=np.radians([180,-20,-35,0,0,0])
BASE_POSITION=np.array([2.1,2.2,0.])

def fk(q,base_position=None):
    r=Rotation.from_euler('z',-90,degrees=True).as_matrix();p=np.array(BASE_POSITION if base_position is None else base_position,dtype=float)
    for xyz,axis,angle in zip(OFFSETS,AXES,q):
        p=p+r@xyz;r=r@Rotation.from_rotvec(axis*angle).as_matrix()
    return p+r@np.array([.24,0,0]),r

def ik(position,yaw,seed,base_position=None):
    base=BASE_POSITION if base_position is None else np.asarray(base_position)
    target=Rotation.from_euler('z',yaw,degrees=True).as_matrix()
    def residual(q):
        p,r=fk(q,base)
        return np.r_[p-position,Rotation.from_matrix(target.T@r).as_rotvec()]
    az=np.arctan2(position[1]-base[1],position[0]-base[0])+np.pi/2
    seeds=[seed]+[np.array([az,np.radians(j2),np.radians(j3),0,np.radians(-60),0]) for j2,j3 in [(0,30),(30,70),(-30,-30),(45,120)]]
    for guess in seeds:
        result=least_squares(residual,np.clip(guess,LOW+1e-8,HIGH-1e-8),bounds=(LOW,HIGH),ftol=1e-10,xtol=1e-10,gtol=1e-10,max_nfev=180)
        error=residual(result.x)
        if np.linalg.norm(error)<2e-4:return result.x
    raise RuntimeError(f'IK failed at {position}, yaw={yaw}, error={error}')

if __name__=='__main__':
    q=IDLE.copy()
    for p,yaw in [([2.7,0,1.7],180),([2.23,0,1.35],180),([2.8,.2,1.65],0),([3.,1.2,1.45],0),([3.82,1.2,1.31],0)]:
        q=ik(np.array(p),yaw,q);print(p,np.round(np.degrees(q),2),flush=True)
