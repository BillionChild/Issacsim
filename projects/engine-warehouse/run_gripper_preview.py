"""Interactive kinematic jaw preview; no contact, gripping force or robot motion."""
import argparse,time
from pathlib import Path
from isaacsim import SimulationApp
parser=argparse.ArgumentParser();parser.add_argument('--test',action='store_true');parser.add_argument('--detail',action='store_true');args,_=parser.parse_known_args()
app=SimulationApp({'headless':args.test})
import omni.usd,omni.ui as ui
from omni.kit.viewport.utility import get_active_viewport
from pxr import UsdGeom,Gf
root=Path(__file__).resolve().parents[2]
context=omni.usd.get_context();scene_name='jig_detail_preview.usda' if (args.test or args.detail) else 'warehouse_cell_preview.usda'
assert context.open_stage(str(root/'external_assets/engines/caterham_duratec/usd'/scene_name))
print('GRIPPER STAGE READY',flush=True)
s=context.get_stage();s.SetEditTarget(s.GetSessionLayer())
base='/World/Gripper' if (args.test or args.detail) else '/World/FANUC_210L/Base/J1/J2/J3/J4/J5/J6/EngineJig'
jaws=[next(op for op in UsdGeom.Xformable(s.GetPrimAtPath(base+'/'+name)).GetOrderedXformOps() if op.GetOpType()==UsdGeom.XformOp.TypeTranslate) for name in ['Left','Right']]
get_active_viewport().camera_path='/World/PreviewCamera'
opening=.12;target=.12

def command(value):
 global target
 target=value

window=ui.Window('Engine Gripper',width=360,height=180)
with window.frame:
 with ui.VStack(spacing=8):
  ui.Label('Horizontal parallel jaws | kinematic preview')
  label=ui.Label('Open')
  ui.Button('Open jaws',clicked_fn=lambda:command(.12))
  ui.Button('Close jaws',clicked_fn=lambda:command(0.))
  ui.Label('No engine attachment or contact force yet')
previous=time.perf_counter();frames=0
try:
 while app.is_running():
  now=time.perf_counter();dt=.05 if args.test else min(.1,now-previous);previous=now
  if args.test:target=0 if frames<40 else .12
  distance=min(abs(target-opening),dt*.08)
  opening+=distance if target>opening else -distance
  for sign,op in zip([1,-1],jaws):op.Set(Gf.Vec3d(0,sign*opening,0))
  label.text=f'Jaw gap: {(0.43+2*opening)*1000:.0f} mm'
  app.update();frames+=1
  if args.test:
   if frames==35:assert abs(opening)<1e-8;print('CLOSE PASS',flush=True)
   if frames==75:
    assert abs(opening-.12)<1e-8;print('OPEN PASS',flush=True);break
finally:app.close()


