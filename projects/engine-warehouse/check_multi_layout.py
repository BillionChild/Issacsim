"""Expanded conveyor/carrier clearance during the actual multi-engine replay."""
import itertools,json
import os,sys
from pathlib import Path
lib=next(Path('C:/isaacsim/extscache').glob('omni.usd.libs-*'));sys.path.insert(0,str(lib));dll=os.add_dll_directory(str(lib/'bin'))
from pxr import Usd
from pxr import UsdGeom
from multi_runtime import MultiRuntime
from fanuc_kinematics import np
from storage_geometry import box,overlap,mesh_cube_overlap
ROOT=Path(__file__).resolve().parents[2]
s=Usd.Stage.Open(str(ROOT/'external_assets/engines/caterham_duratec/usd/warehouse_multi_layout.usda'));r=MultiRuntime(s)
bc=UsdGeom.BBoxCache(Usd.TimeCode.Default(),['default','render'])
def item(p):
 b=bc.ComputeUntransformedBound(p).ComputeAlignedRange()
 return p,np.array(list(itertools.product(*zip(b.GetMin(),b.GetMax()))))
robot=[];others=[]
for p in s.Traverse():
 if not(p.IsA(UsdGeom.Cube) or p.IsA(UsdGeom.Cylinder) or p.IsA(UsdGeom.Mesh)):continue
 path=str(p.GetPath())
 if path.startswith('/World/Robot/'):robot.append(item(p))
 elif path.startswith(('/World/Carriers/','/World/Conveyors/EmptyCarrierFeed/','/World/Conveyors/LoadedCarrierBuffer/','/World/Conveyors/CarrierTransfer','/World/Conveyors/EmptyInlineReturn/')):others.append(item(p))
hits=set();samples=0
while not r.finished:
 r.tick(.2);xf=UsdGeom.XformCache();ob=[box(v,np.array(xf.GetLocalToWorldTransform(p))) for p,v in others]
 lo=np.array([b[0] for b in ob]);hi=np.array([b[1] for b in ob])
 for p,v in robot:
  rb=box(v,np.array(xf.GetLocalToWorldTransform(p)))
  for j in np.where(np.all(np.minimum(rb[1],hi)-np.maximum(rb[0],lo)>.0005,axis=1))[0]:
   other=others[j][0]
   if overlap(rb,ob[j]) and (not p.IsA(UsdGeom.Mesh) or not other.IsA(UsdGeom.Cube) or mesh_cube_overlap(p,other,xf)):
    hits.add((r.model.phase,str(p.GetPath()),str(other.GetPath())))
 samples+=1
result=dict(samples=samples,interval=.2,hits=sorted(hits),empty_pallet_exits=[e['engine'] for e in r.model.events if e['event']=='EMPTY_PALLET_EXIT'],limits='Robot versus new conveyors and four moving carrier structures; supplements existing cell-path checks. Sampled only, not full swept volumes or physical grasp.')
(ROOT/'outputs/multi-expanded-clearance.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));r.close();assert not hits
