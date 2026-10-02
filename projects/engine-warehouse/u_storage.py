"""One-shot, gated, kinematic engine transfer for the U layout."""
from dataclasses import dataclass
from bisect import bisect_right
import math
from fanuc_kinematics import np, fk, ik

# Pickup-ready hover: flange (.43, -2.2, 2.35), level tool yaw 180.
IDLE=np.radians([16.9378758384079,20.620693292315774,35.933043437943965,94.59809662178361,-106.31944379640223,-74.02800640819173])
PICK=np.array([0.,-2.2,.7])
CELL=np.array([.6,3.,.66])


@dataclass
class Frame:
    time:float
    phase:str
    q:np.ndarray
    opening:float
    payload:np.ndarray
    yaw:float
    owner:str


def build_transfer():
    frames=[];q=IDLE.copy();opening=.12;owner='pallet';yaw=0.
    def emit(phase,dt):
        nonlocal yaw
        if owner=='gripper':
            p,r=fk(q,(0,0,0));payload=p+r@[.43,0,-.65]
            raw=np.degrees(np.arctan2(r[1,0],r[0,0]))-180
            yaw=raw+360*round((yaw-raw)/360)
        else:payload=PICK.copy() if owner=='pallet' else CELL.copy()
        frames.append(Frame(frames[-1].time+dt if frames else 0.,phase,q.copy(),opening,payload.copy(),yaw,owner))
    def smooth(t):return t*t*(3-2*t)
    def move(position,start_yaw,end_yaw,phase):
        nonlocal q
        start,_=fk(q,(0,0,0));target=np.array(position)
        n=max(100,int(abs(end_yaw-start_yaw)/.3),int(np.linalg.norm(target-start)/.006))
        for t in np.linspace(0,1,n+1)[1:]:
            a=smooth(t)
            new=ik(start+a*(target-start),start_yaw+a*(end_yaw-start_yaw),q,(0,0,0))
            dt=max(3/n,float(np.max(np.abs(np.degrees(new-q))))/20)
            q=new;emit(phase,dt)
    def jaws(target,phase):
        nonlocal opening
        start=opening
        for t in np.linspace(0,1,61)[1:]:
            opening=start+smooth(t)*(target-start);emit(phase,2/60)

    emit('WAIT_PICKUP_OK',0)
    move([.43,-2.2,1.35],180,180,'LOWER_OPEN_JAWS')
    jaws(0.,'CLOSE_JAWS');owner='gripper';emit('ATTACH_ENGINE_KINEMATIC',.04)
    move([.43,-2.2,2.35],180,180,'LIFT_ENGINE')
    move([1.8,-.8,2.35],180,270,'CLEAR_PICKUP')
    move([1.8,.8,2.35],270,360,'PASS_ABOVE_OUTBOUND')
    move([.6,1.6,2.35],360,450,'ALIGN_RACK')
    move([.6,1.6,1.45],450,450,'LOWER_AT_RACK_FRONT')
    move([.6,2.57,1.45],450,450,'INSERT_ENGINE')
    move([.6,2.57,1.31],450,450,'SEAT_ENGINE')
    owner='cell';emit('RELEASE_ON_CRADLE',.04);jaws(.12,'OPEN_JAWS')
    move([.6,1.6,1.31],450,450,'WITHDRAW')
    move([.6,1.6,2.35],450,450,'RAISE_CLEAR')
    move([1.8,.8,2.35],450,360,'RETURN_NORTH')
    move([1.8,-.8,2.35],360,270,'RETURN_SOUTH')
    move([.43,-2.2,2.35],270,180,'RETURN_PICKUP_SIDE')
    emit('READY_NEXT_ENGINE',.04)
    return frames


class StorageTransfer:
    def __init__(self,frames):
        self.frames=frames;self.times=[f.time for f in frames];self.reset()
    def reset(self):
        self.state='WAITING';self.elapsed=0.;self.cell_occupied=False
    def try_start(self,cycle):
        if self.state!='WAITING' or self.cell_occupied or not cycle.pickup_allowed:return False
        if cycle.result!='OK' or cycle.state!='READY_PICKUP' or not np.allclose(cycle.position,PICK,atol=1e-6):return False
        self.state='MOVING';return True
    def step(self,dt):
        if not math.isfinite(dt) or dt<0:raise ValueError('dt must be finite and nonnegative')
        if self.state!='MOVING':return
        self.elapsed=min(self.times[-1],self.elapsed+dt)
        self.cell_occupied=self.sample().owner=='cell'
        if self.elapsed>=self.times[-1]:self.state='DONE'
    def sample(self):
        i=max(0,min(len(self.frames)-1,bisect_right(self.times,self.elapsed)-1));a=self.frames[i]
        if i==len(self.frames)-1:return a
        b=self.frames[i+1];t=(self.elapsed-a.time)/(b.time-a.time)
        return Frame(self.elapsed,a.phase,a.q+t*(b.q-a.q),a.opening+t*(b.opening-a.opening),a.payload+t*(b.payload-a.payload),a.yaw+t*(b.yaw-a.yaw),a.owner)
