"""RGB estimate drives pickup; rejoin the existing level warehouse route."""
from dataclasses import replace
from fanuc_kinematics import np, fk, ik, LOW, HIGH
from pickup_correction import plan
from u_storage import Frame


def build_guided(result, nominal):
    approach, target, yaw = plan(result, standoff=0.)
    pose=np.asarray(result['pose']);pickup=np.array([pose[0]/1000,-2.2+pose[1]/1000,.7])
    frames=[Frame(t,'VISION_APPROACH',q,.12,pickup.copy(),float(pose[2]),'pallet') for t,q in approach]
    q=frames[-1].q.copy()
    for opening in np.linspace(.12,0,61)[1:]:
        frames.append(Frame(frames[-1].time+2/60,'CLOSE_JAWS',q.copy(),float(opening),pickup.copy(),float(pose[2]),'pallet'))
    def emit(phase,dt):
        p,r=fk(q,(0,0,0))
        angle=float(np.degrees(np.arctan2(r[1,0],r[0,0]))-180)
        angle+=360*round((float(pose[2])-angle)/360)
        frames.append(Frame(frames[-1].time+dt,phase,q.copy(),0.,p+r@[.43,0,-.65],angle,'gripper'))
    emit('ATTACH_ENGINE_KINEMATIC',.04)
    for end,y0,y1,phase in (([target[0],target[1],2.35],yaw,yaw,'LIFT_ENGINE'),([.43,-2.2,2.35],yaw,180.,'VISION_REJOIN')):
        origin,_=fk(q,(0,0,0));end=np.asarray(end)
        for t in np.linspace(0,1,181)[1:]:
            a=t*t*(3-2*t);new=ik(origin+a*(end-origin),y0+a*(y1-y0),q,(0,0,0))
            if np.any(new<LOW) or np.any(new>HIGH):raise ValueError('Joint limit in corrected lift')
            dt=max(3/180,float(np.max(np.abs(np.degrees(new-q))))/15)
            q=new;emit(phase,dt)
    index=next(i for i,f in enumerate(nominal) if f.phase=='CLEAR_PICKUP')
    offset=frames[-1].time-nominal[index-1].time
    frames.extend(replace(f,time=f.time+offset) for f in nominal[index:])
    return frames
