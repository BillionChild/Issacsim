"""Editor-owned runtime: no SimulationApp, loop, windows, or subscriptions."""
import csv,math,time
from pathlib import Path
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

    def phase(self):
        return self.storage.sample().phase if self.storage.state!='WAITING' else self.cycle.state

    def tick(self,dt,wall_dt=None):
        if not math.isfinite(dt) or dt<0:raise ValueError('Invalid elapsed time')
        started=time.perf_counter();phase=self.phase()
        # Explicit kinematic model clock; bounded substeps keep phase timings
        # independent of rendered FPS. This is NOT the PhysX clock.
        self.cycle.start()
        remaining=dt
        while remaining>1e-9 and self.storage.state!='DONE':
            step=min(1/60,remaining);remaining-=step
            phase_now=self.phase()
            self.phase_seconds[phase_now]=self.phase_seconds.get(phase_now,0.)+step
            self.sim_seconds+=step
            if self.storage.state=='WAITING':
                self.cycle.step(step);self.storage.try_start(self.cycle)
            else:self.storage.step(step)
        self.apply()
        if wall_dt is not None:
            row=self.performance.setdefault(phase,[0,0.,0.,0.])
            row[0]+=1;row[1]+=wall_dt;row[2]+=time.perf_counter()-started;row[3]=max(row[3],wall_dt)

    def reset(self):
        self.sim_seconds=0.;self.phase_seconds={};self.performance={}
        self.cycle.reset();self.storage.reset();self.apply()

    def export_metrics(self):
        folder=Path(__file__).resolve().parents[2]/'outputs';folder.mkdir(exist_ok=True)
        path=folder/'editor-cycle-metrics.csv'
        with path.open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.writer(f);w.writerow(['phase','model_seconds','update_frames','wall_seconds','mean_update_fps','max_frame_ms','mean_runtime_ms'])
            for phase in dict.fromkeys([*self.phase_seconds,*self.performance]):
                n,wall,cpu,worst=self.performance.get(phase,[0,0,0,0])
                w.writerow([phase,self.phase_seconds.get(phase,0),n,wall,n/wall if wall else '',worst*1000,cpu*1000/n if n else ''])
        return path

    def repair(self):return self.cycle.complete_rework()

    def close(self):
        # Kit can invalidate the stage wrapper before the update callback detaches.
        paths=self.session.subLayerPaths
        if self.layer.identifier in paths:paths.remove(self.layer.identifier)
