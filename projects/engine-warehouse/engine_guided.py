"""Six-axis engine pose -> grip transform -> lift -> level -> nominal rack route."""
from dataclasses import replace
from fanuc_kinematics import np,Rotation,fk,ik,LOW,HIGH
from u_storage import Frame,IDLE

LIMITS=np.array([40,25,30,3,3,3])  # mm, mm, mm, roll/pitch/yaw degrees
GRIP_OFFSET=np.array([.43,0.,-.65])
R180=Rotation.from_euler('z',180,degrees=True).as_matrix()

def build_engine_guided(result,nominal):
    pose=np.asarray(result.get('pose6',[]),dtype=float)
    if not result.get('accepted') or pose.shape!=(6,) or not np.isfinite(pose).all():
        raise ValueError('HOLD: fresh accepted engine pose required')
    if np.any(np.abs(pose)>LIMITS):raise ValueError('HOLD: engine pose outside validated correction envelope')
    origin=np.array([0.,-2.2,.7])+pose[:3]/1000
    engine_r=Rotation.from_euler('xyz',pose[3:],degrees=True).as_matrix()
    grip_r=engine_r@R180;target=origin-grip_r@GRIP_OFFSET
    q=IDLE.copy();frames=[]
    def emit(phase,dt,owner='pallet',opening=.12):
        p,r=fk(q,(0,0,0));er=r@R180
        payload=origin.copy() if owner=='pallet' else p+r@GRIP_OFFSET
        yaw=float(Rotation.from_matrix(er).as_euler('xyz',degrees=True)[2])
        frames.append(Frame(frames[-1].time+dt if frames else 0.,phase,q.copy(),opening,payload,yaw,owner))
    def move(position,rotation,phase,owner='pallet'):
        nonlocal q
        start,rs=fk(q,(0,0,0));rv=Rotation.from_matrix(rs.T@rotation).as_rotvec()
        for t in np.linspace(0,1,121)[1:]:
            a=t*t*(3-2*t)
            r=rs@Rotation.from_rotvec(rv*a).as_matrix()
            new=ik(start+a*(np.asarray(position)-start),r,q,(0,0,0))
            if np.any(new<LOW) or np.any(new>HIGH):raise ValueError('HOLD: engine correction joint limit')
            dt=max(3/120,float(np.max(np.abs(np.degrees(new-q))))/15)
            q=new;emit(phase,dt,owner,0. if owner=='gripper' else .12)
    emit('ENGINE_OBSERVE',0.)
    move([target[0],target[1],2.35],grip_r,'ENGINE_ALIGN_ABOVE')
    move(target,grip_r,'ENGINE_APPROACH')
    for opening in np.linspace(.12,0,61)[1:]:emit('CLOSE_JAWS',2/60,opening=float(opening))
    emit('ATTACH_ENGINE_KINEMATIC',.04,'gripper',0.)
    move([target[0],target[1],2.35],grip_r,'LIFT_ENGINE_POSE','gripper')
    move([.43,-2.2,2.35],R180,'LEVEL_ENGINE_IN_AIR','gripper')
    index=next(i for i,f in enumerate(nominal) if f.phase=='CLEAR_PICKUP')
    offset=frames[-1].time-nominal[index-1].time
    frames.extend(replace(f,time=f.time+offset) for f in nominal[index:])
    return frames
