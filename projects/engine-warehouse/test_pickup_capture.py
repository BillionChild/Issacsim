from isaacsim import SimulationApp
app=SimulationApp({'headless':True})
import asyncio
from pickup_capture_editor import show
from pickup_anomalies import CASES
async def test():
    lab=show()
    await lab.load_async()
    for name in CASES:
        lab.select(name)
        await lab.capture_async()
        assert lab.stage.GetPrimAtPath('/World/TestLoad').GetAttribute('xformOp:rotateZ').Get()==CASES[name][2]
    lab.select('normal')
    a=await lab.capture_async()
    lab.select('combined_occluded')
    b=await lab.capture_async()
    import numpy as np
    from PIL import Image
    depth=np.load(b/'observation/depth_m.npy')
    assert np.isnan(depth[128:384,256:384]).all()
    assert np.asarray(Image.open(a/'observation/rgb.png')).std()>5
    lab.select('normal')
    assert tuple(lab.stage.GetPrimAtPath('/World/TestLoad').GetAttribute('xformOp:translate').Get())==(0.,-2.2,.7)
    lab.close()
    print('PICKUP CAPTURE PASS',a,b,flush=True)
task=asyncio.ensure_future(test())
try:
    while not task.done():app.update()
    task.result()
finally:app.close()
