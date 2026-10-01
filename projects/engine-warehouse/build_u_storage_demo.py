"""Prepare/cache and validate a U-cell transfer without starting Isaac Sim."""
import os,sys,json,hashlib
from pathlib import Path
from u_storage import build_transfer, Frame, PICK
from fanuc_kinematics import np,fk

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def fingerprint():
    return hashlib.sha256(b''.join((HERE/p).read_bytes() for p in ('u_storage.py','fanuc_kinematics.py'))).hexdigest()

def load_transfer():
    with np.load(ROOT/'outputs/u_storage_motion.npz',allow_pickle=False) as data:
        if str(data['fingerprint'])!=fingerprint():raise RuntimeError('Motion source changed; rerun build_u_storage_demo.py')
        return [Frame(float(t),str(phase),q.copy(),float(gap),p.copy(),float(yaw),str(owner)) for t,phase,q,gap,p,yaw,owner in zip(data['time'],data['phase'],data['q'],data['opening'],data['payload'],data['yaw'],data['owner'])]

def build():
    lib=next(Path('C:/isaacsim/extscache').glob('omni.usd.libs-*'));sys.path.insert(0,str(lib));dll=os.add_dll_directory(str(lib/'bin'))
    from pxr import Usd,UsdGeom
    from u_storage_scene import StorageScene,FOLDER
    frames=build_transfer()
    (ROOT/'outputs').mkdir(exist_ok=True)
    np.savez_compressed(ROOT/'outputs/u_storage_motion.npz',fingerprint=fingerprint(),
        **{key:np.array([getattr(f,key) for f in frames]) for key in ('time','phase','q','opening','payload','yaw','owner')})
    stage=Usd.Stage.CreateNew(str(FOLDER/'u_storage_motion_preview.usdc'))
    world=UsdGeom.Xform.Define(stage,'/World').GetPrim();world.GetReferences().AddReference(str(FOLDER/'warehouse_u_layout_preview.usda'));stage.SetDefaultPrim(world)
    UsdGeom.SetStageMetersPerUnit(stage,1.);UsdGeom.SetStageUpAxis(stage,'Z')
    stage.SetTimeCodesPerSecond(30);stage.SetStartTimeCode(0);stage.SetEndTimeCode(frames[-1].time*30)
    adapter=StorageScene(stage);adapter.apply(frames[0],PICK)
    for f in frames:adapter.apply(f,PICK,False,f.owner=='cell',f.time*30)
    stage.GetRootLayer().Save()
    for f in frames[::max(1,len(frames)//60)]+[frames[-1]]:
        m=UsdGeom.XformCache(f.time*30).GetLocalToWorldTransform(stage.GetPrimAtPath(adapter.tool_path))
        p,r=fk(f.q,(0,0,0))
        assert np.max(np.abs(np.array(m.ExtractTranslation())-p))<2e-5
        assert np.max(np.abs(np.array(m)[:3,:3].T-r))<2e-5
    print(f'U STORAGE BUILT: {len(frames)} frames, {frames[-1].time:.1f}s; FK/USD agreement PASS',flush=True)
    return frames

if __name__=='__main__':build()
