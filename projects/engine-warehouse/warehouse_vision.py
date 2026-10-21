"""Fresh wrist observation in the actual warehouse; inference receives pixels only."""
import time,json
from pathlib import Path


async def observe(stage,current,occluded=False,engine_pose=False):
    import omni.usd
    import omni.replicator.core as rep
    from pxr import UsdGeom
    from fanuc_kinematics import np
    from wrist_camera import CAMERA
    from pickup_perception import Predictor,annotated
    if engine_pose:
        from engine_depth import DepthPredictor,annotated_engine
        predictor=DepthPredictor()
        expected=np.linalg.inv(predictor.data['camera_to_world'])
    else:
        model=Path(__file__).resolve().parents[2]/'outputs/pickup-perception/warehouse-model.npz'
        if not model.exists():raise RuntimeError('Warehouse model missing: run train_warehouse_perception.py')
        predictor=Predictor(model);expected=predictor.data['world_to_camera']
    def guard():
        if not current() or omni.usd.get_context().get_stage()!=stage:raise RuntimeError('Observation cancelled: stage or runtime changed')
        matrix=np.array(UsdGeom.Xformable(stage.GetPrimAtPath(CAMERA)).ComputeLocalToWorldTransform(0).GetInverse())
        if not np.allclose(matrix,expected,atol=1e-5):raise RuntimeError('Wrist calibration differs from reference')
    guard();product=None;annotator=None;depth=None
    try:
        product=rep.create.render_product(CAMERA,(512,512))
        annotator=rep.AnnotatorRegistry.get_annotator('rgb');annotator.attach([product])
        if engine_pose:
            depth=rep.AnnotatorRegistry.get_annotator('distance_to_image_plane');depth.attach([product])
        for _ in range(4):
            await rep.orchestrator.step_async(rt_subframes=4,pause_timeline=False)
            guard()
        rgb=np.asarray(annotator.get_data()).copy()
        from warehouse_cases import sensor_image
        rgb=sensor_image(rgb,occluded)
        result=predictor.predict(rgb,np.asarray(depth.get_data()).copy()) if engine_pose else predictor.predict(rgb)
        folder=Path(__file__).resolve().parents[2]/'outputs/warehouse-vision';folder.mkdir(exist_ok=True)
        path=folder/(str(time.time_ns())+'.png')
        if engine_pose:annotated_engine(rgb,result,path)
        else:annotated(rgb,result,predictor.data,path)
        result['evidence']=str(path);result['scope']=('Fixed-workspace geometric RGB-D registration' if engine_pose else 'Fixed-scene learned RGB')+'; ideal kinematic clamp; first engine only'
        path.with_suffix('.json').write_text(json.dumps(result,indent=2))
        return result
    finally:
        if depth is not None and product is not None:depth.detach([product])
        if annotator is not None and product is not None:annotator.detach([product])
        if product is not None:product.destroy()
