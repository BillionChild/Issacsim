"""Capture a nominal engine-only depth reference and independent pose checks."""
from isaacsim import SimulationApp
app=SimulationApp({'headless':True})
import asyncio,json
from pathlib import Path
import omni.usd,omni.replicator.core as rep
from pxr import Usd,UsdGeom,Gf
from multi_runtime import MultiRuntime
from engine_depth import world_points,engine_surface,register,np
from wrist_camera import CAMERA

async def run():
    root=Path(__file__).resolve().parents[2];folder=root/'outputs/engine-depth';folder.mkdir(exist_ok=True)
    await omni.usd.get_context().open_stage_async(str(root/'external_assets/engines/caterham_duratec/usd/warehouse_multi_layout.usda'))
    stage=omni.usd.get_context().get_stage();runtime=MultiRuntime(stage,vision_required=True);runtime.tick(100)
    stage.SetEditTarget(runtime.layer)
    engine=UsdGeom.Xformable(stage.GetPrimAtPath('/World/Engines/E1'))
    engine.ClearXformOpOrder();xyz=engine.AddTranslateOp();angles=engine.AddRotateXYZOp()
    xyz.Set(Gf.Vec3d(0,-2.2,.7));angles.Set(Gf.Vec3f(0))
    matrix=np.array(UsdGeom.Xformable(stage.GetPrimAtPath(CAMERA)).ComputeLocalToWorldTransform(0))
    focal=512*12/20.955
    product=rep.create.render_product(CAMERA,(512,512));depth=rep.AnnotatorRegistry.get_annotator('distance_to_image_plane');depth.attach([product])
    async def capture(pose):
        x,y,z,rx,ry,rz=pose
        xyz.Set(Gf.Vec3d(x/1000,-2.2+y/1000,.7+z/1000));angles.Set(Gf.Vec3f(rx,ry,rz))
        for _ in range(4):await rep.orchestrator.step_async(rt_subframes=4,pause_timeline=False)
        return engine_surface(world_points(np.asarray(depth.get_data()).copy(),matrix,focal))
    reference=await capture([0]*6)
    candidate=folder/'reference-candidate.npz'
    np.savez_compressed(candidate,points=reference,camera_to_world=matrix,focal_pixels=focal)
    tests=[[30,15,0,0,0,2],[0,0,20,0,0,0],[0,0,15,2,0,0],[0,0,15,0,-2,0],[20,-12,20,1.5,-1,2],[-20,10,10,-1,1.5,-2]]
    report=[]
    for truth in tests:
        observed=await capture(truth);pose,rmse=register(reference,observed)
        error=np.abs(pose-truth)
        report.append(dict(truth=truth,estimate=pose.tolist(),error=error.tolist(),rmse=rmse))
        print('DEPTH VALIDATION',truth,'estimate',pose.round(3).tolist(),'error',error.round(3).tolist(),flush=True)
    (folder/'calibration-check.json').write_text(json.dumps(report,indent=2))
    assert all(max(r['error'][:3])<3 and max(r['error'][3:])<.20 for r in report),report
    candidate.replace(folder/'reference.npz')
    print('ENGINE DEPTH CALIBRATION PASS',flush=True)
    depth.detach([product]);product.destroy();runtime.close()

task=asyncio.ensure_future(run())
try:
    while not task.done():app.update()
    task.result()
except BaseException:
    import traceback
    traceback.print_exc();print('ENGINE DEPTH CALIBRATION FAILED',flush=True)
finally:app.close()
