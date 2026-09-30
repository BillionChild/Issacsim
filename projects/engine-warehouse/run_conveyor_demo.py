"""Isaac Sim kinematic conveyor demo. Use the Conveyor Demo window controls."""
import argparse
from pathlib import Path
import time
from conveyor_cycle import ConveyorCycle
from isaacsim import SimulationApp

parser=argparse.ArgumentParser();parser.add_argument('--test',action='store_true')
args,_=parser.parse_known_args()
app=SimulationApp({'headless':args.test,'hide_ui':args.test})
import omni.usd
import omni.ui as ui
from omni.kit.viewport.utility import get_active_viewport
from pxr import UsdGeom,Gf

root=Path(__file__).resolve().parents[2]
scene=root/'external_assets/engines/caterham_duratec/usd/inlet_conveyor_preview.usda'
context=omni.usd.get_context()
if not context.open_stage(str(scene)):raise RuntimeError(f'Cannot open {scene}')
stage=context.get_stage()
# Keep all animation changes in the session layer; preserve the saved static scene.
stage.SetEditTarget(stage.GetSessionLayer())
load=UsdGeom.Xformable(stage.GetPrimAtPath('/World/InspectionLoad'))
load_translate=next(op for op in load.GetOrderedXformOps() if op.GetOpType()==UsdGeom.XformOp.TypeTranslate)
strips=[]
for i in range(3):
    obj=UsdGeom.Xformable(stage.GetPrimAtPath(f'/World/Conveyor/Transfer/LoweredStrip_{i}'))
    op=next(op for op in obj.GetOrderedXformOps() if op.GetOpType()==UsdGeom.XformOp.TypeTranslate)
    strips.append((op,op.Get()))
get_active_viewport().camera_path='/World/PreviewCamera'
cycle=ConveyorCycle();paused=False;last_state=None

def start():
    global paused
    paused=False;cycle.start()

def pause():
    global paused
    paused=not paused

def reset():
    global paused
    paused=False;cycle.reset()

window=ui.Window('Conveyor Demo - SIMULATED VISION',width=390,height=245)
with window.frame:
    with ui.VStack(spacing=6):
        ui.Label('Kinematic demo | First check NG, recheck OK')
        status=ui.Label('IDLE')
        result=ui.Label('Vision: PENDING')
        ui.Button('Start infeed',clicked_fn=start)
        ui.Button('Pause / Resume',clicked_fn=pause)
        rework=ui.Button('Rework complete -> return',clicked_fn=cycle.complete_rework)
        ui.Button('Reset to inlet',clicked_fn=reset)
        ui.Label('Use these buttons. No physical transport or real vision.')

if args.test:cycle.start()
previous=time.perf_counter();frames=0
try:
    while app.is_running():
        now=time.perf_counter();dt=.1 if args.test else min(now-previous,.1);previous=now
        if args.test and cycle.state=='WAIT_REWORK':cycle.complete_rework()
        if not paused:cycle.step(dt)
        load_translate.Set(Gf.Vec3d(*cycle.position))
        lift=max(0.,min(1.,(cycle.position[2]-.7)/.015))
        for op,base in strips:op.Set(Gf.Vec3d(base[0],base[1],base[2]+.0525*lift))
        status.text=f'{cycle.state}' + (' (PAUSED)' if paused else '')
        result.text=f'Vision: {cycle.result} | Pickup allowed: {cycle.pickup_allowed}'
        rework.enabled=cycle.state=='WAIT_REWORK' and not paused
        if cycle.state!=last_state:
            print('CONVEYOR',cycle.state,cycle.position,cycle.result,flush=True);last_state=cycle.state
        app.update();frames+=1
        if args.test:
            if cycle.state=='DONE':
                actual=load_translate.Get()
                assert all(abs(actual[i]-v)<1e-6 for i,v in enumerate((.75,0,.7)))
                assert cycle.pickup_allowed
                print('CONVEYOR INTEGRATION PASS',flush=True)
                break
            if frames>500:raise RuntimeError('Demo did not complete')
finally:
    app.close()
