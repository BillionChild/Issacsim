"""Calibrated depth point clouds; no case labels or live object transforms."""
from fanuc_kinematics import np, Rotation
from scipy.spatial import cKDTree
from pathlib import Path

ORIGIN=np.array([0.,-2.2,.7])
REFERENCE=Path(__file__).resolve().parents[2]/'outputs/engine-depth/reference.npz'

class DepthPredictor:
    def __init__(self,path=REFERENCE):
        if not path.exists():raise RuntimeError('Engine depth reference missing: run calibrate_engine_depth.py')
        with np.load(path) as data:self.data={k:data[k] for k in data.files}

    def predict(self,rgb,depth):
        from engine_guided import LIMITS
        crop=np.asarray(rgb)[160:464,80:432,:3]
        if np.mean(np.max(crop,axis=2)<3)>.04:
            return dict(accepted=False,pose=[0,0,0],pose6=None,reason='HOLD: missing / dark engine image',method='engine_depth_registration')
        points=engine_surface(world_points(depth,self.data['camera_to_world'],float(self.data['focal_pixels'])))
        pose,rmse=register(self.data['points'],points)
        reason='ENGINE_POSE_ESTIMATED'
        if rmse>.004:reason='HOLD: engine shape registration residual too large'
        elif np.any(np.abs(pose)>LIMITS):reason='HOLD: engine pose outside validated correction envelope'
        return dict(accepted=reason=='ENGINE_POSE_ESTIMATED',pose=pose[[0,1,5]].tolist(),pose6=pose.tolist(),
                    reason=reason,method='engine_depth_registration',registration_rmse_mm=rmse*1000,depth_points=len(points))

def annotated_engine(rgb,result,path):
    from PIL import Image,ImageDraw
    im=Image.fromarray(np.asarray(rgb)[:,:,:3].astype('uint8'));draw=ImageDraw.Draw(im)
    draw.rectangle((0,0,512,92),fill=(20,24,30))
    draw.text((10,8),'ENGINE pose from depth | pallet excluded',fill='white')
    if result.get('accepted'):
        x,y,z,rx,ry,rz=result['pose6']
        draw.text((10,28),f'XYZ {x:+.1f} {y:+.1f} {z:+.1f} mm',fill='white')
        draw.text((10,46),f'Roll/Pitch/Yaw {rx:+.2f} {ry:+.2f} {rz:+.2f} deg',fill='white')
    draw.text((10,68),result['reason'],fill='white');im.save(path)

def world_points(depth,camera_to_world,focal_pixels):
    depth=np.asarray(depth).squeeze();h,w=depth.shape
    yy,xx=np.indices((h,w));valid=np.isfinite(depth)&(depth>.02)&(depth<20)
    z=depth[valid]
    # USD camera looks down -Z, with +Y up. Pixel centers use half offsets.
    camera=np.column_stack(((xx[valid]+.5-w/2)*z/focal_pixels,
                            -(yy[valid]+.5-h/2)*z/focal_pixels,-z,np.ones(len(z))))
    return (camera@np.asarray(camera_to_world))[:,:3]

def engine_surface(points):
    # Fixed workspace crop of the upper engine; excludes low pallet/fixture.
    p=np.asarray(points)
    keep=(np.abs(p[:,0])<.38)&(np.abs(p[:,1]+2.2)<.40)&(p[:,2]>1.10)&(p[:,2]<1.55)
    return p[keep]

def register(reference,observed):
    """Trimmed point-to-point ICP. Returns reference->observed rigid motion."""
    ref=np.asarray(reference);obs=np.asarray(observed)
    if len(ref)<150 or len(obs)<150:raise ValueError('HOLD: insufficient engine depth points')
    ref=ref[::max(1,len(ref)//3500)];obs=obs[::max(1,len(obs)//6000)]
    tree=cKDTree(obs);r=np.eye(3);t=np.median(obs,axis=0)-np.median(ref,axis=0)
    for _ in range(100):
        transformed=ref@r.T+t;dist,idx=tree.query(transformed)
        keep=dist<min(.06,float(np.quantile(dist,.85)))
        if keep.sum()<100:raise ValueError('HOLD: engine depth registration has insufficient overlap')
        a=transformed[keep];b=obs[idx[keep]];am=a.mean(0);bm=b.mean(0)
        u,_,vt=np.linalg.svd((a-am).T@(b-bm));delta=vt.T@u.T
        if np.linalg.det(delta)<0:vt[-1]*=-1;delta=vt.T@u.T
        shift=bm-delta@am;r=delta@r;t=delta@t+shift
        if np.linalg.norm(shift)<1e-7 and np.linalg.norm(delta-np.eye(3))<1e-7:break
    dist,_=tree.query(ref@r.T+t)
    rmse=float(np.sqrt(np.mean(np.sort(dist)[:int(len(dist)*.85)]**2)))
    offset=r@ORIGIN+t-ORIGIN
    angles=Rotation.from_matrix(r).as_euler('xyz',degrees=True)
    return np.r_[offset*1000,angles],rmse
