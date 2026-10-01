"""Isaac Sim single-pallet inspection/rework loop; robot remains static."""
import argparse
import time
from pathlib import Path
from u_loop_cycle import ULoopCycle
from isaacsim import SimulationApp

parser=argparse.ArgumentParser()
parser.add_argument('--autoplay',action='store_true')
parser.add_argument('--test',action='store_true',help='Visible integration test; auto-completes rework after verifying the wait gate')
args,_=parser.parse_known_args()
root=Path(__file__).resolve().parents[2]
scene=root/'external_assets/engines/caterham_duratec/usd/warehouse_u_layout_preview.usda'
if not scene.is_file():raise FileNotFoundError('Run build_u_layout.py first')
app=SimulationApp({'headless':False,'hide_ui':False})
import omni.usd
import omni.ui as ui
from omni.kit.viewport.utility import get_active_viewport
from pxr import UsdGeom,Gf

context=omni.usd.get_context()
assert context.open_stage(str(scene))
stage=context.get_stage();stage.SetEditTarget(stage.GetSessionLayer())
load=UsdGeom.Xformable(stage.GetPrimAtPath('/World/InlineLoad'))
op=next(o for o in load.GetOrderedXformOps() if o.GetOpType()==UsdGeom.XformOp.TypeTranslate)
get_active_viewport().camera_path='/World/PreviewCamera'
cycle=ULoopCycle();paused=False;last_state=None;test_wait=0;test_done=False


def start():
    global paused
    paused=False;cycle.start()


def toggle_pause():
    global paused
    paused=not paused


def reset():
    global paused
    paused=False;cycle.reset()


def finish_rework():
    if not paused:cycle.complete_rework()


window=ui.Window('U Loop - SIMULATED VISION',width=420,height=290)
with window.frame:
    with ui.VStack(spacing=6):
        ui.Label('One pallet | first FAIL -> repair -> recheck OK')
        status=ui.Label('IDLE')
        result=ui.Label('Vision: PENDING')
        permission=ui.Label('Robot pickup: BLOCKED')
        ui.Button('Start infeed',clicked_fn=start)
        ui.Button('Pause / Resume',clicked_fn=toggle_pause)
        rework=ui.Button('Repair complete -> REINSPECT',clicked_fn=finish_rework)
        ui.Button('Reset to inlet',clicked_fn=reset)
        with ui.HStack():
            ui.Button('Top view',clicked_fn=lambda:setattr(get_active_viewport(),'camera_path','/World/PreviewCamera'))
            ui.Button('Perspective',clicked_fn=lambda:setattr(get_active_viewport(),'camera_path','/World/PerspectiveCamera'))
        ui.Label('Simulated inspection / position-controlled transport')
        ui.Label('Robot stays idle. No real vision or physical roller drive.')
        if args.test:test_notice=ui.Label('TEST MODE: automated repair input; normal mode waits for you')

if args.autoplay or args.test:cycle.start()
previous=time.perf_counter();frames=0
robot_before=UsdGeom.XformCache().GetLocalToWorldTransform(stage.GetPrimAtPath('/World/Robot/Base/J1/J2/J3/J4/J5/J6'))
print('U LOOP READY: single pallet, robot static, vision simulated',flush=True)
try:
    while app.is_running():
        now=time.perf_counter();dt=.05 if args.test and not test_done else min(.1,now-previous);previous=now
        if args.test and not test_done and cycle.state=='WAIT_REWORK':
            test_wait+=1
            assert not cycle.pickup_allowed and cycle.result=='FAIL'
            if test_wait==30:
                assert cycle.complete_rework()
                assert cycle.result=='PENDING' and not cycle.pickup_allowed
        if not paused:cycle.step(dt)
        op.Set(Gf.Vec3d(*cycle.position))
        status.text=cycle.state+(' (PAUSED)' if paused else '')
        result.text=f'Vision: {cycle.result} | Inspections: {cycle.inspections}'
        permission.text='Robot pickup: ALLOWED (robot stays idle)' if cycle.pickup_allowed else 'Robot pickup: BLOCKED'
        rework.enabled=cycle.state=='WAIT_REWORK' and not paused
        if cycle.state!=last_state:
            print('U LOOP',cycle.state,cycle.position,cycle.result,'pickup=',cycle.pickup_allowed,flush=True)
            last_state=cycle.state
        app.update();frames+=1
        if args.test and not test_done:
            if cycle.state=='READY_PICKUP':
                actual=UsdGeom.XformCache().GetLocalToWorldTransform(stage.GetPrimAtPath('/World/InlineLoad')).ExtractTranslation()
                assert max(abs(actual[i]-v) for i,v in enumerate(cycle.PICKUP))<1e-6
                assert cycle.inspections==2 and test_wait==30 and cycle.pickup_allowed
                assert robot_before==UsdGeom.XformCache().GetLocalToWorldTransform(stage.GetPrimAtPath('/World/Robot/Base/J1/J2/J3/J4/J5/J6'))
                print('U LOOP INTEGRATION PASS: wait gate, reinspection, pickup permission, USD position and static robot',flush=True)
                test_done=True
                test_notice.text='Test passed. Repair button now requires your input.'
                cycle.reset();paused=False
                print('TEST COMPLETE: reset to inlet; buttons now operate normally; window stays open',flush=True)
            elif frames>3000:raise RuntimeError('Integration cycle timed out')
finally:
    app.close()
