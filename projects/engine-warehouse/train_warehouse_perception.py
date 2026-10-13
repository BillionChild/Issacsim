"""Fixed warehouse synthetic training; labels are training/evaluation only."""
from isaacsim import SimulationApp
app=SimulationApp({'headless':True})
import asyncio,itertools,json,sys
from pathlib import Path
import omni.usd
import omni.replicator.core as rep
from pxr import Gf,UsdGeom
from fanuc_kinematics import np
from multi_runtime import MultiRuntime
from wrist_camera import CAMERA
from pickup_perception import train,Predictor,annotated

async def run():
    root=Path(__file__).resolve().parents[2];folder=root/'outputs/pickup-perception';folder.mkdir(exist_ok=True)
    await omni.usd.get_context().open_stage_async(str(root/'external_assets/engines/caterham_duratec/usd/warehouse_multi_layout.usda'))
    stage=omni.usd.get_context().get_stage();runtime=MultiRuntime(stage,vision_required=True);runtime.tick(100)
    roots=[stage.GetPrimAtPath(p) for p in ('/World/Engines/E1','/World/InlinePallets/E1')]
    product=rep.create.render_product(CAMERA,(512,512));rgb=rep.AnnotatorRegistry.get_annotator('rgb');rgb.attach([product])
    async def render(pose):
        x,y,yaw=pose
        for p in roots:
            p.GetAttribute('xformOp:translate').Set(Gf.Vec3d(x/1000,-2.2+y/1000,.7))
            p.GetAttribute('xformOp:rotateZ').Set(float(yaw))
        for _ in range(3):await rep.orchestrator.step_async(rt_subframes=4)
        return np.asarray(rgb.get_data()).copy()
    # Author in the strongest runtime layer, never in the asset file.
    from pxr import Usd
    stage.SetEditTarget(runtime.layer)
    await render((0,0,0))
    matrix=np.array(UsdGeom.Xformable(stage.GetPrimAtPath(CAMERA)).ComputeLocalToWorldTransform(0).GetInverse())
    calibration=dict(world_to_camera=matrix,focal_pixels=np.array(512*12/20.955))
    capture=folder/'warehouse-training-capture.npz'
    if '--reuse-captures' in sys.argv:
        with np.load(capture) as data:
            labels=data['labels'];images=data['images'];tests=data['tests'];test_images=data['test_images']
            np.testing.assert_allclose(data['world_to_camera'],matrix,atol=1e-5)
        print('REUSING WAREHOUSE CAPTURES (only valid for unchanged assets/lighting)',flush=True)
    else:
        labels=list(itertools.product(np.linspace(-40,40,7),np.linspace(-25,25,7),np.linspace(-3,3,7)))
        images=[]
        for i,pose in enumerate(labels):
            images.append(await render(pose))
            if i%70==0:print('WAREHOUSE TRAIN',i,'/',len(labels),flush=True)
        rng=np.random.default_rng(20261013);tests=rng.uniform([-35,-20,-2.7],[35,20,2.7],(32,3))
        test_images=[await render(pose) for pose in tests]
        np.savez_compressed(capture,labels=labels,images=images,tests=tests,test_images=test_images,world_to_camera=matrix)
    candidate=folder/'warehouse-model-candidate.npz';train(images,labels,candidate,calibration,kernel_sigma=.04)
    predictor=Predictor(candidate)
    # The cached 32 poses were used for model selection. Report a separate
    # final check after fixing the kernel choice; these images are not fitted.
    final_tests=np.random.default_rng(20261014).uniform([-35,-20,-2.7],[35,20,2.7],(32,3))
    tests=final_tests;test_images=[await render(pose) for pose in tests]
    errors=[];accepted=0
    for pose,image in zip(tests,test_images):
        result=predictor.predict(image)
        errors.append(np.abs(np.asarray(result['pose'])-pose));accepted+=result['accepted']
    from warehouse_cases import sensor_image
    image=await render((30,15,2));result=predictor.predict(image)
    rejected=predictor.predict(sensor_image(image,True))
    report=dict(train_samples=len(labels),selection_samples=32,heldout_samples=32,heldout_seed=20261014,kernel_sigma=.04,
                mae_mm_mm_deg=np.mean(errors,axis=0).tolist(),max_mm_mm_deg=np.max(errors,axis=0).tolist(),
                accepted=accepted,combined=result,occlusion=rejected,scope='Fixed scene RGB regression; independent held-out poses; no physical proof')
    (folder/'warehouse-evaluation.json').write_text(json.dumps(report,indent=2))
    annotated(image,result,calibration,folder/'warehouse-combined.png')
    assert accepted==32 and not rejected['accepted'],report
    assert np.all(np.max(errors,axis=0)<[5,5,.25]),report
    candidate.replace(folder/'warehouse-model.npz')
    print('WAREHOUSE TRAIN PASS',json.dumps(report),flush=True)
    rgb.detach([product]);product.destroy();runtime.close()

task=asyncio.ensure_future(run())
try:
    while not task.done():app.update()
    task.result()
except BaseException:
    import traceback
    traceback.print_exc();print('WAREHOUSE TRAIN FAILED',flush=True)
finally:app.close()
