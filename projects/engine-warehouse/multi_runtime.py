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
    def __init__(self,stage,vision_required=False):
        self.stage=stage;self.layer=Sdf.Layer.CreateAnonymous('warehouse-runtime-multi')
        self.session_id=stage.GetSessionLayer().identifier
        stage.GetSessionLayer().subLayerPaths.insert(0,self.layer.identifier)
        try:
            self.model=MultiCycle({(kind,cell):load_motion(kind,cell) for kind in ('inbound','outbound') for cell in ('A','B')},empty_pallet_route=True,level_pickup=True,vision_required=vision_required)
            with Usd.EditContext(stage,self.layer):
                self.adapter=MultiScene(stage)
                if vision_required:
                    from wrist_camera import attach
                    attach(stage)
            self.reset()
        except Exception:self.close();raise
    @property
    def finished(self):return self.model.done
    @property
    def sim_seconds(self):return self.model.time
    def status(self):
        owners=' | '.join(f"{k}: {v['owner']} ({v['clamp_status']})" for k,v in self.model.engines.items())
        return f'Case: {self.model.pickup_case} | {self.model.phase} | Robot: {self.model.robot_frame.phase} | Vision: {self.model.vision_state}\n{self.model.fault or self.vision_message}\n{owners}\nDispatching: {list(self.model.dispatches)} | Cells: {self.model.cells}'
    def apply(self):
        with Usd.EditContext(self.stage,self.layer):self.adapter.apply(self.model)
    def tick(self,dt,wall_dt=None):
        if not math.isfinite(dt) or dt<0:raise ValueError('Invalid elapsed time')
        phase=self.model.phase;start=time.perf_counter();self.model.step(dt);self.apply()
        if wall_dt is not None:
            row=self.performance.setdefault(phase,[0,0.,0.]);row[0]+=1;row[1]+=wall_dt;row[2]+=time.perf_counter()-start
    def reset(self):
        self.generation=getattr(self,'generation',0)+1
        self.model.reset();self.performance={};self.vision_message='First-engine wrist RGB gate' if self.model.vision_required else 'Replay mode';self.apply()
    async def observe_pickup(self):
        from warehouse_vision import observe
        from guided_inbound import build_guided
        generation=self.generation
        try:
            from warehouse_cases import ENGINE_CASES
            # Viewport navigation can alter the sensor camera. Restore its known
            # local pose/lens before capture; the world-calibration guard still applies.
            from wrist_camera import attach
            with Usd.EditContext(self.stage,self.layer):attach(self.stage,restore=True)
            engine_pose=self.model.pickup_case in ENGINE_CASES
            result=await observe(self.stage,lambda:self.generation==generation,self.model.sensor_occluded,engine_pose)
            if self.generation!=generation:return
            self.model.vision_result=result
            self.model.observations.append(result)
            if not result['accepted']:raise ValueError(result['reason'])
            self.vision_message='ESTIMATE: X %.1f mm, Y %.1f mm, yaw %.2f deg'%tuple(result['pose'])
            self.model._event('VISION_ESTIMATED','E1')
            if engine_pose:
                from engine_guided import build_engine_guided
                self.vision_message='ENGINE XYZ mm / RPY deg: '+', '.join(f'{v:+.2f}' for v in result['pose6'])
                self.model.guided_frames=build_engine_guided(result,self.model.motions['inbound','A'])
            else:self.model.guided_frames=build_guided(result,self.model.motions['inbound','A'])
            self.model.vision_state='ACCEPTED';self.model.phase='E1_CORRECTED_APPROACH'
            self.model._event('VISION_CORRECTION_READY','E1')
        except Exception as exc:
            if self.generation!=generation:return
            self.model.fault='HOLD: '+str(exc);self.model.phase='HOLD';self.model.vision_state='HOLD'
            self.model._event('VISION_HOLD','E1')
    def export_metrics(self):
        folder=ROOT/'outputs';folder.mkdir(exist_ok=True);path=folder/'multi-engine-events.csv'
        with path.open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=['time','event','engine'],extrasaction='ignore');writer.writeheader();writer.writerows(self.model.events)
        (folder/'multi-engine-performance.json').write_text(json.dumps(self.performance,indent=2))
        (folder/'multi-engine-vision.json').write_text(json.dumps(dict(case=self.model.pickup_case,state=self.model.vision_state,result=self.model.vision_result,observations=self.model.observations,fault=self.model.fault),indent=2))
        (folder/'multi-engine-pickup-checks.json').write_text(json.dumps(self.model.pickup_checks,indent=2))
        return path
    def close(self):
        self.generation=getattr(self,'generation',0)+1
        session=Sdf.Layer.Find(self.session_id)
        if session and self.layer.identifier in session.subLayerPaths:session.subLayerPaths.remove(self.layer.identifier)
