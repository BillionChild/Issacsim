"""Fresh wrist observation in the actual warehouse; inference receives pixels only."""
import time,json
from pathlib import Path


async def observe(stage,current,occluded=False):
    import omni.usd
    import omni.replicator.core as rep
    from pxr import UsdGeom
    from fanuc_kinematics import np
    from wrist_camera import CAMERA
    from pickup_perception import Predictor,annotated
    model=Path(__file__).resolve().parents[2]/'outputs/pickup-perception/warehouse-model.npz'
    if not model.exists():raise RuntimeError('Warehouse model missing: run train_warehouse_perception.py')
    predictor=Predictor(model)
    def guard():
        if not current() or omni.usd.get_context().get_stage()!=stage:raise RuntimeError('Observation cancelled: stage or runtime changed')
        matrix=np.array(UsdGeom.Xformable(stage.GetPrimAtPath(CAMERA)).ComputeLocalToWorldTransform(0).GetInverse())
        if not np.allclose(matrix,predictor.data['world_to_camera'],atol=1e-5):raise RuntimeError('Wrist calibration differs from training')
    guard();product=None;annotator=None
    try:
        product=rep.create.render_product(CAMERA,(512,512))
        annotator=rep.AnnotatorRegistry.get_annotator('rgb');annotator.attach([product])
        for _ in range(4):
            await rep.orchestrator.step_async(rt_subframes=4,pause_timeline=False)
            guard()
        rgb=np.asarray(annotator.get_data()).copy()
        from warehouse_cases import sensor_image
        rgb=sensor_image(rgb,occluded)
        result=predictor.predict(rgb)
        folder=Path(__file__).resolve().parents[2]/'outputs/warehouse-vision';folder.mkdir(exist_ok=True)
        path=folder/(str(time.time_ns())+'.png')
        annotated(rgb,result,predictor.data,path)
        result['evidence']=str(path);result['scope']='Fixed-scene learned RGB; ideal kinematic clamp; first engine only'
        path.with_suffix('.json').write_text(json.dumps(result,indent=2))
        return result
    finally:
        if annotator is not None and product is not None:annotator.detach([product])
        if product is not None:product.destroy()
