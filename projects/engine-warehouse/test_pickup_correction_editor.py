from isaacsim import SimulationApp
app=SimulationApp({'headless':True})
import asyncio
import numpy as np
from pickup_capture_editor import show
from pickup_correction import joint_attributes
async def test():
    lab=show();await lab.load_async()
    attrs=joint_attributes(lab.stage);start=[a.Get() for a in attrs]
    lab.select('combined_occluded')
    assert await lab.correct_async(.01) is None
    assert [a.Get() for a in attrs]==start
    lab.select('x_y_yaw')
    report=await lab.correct_async(.01)
    assert report is not None,lab.process.text
    assert report['status']=='PREGRASP_VERIFIED'
    assert report['tracking_error_mm']<.2
    assert np.allclose([a.Get() for a in attrs],start,atol=1e-4)
    result=await lab.estimate_async()
    assert result and result['accepted'],lab.process.text
    print('CORRECTION EDITOR PASS',report,flush=True)
    lab.close()
task=asyncio.ensure_future(test())
try:
    while not task.done():app.update()
    task.result()
finally:app.close()
