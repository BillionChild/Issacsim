"""Outbound motion candidate. Separate from the active inbound controller."""
from u_storage import Frame,IDLE,CELL
from fanuc_kinematics import np,fk,ik
OUTBOUND=np.array([2.5,0.,.85])

def build_transfer(cell=CELL):
    cell=np.asarray(cell,dtype=float); dz=float(cell[2]-CELL[2])
    frames=[];q=IDLE.copy();opening=.12;owner='cell';yaw=90.
    def emit(phase,dt):
        nonlocal yaw
        if owner=='gripper':
            p,r=fk(q,(0,0,0));payload=p+r@[.43,0,-.65]
            raw=np.degrees(np.arctan2(r[1,0],r[0,0]))-180
            yaw=raw+360*round((yaw-raw)/360)
        else:payload=OUTBOUND.copy() if owner=='outbound' else cell.copy()
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


    emit('WAIT_OUTBOUND_REQUEST',0)
    move([1.8,-.8,2.35],180,270,'OUT_CLEAR_PICKUP')
    move([1.8,.8,2.35],270,360,'OUT_PASS_EAST')
    move([.6,1.6,2.35],360,450,'OUT_ALIGN_CELL')
    move([cell[0],1.6,1.31+dz],450,450,'OUT_LOWER_CELL_FRONT')
    move([cell[0],cell[1]-.43,1.31+dz],450,450,'OUT_INSERT_OPEN_JAWS')
    jaws(0.,'OUT_CLOSE_JAWS');owner='gripper';emit('OUT_ATTACH',.04)
    move([cell[0],cell[1]-.43,1.45+dz],450,450,'OUT_LIFT_FROM_CELL')
    move([cell[0],1.6,1.45+dz],450,450,'OUT_WITHDRAW_ENGINE')
    move([.6,1.6,2.35],450,450,'OUT_RAISE_CLEAR')
    move([1.8,.8,2.35],450,360,'OUT_TO_CARRIER')
    move([2.07,0,2.35],360,360,'OUT_ABOVE_CARRIER')
    move([2.07,0,1.54],360,360,'OUT_PRESEAT_ENGINE')
    jaws(.035,'OUT_RELIEVE_JAWS')
    move([2.07,0,1.50],360,360,'OUT_SEAT_ENGINE')
    owner='outbound';emit('OUT_RELEASE',.04);jaws(.12,'OUT_OPEN_JAWS')
    move([2.07,0,2.35],360,360,'OUT_CLEAR_FRAME')
    move([1.8,-.8,2.35],360,270,'OUT_RETURN_EAST')
    move([.43,-2.2,2.35],270,180,'OUT_RETURN_READY')
    emit('OUT_READY',.04)
    return frames
