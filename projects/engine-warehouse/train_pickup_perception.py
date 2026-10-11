"""Small rendered-data experiment; labels are accessed only here for training/evaluation."""
from isaacsim import SimulationApp
app=SimulationApp({'headless':True})
import asyncio,itertools,json
import numpy as np
import omni.replicator.core as rep
from pxr import Gf,UsdGeom
from pickup_capture_editor import show
from pickup_perception import train,Predictor,MODEL,annotated
from wrist_camera import CAMERA

async def run():
    lab=show();await lab.load_async()
    product=rep.create.render_product(CAMERA,(512,512))
    rgb=rep.AnnotatorRegistry.get_annotator('rgb');rgb.attach([product])
    p=lab.stage.GetPrimAtPath('/World/TestLoad')
    async def render(pose):
        x,y,yaw=pose
        p.GetAttribute('xformOp:translate').Set(Gf.Vec3d(x/1000,-2.2+y/1000,.7))
        p.GetAttribute('xformOp:rotateZ').Set(float(yaw))
        for _ in range(2):await rep.orchestrator.step_async(rt_subframes=4)
        return np.asarray(rgb.get_data()).copy()
    camera=lab.stage.GetPrimAtPath(CAMERA)
    matrix=np.array(UsdGeom.Xformable(camera).ComputeLocalToWorldTransform(0).GetInverse())
    calibration=dict(world_to_camera=matrix,focal_pixels=np.array(512*12/20.955))
    labels=list(itertools.product((-40,-20,0,20,40),(-25,-12.5,0,12.5,25),(-3,-1.5,0,1.5,3)))
    images=[]
    for i,pose in enumerate(labels):
        images.append(await render(pose))
        if i%25==0:print('TRAIN CAPTURE',i,'/125',flush=True)
    MODEL.parent.mkdir(parents=True,exist_ok=True)
    train(images,labels,MODEL,calibration)
    predictor=Predictor();rng=np.random.default_rng(42)
    tests=rng.uniform([-35,-20,-2.7],[35,20,2.7],(24,3))
    errors=[];accepted=0
    for pose in tests:
        image=await render(pose);result=predictor.predict(image)
        errors.append(np.abs(np.array(result['pose'])-pose).tolist());accepted+=result['accepted']
    image=await render((30,15,2));result=predictor.predict(image)
    annotated(image,result,calibration,MODEL.parent/'combined-estimate.png')
    from pickup_anomalies import mask_observation
    masked,_=mask_observation(image,np.ones((512,512)),True)
    rejected=predictor.predict(masked)
    annotated(masked,rejected,calibration,MODEL.parent/'occlusion-hold.png')
    report=dict(train_samples=125,heldout_samples=24,mae_mm_mm_deg=np.mean(errors,axis=0).tolist(),
        max_mm_mm_deg=np.max(errors,axis=0).tolist(),accepted=accepted,combined=result,occlusion=rejected,
        limits='Fixed wrist pose, engine, lighting. No physical grasp or recovery validation.')
    (MODEL.parent/'evaluation.json').write_text(json.dumps(report,indent=2))
    assert accepted==24,report
    assert np.all(np.mean(errors,axis=0)<[5,5,.6]),report
    assert not rejected['accepted'],report
    print('PERCEPTION PASS',json.dumps(report),flush=True)
    rgb.detach([product]);product.destroy();lab.close()

task=asyncio.ensure_future(run())
try:
    while not task.done():app.update()
    task.result()
finally:app.close()
