"""Conservative standby robot versus moving pallet/load boxes over the U loop."""
import sys,os,itertools,json
from pathlib import Path
lib=next(Path('C:/isaacsim/extscache').glob('omni.usd.libs-*'));sys.path.insert(0,str(lib));dll=os.add_dll_directory(str(lib/'bin'))
from fanuc_kinematics import np
from pxr import Usd,UsdGeom
from storage_geometry import box,overlap
from u_loop_cycle import ULoopCycle
ROOT=Path(__file__).resolve().parents[2]
s=Usd.Stage.Open(str(ROOT/'external_assets/engines/caterham_duratec/usd/warehouse_u_layout_preview.usda'))
bounds=UsdGeom.BBoxCache(Usd.TimeCode.Default(),['default','render']);xf=UsdGeom.XformCache()
def corners(p):
 e=bounds.ComputeUntransformedBound(p).ComputeAlignedRange()
 return np.array(list(itertools.product(*zip(e.GetMin(),e.GetMax()))))
robots=[(str(p.GetPath()),box(corners(p),np.array(xf.GetLocalToWorldTransform(p)))) for p in s.Traverse() if str(p.GetPath()).startswith('/World/Robot/') and (p.IsA(UsdGeom.Mesh) or p.IsA(UsdGeom.Cube) or p.IsA(UsdGeom.Cylinder))]
load=corners(s.GetPrimAtPath('/World/InlineLoad'));cycle=ULoopCycle();cycle.start();hits=set();samples=0
while cycle.state!='READY_PICKUP':
 if cycle.state=='WAIT_REWORK':cycle.complete_rework()
 m=np.eye(4);m[3,:3]=cycle.position;pb=box(load,m)
 for path,rb in robots:
  if overlap(pb,rb):hits.add(path)
 samples+=1;cycle.step(.05)
result=dict(samples=samples,interval_seconds=.05,standby_load_box_overlaps=sorted(hits),limits='Conservative robot/load OBBs at sampled U-loop positions; not continuous swept-volume, self-collision or physical validation.')
(ROOT/'outputs/standby-clearance.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result));assert not hits
