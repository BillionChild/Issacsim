"""Exercise the same RGB -> contact -> cleanup path as the editor button."""
from isaacsim import SimulationApp
app=SimulationApp({'headless':True})
import asyncio
import omni.usd
from pickup_capture_editor import show
from pickup_correction import joint_attributes
from pxr import UsdGeom

def geometry_state(stage):
    paths=['/World/TestLoad','/World/TestLoad/Engine']
    return ([a.Get() for a in joint_attributes(stage)],
        [str(UsdGeom.Xformable(stage.GetPrimAtPath(p)).ComputeLocalToWorldTransform(0)) for p in paths])

async def test():
    lab=show();await lab.load_async()
    stage=lab.stage
    lab.select('combined_occluded')
    before=geometry_state(stage)
    assert await lab.grasp_async(playback_scale=.001) is None
    assert geometry_state(stage)==before
    reports=[]
    for case,close in [('normal',True),('normal',False),('x_y_yaw',True)]:
        lab.select(case)
        before=geometry_state(stage)
        joints=[a.Get() for a in joint_attributes(stage)]
        report=await lab.grasp_async(close=close,playback_scale=.001)
        assert report is not None,lab.process.text
        print('EDITOR CONTACT RESULT',case,report,flush=True)
        assert report['success']==close,report
        assert geometry_state(stage)==before,'Payload or robot transforms changed after cleanup'
        assert [a.Get() for a in joint_attributes(stage)]==joints,'Observation pose not restored'
        assert not stage.GetPrimAtPath('/World/ContactPhysics'),'Physics overlay leaked'
        reports.append(report)
    lab.close()
    print('GRASP EDITOR PASS',flush=True)

task=asyncio.ensure_future(test())
try:
    while not task.done():app.update()
    task.result()
except BaseException:
    import traceback
    traceback.print_exc()
    print('GRASP EDITOR FAILED',flush=True)
finally:app.close()
