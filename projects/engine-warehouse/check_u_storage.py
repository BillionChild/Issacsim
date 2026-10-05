"""Sample geometry and carried interpolation; report what is not covered."""
import os,sys,itertools,json
from pathlib import Path
from build_u_storage_demo import load_transfer,ROOT,np
from fanuc_kinematics import fk
from u_storage import StorageTransfer
lib=next(Path('C:/isaacsim/extscache').glob('omni.usd.libs-*'));sys.path.insert(0,str(lib));dll=os.add_dll_directory(str(lib/'bin'))
from pxr import Usd,UsdGeom
from storage_geometry import box,overlap,mesh_cube_overlap

def check(outbound=False):
    if outbound:
        from build_u_outbound_demo import load_transfer as loader
    else:loader=load_transfer
    name='u_outbound_motion_preview.usdc' if outbound else 'u_storage_motion_preview.usdc'
    s=Usd.Stage.Open(str(ROOT/'external_assets/engines/caterham_duratec/usd'/name))
    cache=UsdGeom.BBoxCache(Usd.TimeCode.Default(),['default','render'])
    robot=[];others=[]
    for p in s.Traverse():
        path=str(p.GetPath())
        if path.startswith(('/World/CarriedEngine/','/World/Flow/','/World/Zones/')):continue
        if not(p.IsA(UsdGeom.Mesh) or p.IsA(UsdGeom.Cube) or p.IsA(UsdGeom.Cylinder)):continue
        e=cache.ComputeUntransformedBound(p).ComputeAlignedRange()
        item=(p,np.array(list(itertools.product(*zip(e.GetMin(),e.GetMax())))))
        (robot if path.startswith('/World/Robot/') else others).append(item)
    payload=s.GetPrimAtPath('/World/CarriedEngine');e=cache.ComputeUntransformedBound(payload).ComputeAlignedRange()
    payload_local=np.array(list(itertools.product(*zip(e.GetMin(),e.GetMax()))))
    hits={};payload_hits={};below=set();broad=0
    phase=s.GetDefaultPrim().GetAttribute('demo:phase')
    times=np.arange(0,s.GetEndTimeCode()/30,.2)
    for sec in times:
        transforms=UsdGeom.XformCache(float(sec)*30);name=phase.Get(float(sec)*30)
        boxes=[box(local,np.array(transforms.GetLocalToWorldTransform(p))) for p,local in others]
        lo=np.array([b[0] for b in boxes]);hi=np.array([b[1] for b in boxes])
        for p,local in robot:
            rb=box(local,np.array(transforms.GetLocalToWorldTransform(p)))
            if rb[0][2]<-.005:below.add((name,str(p.GetPath())))
            for j in np.where(np.all(np.minimum(rb[1],hi)-np.maximum(rb[0],lo)>.0005,axis=1))[0]:
                if not overlap(rb,boxes[j]):continue
                broad+=1;other=others[j][0]
                if not p.IsA(UsdGeom.Mesh) or not other.IsA(UsdGeom.Cube) or mesh_cube_overlap(p,other,transforms):
                    hits.setdefault((name,str(p.GetPath()),str(other.GetPath())),float(sec))
        pb=box(payload_local,np.array(transforms.GetLocalToWorldTransform(payload)))
        for (p,_),ob in zip(others,boxes):
            if str(p.GetPath()).startswith(('/World/Rack/','/World/OutboundCarrier/')) and overlap(pb,ob):
                payload_hits.setdefault((name,str(p.GetPath())),float(sec))
    motion=StorageTransfer(loader());max_tilt=0.;max_slip=0.
    for a,b in zip(motion.frames,motion.frames[1:]):
        if a.owner!='gripper' or b.owner!='gripper':continue
        motion.elapsed=(a.time+b.time)/2;f=motion.sample();p,r=fk(f.q,(0,0,0))
        max_tilt=max(max_tilt,float(np.linalg.norm(r[:,2]-[0,0,1])))
        max_slip=max(max_slip,float(np.linalg.norm(f.payload-(p+r@[.43,0,-.65]))))
    result={'samples':len(times),'interval':.2,'broad_phase_pairs':broad,'robot_environment_hits':[dict(phase=k[0],robot=k[1],obstacle=k[2],time=v) for k,v in hits.items()],
        'payload_hits':[dict(phase=k[0],obstacle=k[1],time=v) for k,v in payload_hits.items()], 'below_floor':list(below),'max_midpoint_vertical_axis_error':max_tilt,'max_midpoint_grip_slip_m':max_slip,
        'limits':'Sampled external geometry only. No robot self-collision, engine/jig contact or full continuous swept-volume/physics verification.'}
    (ROOT/'outputs'/('u_outbound_geometry.json' if outbound else 'u_storage_geometry.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(f'{len(times)} samples; robot hits={len(hits)}, payload hits={len(payload_hits)}, floor={len(below)}; tilt={max_tilt:.6f}, slip={max_slip:.6f}m')
    for h in result['robot_environment_hits'][:8]+result['payload_hits'][:4]:print(h)
    assert not hits and not payload_hits and not below
    assert max_tilt<.002 and max_slip<.002

if __name__=='__main__':check('--outbound' in sys.argv)
