from isaacsim import SimulationApp
app=SimulationApp({'headless':True})
import asyncio
from pickup_capture_editor import show
from pickup_anomalies import CASES
async def test():
    lab=show();await lab.load_async()
    results={}
    for name in CASES:
        lab.select(name);result=await lab.estimate_async();assert result is not None,lab.status.text
        assert result['accepted'] != CASES[name][3],(name,result)
        if result['accepted']:
            import numpy as np
            truth=np.array(CASES[name][:3])*[1000,1000,1]
            assert np.all(np.abs(np.array(result['pose'])-truth)<[8,8,1]),(name,result)
        results[name]=result
    joint=lab.stage.GetPrimAtPath('/World/Robot/Base/J1').GetAttribute('xformOp:rotateZ')
    joint.Set(joint.Get()+5)
    assert await lab.estimate_async() is None
    assert 'wrist pose differs' in lab.process.text
    lab.close()
    import json
    print('PERCEPTION EDITOR PASS',json.dumps(results),flush=True)
task=asyncio.ensure_future(test())
try:
    while not task.done():app.update()
    task.result()
finally:app.close()
