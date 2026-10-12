"""Estimate-only pregrasp planning; no injected pose/case inputs."""
from fanuc_kinematics import np,ik,fk,LOW,HIGH
from u_storage import IDLE

STANDOFF=.35  # Default approach stops above contact; contact lab explicitly requests zero.

def plan(result,standoff=STANDOFF):
    pose=np.asarray(result.get('pose',[]),dtype=float)
    if not result.get('accepted') or pose.shape!=(3,) or not np.isfinite(pose).all():
        raise ValueError('HOLD: fresh accepted estimate required')
    if np.any(np.abs(pose)>[40,25,3]):raise ValueError('HOLD: correction exceeds training envelope')
    dx,dy,angle=pose;theta=np.radians(angle)
    target=np.array([dx/1000+.43*np.cos(theta),-2.2+dy/1000+.43*np.sin(theta),1.35+standoff])
    q=IDLE.copy();frames=[(0.,q.copy())];start,_=fk(q,(0,0,0))
    for end,y0,y1 in ((np.array([target[0],target[1],2.35]),180,180+angle),(target,180+angle,180+angle)):
        origin=start.copy()
        for t in np.linspace(0,1,81)[1:]:
            a=t*t*(3-2*t);new=ik(origin+a*(end-origin),y0+a*(y1-y0),q,(0,0,0))
            if np.any(new<LOW) or np.any(new>HIGH):raise ValueError('HOLD: joint limit')
            dt=max(3/80,float(np.max(np.abs(np.degrees(new-q))))/15)
            frames.append((frames[-1][0]+dt,new.copy()));q=new
        start=end
    return frames,target,180+angle

def joint_attributes(stage):
    path='/World/Robot/Base';attrs=[]
    for i,axis in enumerate('ZYYXYX',1):
        path+=f'/J{i}';attrs.append(stage.GetPrimAtPath(path).GetAttribute('xformOp:rotate'+axis))
    return attrs

def write_joints(attrs,q):
    for attr,v,sign in zip(attrs,q,(1,1,-1,-1,-1,-1)):attr.Set(float(np.degrees(v))*sign)

def clearance(stage,frames):
    """Sample conservative geometry on a private stage; never move the live robot here."""
    from pxr import Usd,UsdGeom
    import itertools
    from storage_geometry import box,overlap,mesh_cube_overlap
    clone=Usd.Stage.Open(stage.Flatten());attrs=joint_attributes(clone)
    bounds=UsdGeom.BBoxCache(Usd.TimeCode.Default(),['default','render'])
    robot=[];obstacles=[]
    def item(p):
        r=bounds.ComputeUntransformedBound(p).ComputeAlignedRange()
        return p,np.array(list(itertools.product(*zip(r.GetMin(),r.GetMax()))))
    for p in clone.Traverse():
        path=str(p.GetPath())
        if not(p.IsA(UsdGeom.Mesh) or p.IsA(UsdGeom.Cube) or p.IsA(UsdGeom.Cylinder)):continue
        if path.startswith('/World/Robot/'):robot.append(item(p))
        elif path.startswith(('/World/Conveyors/','/World/Rack/','/World/OutboundCarrier/','/World/Transfers/','/World/TestLoad/')):obstacles.append(item(p))
    xc=UsdGeom.XformCache()
    obs=[box(local,np.array(xc.GetLocalToWorldTransform(p))) for p,local in obstacles]
    lo=np.array([b[0] for b in obs]);hi=np.array([b[1] for b in obs])
    for index,(_,q) in enumerate(frames):
        write_joints(attrs,q);xc=UsdGeom.XformCache()
        for p,local in robot:
            rb=box(local,np.array(xc.GetLocalToWorldTransform(p)))
            if rb[0][2]<-.005:raise ValueError('HOLD: robot below floor')
            for j in np.where(np.all(np.minimum(rb[1],hi)-np.maximum(rb[0],lo)>.0005,axis=1))[0]:
                if not overlap(rb,obs[j]):continue
                other=obstacles[j][0]
                if p.IsA(UsdGeom.Mesh) and other.IsA(UsdGeom.Cube) and not mesh_cube_overlap(p,other,xc):continue
                if p.IsA(UsdGeom.Cube) and other.IsA(UsdGeom.Mesh) and not mesh_cube_overlap(other,p,xc):continue
                raise ValueError(f'HOLD: sampled interference at {index}: {p.GetPath()} / {other.GetPath()}')
    return dict(samples=len(frames),result='clear',scope='sampled robot/environment; no self-collision, swept-volume or physics proof')
