"""Editor host for the deterministic three-engine scenario."""
import csv,json,math,time
from pathlib import Path
from pxr import Usd,Sdf
from build_multi_motion import load_motion
from multi_cycle import MultiCycle
from multi_scene import MultiScene
ROOT=Path(__file__).resolve().parents[2]

class MultiRuntime:
    is_multi=True
    def __init__(self,stage):
        self.stage=stage;self.layer=Sdf.Layer.CreateAnonymous('warehouse-runtime-multi')
        self.session_id=stage.GetSessionLayer().identifier
        stage.GetSessionLayer().subLayerPaths.insert(0,self.layer.identifier)
        try:
            self.model=MultiCycle({(kind,cell):load_motion(kind,cell) for kind in ('inbound','outbound') for cell in ('A','B')},empty_pallet_route=True)
            with Usd.EditContext(stage,self.layer):self.adapter=MultiScene(stage)
            self.reset()
        except Exception:self.close();raise
    @property
    def finished(self):return self.model.done
    @property
    def sim_seconds(self):return self.model.time
    def status(self):
        owners=' | '.join(f"{k}: {v['owner']}" for k,v in self.model.engines.items())
        return f'{self.model.phase}\n{owners}\nCells: {self.model.cells}'
    def apply(self):
        with Usd.EditContext(self.stage,self.layer):self.adapter.apply(self.model)
    def tick(self,dt,wall_dt=None):
        if not math.isfinite(dt) or dt<0:raise ValueError('Invalid elapsed time')
        phase=self.model.phase;start=time.perf_counter();self.model.step(dt);self.apply()
        if wall_dt is not None:
            row=self.performance.setdefault(phase,[0,0.,0.]);row[0]+=1;row[1]+=wall_dt;row[2]+=time.perf_counter()-start
    def reset(self):self.model.reset();self.performance={};self.apply()
    def export_metrics(self):
        folder=ROOT/'outputs';folder.mkdir(exist_ok=True);path=folder/'multi-engine-events.csv'
        with path.open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=['time','event','engine'],extrasaction='ignore');writer.writeheader();writer.writerows(self.model.events)
        (folder/'multi-engine-performance.json').write_text(json.dumps(self.performance,indent=2))
        return path
    def close(self):
        session=Sdf.Layer.Find(self.session_id)
        if session and self.layer.identifier in session.subLayerPaths:session.subLayerPaths.remove(self.layer.identifier)
