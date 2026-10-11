from isaacsim import SimulationApp
app=SimulationApp({'headless':True})
import asyncio
import omni.replicator.core as rep
from pickup_capture_editor import show
from pickup_anomalies import ROOT
from wrist_camera import CAMERA
from pxr import UsdGeom
async def test():
    lab=show();await lab.load_async();lab.open_robot_camera()
    assert str(lab.robot_view.viewport_api.camera_path)==CAMERA
    product=rep.create.render_product(CAMERA,(512,512))
    rgb=rep.AnnotatorRegistry.get_annotator('rgb');rgb.attach([product])
    from PIL import Image
    import numpy as np
    out=ROOT/'outputs/wrist-camera';out.mkdir(exist_ok=True)
    for name in ('normal','x_y_yaw'):
        lab.select(name)
        for _ in range(4):await rep.orchestrator.step_async(rt_subframes=4)
        data=np.asarray(rgb.get_data());assert data.shape[:2]==(512,512)
        Image.fromarray(data[:,:,:3]).save(out/(name+'.png'))
    camera=UsdGeom.Xformable(lab.stage.GetPrimAtPath(CAMERA))
    before=camera.ComputeLocalToWorldTransform(0)
    joint=lab.stage.GetPrimAtPath('/World/Robot/Base/J1').GetAttribute('xformOp:rotateZ')
    old=joint.Get();joint.Set(old+5)
    assert before!=camera.ComputeLocalToWorldTransform(0)
    joint.Set(old)
    rgb.detach([product]);product.destroy();lab.close()
    print('WRIST CAMERA PASS',out,flush=True)
task=asyncio.ensure_future(test())
try:
    while not task.done():app.update()
    task.result()
finally:app.close()
