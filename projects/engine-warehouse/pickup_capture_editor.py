"""Run via Script Editor. RGB-D capture is separate from warehouse playback."""
import asyncio,json,time
from pathlib import Path
import numpy as np
import omni.ui as ui
import omni.usd
import omni.timeline
import omni.kit.window.file
import omni.replicator.core as rep
from omni.kit.viewport.utility import get_active_viewport
from pickup_anomalies import ROOT,OUTPUT,CAMERA,CASES,build,apply_case,mask_observation

class PickupLab:
    def __init__(self):
        self.case='normal';self.product=None;self.rgb=None;self.depth=None;self.task=None
        self.window=ui.Window('Pickup anomaly lab',width=400,height=510)
        with self.window.frame:
            with ui.VStack(spacing=5):
                ui.Label('Observation only | robot disabled',height=24)
                ui.Button('Load pickup test scene',clicked_fn=self.load)
                for name in CASES:
                    ui.Button(name,clicked_fn=lambda n=name:self.select(n))
                ui.Button('Capture RGB + depth',clicked_fn=self.capture)
                self.status=ui.Label('Load the test scene first.',word_wrap=True)
    def load(self):
        if self.task and not self.task.done():return
        omni.kit.window.file.prompt_if_unsaved_stage(lambda:self.start(self.load_async()))
    def start(self,coro):
        self.task=asyncio.ensure_future(coro)
        return self.task
    def release(self):
        if self.product:
            self.rgb.detach([self.product]);self.depth.detach([self.product])
            self.product.destroy();self.product=None
    async def load_async(self):
        try:
            omni.timeline.get_timeline_interface().stop();self.release()
            build()
            ok=await omni.usd.get_context().open_stage_async(str(OUTPUT))
            if isinstance(ok,tuple) and not ok[0]:raise RuntimeError(str(ok))
            self.stage=omni.usd.get_context().get_stage()
            self.product=rep.create.render_product(CAMERA,(512,512))
            self.rgb=rep.AnnotatorRegistry.get_annotator('rgb')
            self.depth=rep.AnnotatorRegistry.get_annotator('distance_to_image_plane')
            self.rgb.attach([self.product]);self.depth.attach([self.product])
            viewport=get_active_viewport()
            if viewport:viewport.camera_path=CAMERA
            self.case='normal';apply_case(self.stage,'normal')
            self.status.text='Ready: select a case, then Capture RGB + depth.'
        except Exception as e:self.status.text='Load failed: '+str(e);raise
    def select(self,name):
        if self.task and not self.task.done():return
        if not self.product or omni.usd.get_context().get_stage()!=self.stage:
            self.status.text='Load pickup test scene first.';return
        self.case=name;truth=apply_case(self.stage,name)
        self.status.text=f'{name}: {truth}\nMask affects captured images only.'
    def capture(self):
        if self.task and not self.task.done():return
        self.start(self.capture_async())
    async def capture_async(self):
        try:
            if not self.product or omni.usd.get_context().get_stage()!=self.stage:
                raise RuntimeError('Load pickup test scene first')
            name=self.case
            for _ in range(4):await rep.orchestrator.step_async(rt_subframes=4)
            rgb=np.asarray(self.rgb.get_data());depth=np.asarray(self.depth.get_data())
            if rgb.shape[:2]!=(512,512) or depth.shape!=(512,512):
                raise RuntimeError(f'Camera frame not ready: {rgb.shape}, {depth.shape}')
            if not np.isfinite(depth).any():raise RuntimeError('No valid depth samples')
            rgb,depth=mask_observation(rgb,depth,CASES[name][3])
            out=ROOT/'outputs/pickup-captures'/f'{time.time_ns()}-{name}'
            obs=out/'observation';obs.mkdir(parents=True)
            from PIL import Image
            Image.fromarray(rgb[:,:,:3]).save(obs/'rgb.png');np.save(obs/'depth_m.npy',depth)
            cam=self.stage.GetPrimAtPath(CAMERA)
            focal=cam.GetAttribute('focalLength').Get();ap=cam.GetAttribute('horizontalAperture').Get()
            (obs/'camera.json').write_text(json.dumps(dict(resolution=[512,512],fx=512*focal/ap,fy=512*focal/ap,cx=256,cy=256,
                position_world=[0,-2.2,3.2],usd_camera_axes='right +X, up +Y, look -Z',depth='distance_to_image_plane, metres',invalid_depth='NaN or infinity'),indent=2))
            (out/'ground_truth.json').write_text(json.dumps(dict(case=name,parameters=dict(zip(('dx_m','dy_m','yaw_deg','observation_mask'),CASES[name])),scope='evaluation only; never estimator input'),indent=2))
            self.status.text='Saved: '+str(out)
            return out
        except Exception as e:self.status.text='Capture failed: '+str(e);raise
    def close(self):
        if self.task and not self.task.done():self.task.cancel()
        self.release();self.window.destroy()

def show():
    global lab
    if 'lab' in globals():lab.close()
    lab=PickupLab()
    return lab
