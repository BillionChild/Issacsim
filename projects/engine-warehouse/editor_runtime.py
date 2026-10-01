"""Editor-owned runtime: no SimulationApp, loop, windows, or subscriptions."""
from pxr import Usd,Sdf
from u_loop_cycle import ULoopCycle
from u_storage import StorageTransfer
from build_u_storage_demo import load_transfer
from u_storage_scene import StorageScene


class EditorRuntime:
    def __init__(self,stage):
        for path in ('/World/Robot','/World/InlineLoad','/World/Rack'):
            if not stage.GetPrimAtPath(path):raise ValueError('Load the U-layout warehouse scene first')
        self.cycle=ULoopCycle();self.storage=StorageTransfer(load_transfer())
        self.stage=stage;self.layer=Sdf.Layer.CreateAnonymous('warehouse-runtime')
        self.session=stage.GetSessionLayer()
        self.session.subLayerPaths.insert(0,self.layer.identifier)
        try:
            with Usd.EditContext(stage,self.layer):self.adapter=StorageScene(stage)
            self.reset()
        except Exception:
            self.close();raise

    def apply(self):
        with Usd.EditContext(self.stage,self.layer):
            self.adapter.apply(self.storage.sample(),self.cycle.position,self.cycle.pickup_allowed and self.storage.state=='WAITING',self.storage.cell_occupied)

    def tick(self,dt):
        self.cycle.start();self.cycle.step(dt)
        self.storage.try_start(self.cycle);self.storage.step(dt);self.apply()

    def reset(self):
        self.cycle.reset();self.storage.reset();self.apply()

    def repair(self):return self.cycle.complete_rework()

    def close(self):
        # Kit can invalidate the stage wrapper before the update callback detaches.
        paths=self.session.subLayerPaths
        if self.layer.identifier in paths:paths.remove(self.layer.identifier)
