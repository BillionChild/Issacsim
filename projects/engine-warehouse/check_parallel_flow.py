"""Sample newly concurrent robot / pallet / carrier bounds; no physics proof."""
import itertools,json
from test_editor_runtime import Usd,Path
from pxr import UsdGeom
from fanuc_kinematics import np
from multi_runtime import MultiRuntime
from storage_geometry import box,overlap

def check():
    root=Path(__file__).resolve().parents[2]
    stage=Usd.Stage.Open(str(root/'external_assets/engines/caterham_duratec/usd/warehouse_multi_layout.usda'))
    runtime=MultiRuntime(stage);model=runtime.model
    bounds=UsdGeom.BBoxCache(Usd.TimeCode.Default(),['default','render'])
    def item(path):
        prim=stage.GetPrimAtPath(path)
        r=bounds.ComputeUntransformedBound(prim).ComputeAlignedRange()
        return prim,np.array(list(itertools.product(*zip(r.GetMin(),r.GetMax()))))
    robot=[item(p.GetPath()) for p in stage.Traverse() if str(p.GetPath()).startswith('/World/Robot/') and
           (p.IsA(UsdGeom.Mesh) or p.IsA(UsdGeom.Cube) or p.IsA(UsdGeom.Cylinder))]
    roots={str(p):item(str(p)) for p in [*(f'/World/Engines/{e}' for e in model.engines),
            *(f'/World/InlinePallets/{e}' for e in model.engines),*(f'/World/Carriers/{c}' for c in model.carriers)]}
    samples=0;overlap_samples=0;hits={}
    while not runtime.finished and model.time<900:
        runtime.tick(.2)
        if not model.active:continue
        kind,eid,cell,transfer,cid=model.active
        targets=[]
        for other,e in model.engines.items():
            if other!=eid and e['visible'] and e['owner'] in ('pallet','carrier'):
                targets.append('/World/Engines/'+other)
            if other!=eid and e['pallet_visible']:targets.append('/World/InlinePallets/'+other)
        targets.extend('/World/Carriers/'+c for c in model.carriers if c!=cid)
        cache=UsdGeom.XformCache()
        def world(item):
            p,local=item
            return box(local,np.array(cache.GetLocalToWorldTransform(p)))
        obstacle_boxes=[world(roots[p]) for p in targets]
        lo=np.array([b[0] for b in obstacle_boxes]);hi=np.array([b[1] for b in obstacle_boxes])
        moving_geometry=list(robot)
        if model.engines[eid]['owner']=='gripper':moving_geometry.append(roots['/World/Engines/'+eid])
        for p,local in moving_geometry:
            b=world((p,local))
            for j in np.where(np.all(np.minimum(b[1],hi)-np.maximum(b[0],lo)>.0005,axis=1))[0]:
                if overlap(b,obstacle_boxes[j]):hits.setdefault((str(p.GetPath()),targets[j]),model.time)
        samples+=1
        if model.dispatches:overlap_samples+=1
    runtime.close()
    report=dict(samples=samples,robot_dispatch_overlap_samples=overlap_samples,
                hits=[dict(robot=a,obstacle=b,time=t) for (a,b),t in hits.items()],
                scope='0.2 s conservative bounds; other loads/carriers only; excludes active grasp, static environment, self-collision and continuous/physical proof')
    (root/'outputs/parallel-flow-geometry.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report),flush=True)
    assert runtime.finished and overlap_samples>0 and not hits

if __name__=='__main__':check()
