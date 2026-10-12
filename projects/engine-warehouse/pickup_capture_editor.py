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
                ui.Label('1. INJECT -> 2. OBSERVE -> 3. ESTIMATE -> 4. CORRECT -> 5. VERIFY',height=35,word_wrap=True)
                self.process=ui.Label('OBSERVE ready | robot correction not connected',height=32,word_wrap=True)
                ui.Button('Open Robot Camera',clicked_fn=self.open_robot_camera)
                ui.Button('Load pickup test scene',clicked_fn=self.load)
                for name in CASES:
                    ui.Button(name,clicked_fn=lambda n=name:self.select(n))
                ui.Button('Estimate from wrist RGB',clicked_fn=self.estimate)
                ui.Button('Run vision-guided approach',clicked_fn=self.correct)
                ui.Button('Verify level pickup (clamp / lift / reseat)',clicked_fn=self.grasp)
                ui.Button('Capture RGB + depth',clicked_fn=self.capture)
                self.status=ui.Label('Load the test scene first.',word_wrap=True)
    def open_robot_camera(self):
        from wrist_camera import open_view
        if getattr(self,'robot_view',None):self.robot_view.destroy()
        self.robot_view=open_view()

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
            # Detach the generated layer before rebuilding it on repeated loads.
            await omni.usd.get_context().new_stage_async()
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
        self.process.text='INJECTED: '+name+' | press Estimate for a fresh observation'
        if getattr(self,'evidence_window',None):self.evidence_window.visible=False
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
    def estimate(self):
        if self.task and not self.task.done():return
        self.start(self.estimate_async())

    async def estimate_async(self):
        if getattr(self,'evidence_window',None):self.evidence_window.visible=False
        product=None;annotator=None
        try:
            if not self.product or omni.usd.get_context().get_stage()!=self.stage:
                raise RuntimeError('Load pickup test scene first')
            from pickup_perception import Predictor,annotated,MODEL
            from wrist_camera import CAMERA as WRIST
            from pxr import UsdGeom
            if not MODEL.exists():raise RuntimeError('Trained model missing: run train_pickup_perception.py')
            predictor=Predictor()
            matrix=np.array(UsdGeom.Xformable(self.stage.GetPrimAtPath(WRIST)).ComputeLocalToWorldTransform(0).GetInverse())
            if not np.allclose(matrix,predictor.data['world_to_camera'],atol=1e-5):
                raise RuntimeError('HOLD: wrist pose differs from training. Reload test scene.')
            self.process.text='OBSERVE: capturing wrist RGB...'
            product=rep.create.render_product(WRIST,(512,512))
            annotator=rep.AnnotatorRegistry.get_annotator('rgb');annotator.attach([product])
            for _ in range(4):await rep.orchestrator.step_async(rt_subframes=4)
            if omni.usd.get_context().get_stage()!=self.stage:raise RuntimeError('Stage changed')
            image=np.asarray(annotator.get_data()).copy()
            # Sensor fault injection precedes estimator; no case or labels enter predict().
            image,_=mask_observation(image,np.ones((512,512)),CASES[self.case][3])
            result=predictor.predict(image)
            dx,dy,yaw=result['pose']
            state=('OFFSET DETECTED' if max(abs(dx),abs(dy))>5 or abs(yaw)>.5 else 'WITHIN DEMO TOLERANCE') if result['accepted'] else result['reason']
            self.process.text=(f'{state} | X {dx:+.1f} mm, Y {dy:+.1f} mm, yaw {yaw:+.2f} deg. Correction NOT executed.' if result['accepted'] else state+' | Pose withheld. Re-observe before moving.')
            out=ROOT/'outputs/pickup-estimates';out.mkdir(exist_ok=True)
            stamp=str(time.time_ns());path=out/(stamp+'.png')
            annotated(image,result,predictor.data,path)
            (out/(stamp+'.json')).write_text(json.dumps(result,indent=2))
            if getattr(self,'evidence_window',None):self.evidence_window.destroy()
            self.evidence_window=ui.Window('Robot perception | evidence',width=540,height=610)
            with self.evidence_window.frame:
                with ui.VStack():
                    self.evidence_status=ui.Label(self.process.text,height=65,word_wrap=True)
                    ui.Image(str(path),width=512,height=512)
                    ui.Label('Learned RGB regression | fixed scene | no physical grasp validation',height=25)
            return result
        except Exception as e:
            self.process.text='HOLD: '+str(e)
            self.status.text=self.process.text
            return None
        finally:
            if annotator and product:annotator.detach([product])
            if product:product.destroy()

    def correct(self):
        if self.task and not self.task.done():return
        self.start(self.correct_async())

    def correction_status(self,text):
        self.process.text=text
        if getattr(self,'evidence_status',None):self.evidence_status.text=text

    def grasp(self):
        if self.task and not self.task.done():return
        self.start(self.grasp_async())

    async def grasp_async(self,close=True,playback_scale=1.):
        result=await self.estimate_async()
        if not result or not result['accepted']:return None
        from grasp_contact import ContactTrial
        from pickup_correction import plan,clearance
        from pxr import Sdf,Usd,UsdGeom
        import omni.physx
        import omni.kit.app
        phys=omni.physx.get_physx_interface()
        stage=self.stage;layer=None;started=False;old_target=stage.GetEditTarget()
        source=stage.GetPrimAtPath('/World/TestLoad')
        source_matrix=UsdGeom.Xformable(source).ComputeLocalToWorldTransform(0)
        try:
            self.correction_status('CHECK: full contact approach clearance...')
            await omni.kit.app.get_app().next_update_async()
            frames,_,_=plan(result,standoff=0.)
            clearance(stage,frames)
            # Physics edits and transform writes stay in a disposable session layer.
            layer=Sdf.Layer.CreateAnonymous('contact-trial.usda')
            stage.GetSessionLayer().subLayerPaths.append(layer.identifier)
            stage.SetEditTarget(Usd.EditTarget(layer))
            phys.set_simulation_layer(layer.identifier)
            trial=ContactTrial(stage,result)
            for _ in range(4):await omni.kit.app.get_app().next_update_async()
            phys.start_simulation();started=True
            wall_start=time.monotonic();phase_old=''
            for phase in trial.steps(close):
                if omni.usd.get_context().get_stage()!=stage:raise RuntimeError('Stage changed; contact test stopped')
                if UsdGeom.Xformable(source).ComputeLocalToWorldTransform(0)!=source_matrix:
                    raise RuntimeError('Pickup frame changed; contact test stopped')
                if phase!=phase_old:
                    self.correction_status('FIXTURE-ASSISTED PICKUP: '+phase+' | ideal pin/clamp lock')
                    phase_old=phase
                phys.update_simulation(trial.dt,trial.time)
                phys.update_transformations(False,True)
                trial.time+=trial.dt
                while time.monotonic()-wall_start<trial.time*playback_scale:
                    await omni.kit.app.get_app().next_update_async()
                if round(trial.time/trial.dt)%12==0:await omni.kit.app.get_app().next_update_async()
            report=trial.report();report['estimated_pose']=result['pose'];report['closed_jaws']=close
            out=ROOT/'outputs/pickup-grasps';out.mkdir(exist_ok=True)
            (out/(str(time.time_ns())+'.json')).write_text(json.dumps(report,indent=2))
            state='LEVEL PICKUP VERIFIED (IDEAL CLAMP)' if report['success'] else 'GRASP FAILED / HOLD'
            self.correction_status(f"{state} | lift {report['lift_m']*1000:.1f} mm | max rotation {report['max_rotation_change_deg']:.3f} deg | reseat error {report['reseat_error_m']*1000:.2f} mm. Test scene resets.")
            return report
        except Exception as e:
            self.correction_status('HOLD: '+str(e));return None
        finally:
            if started:phys.reset_simulation()
            phys.set_simulation_layer(stage.GetRootLayer().identifier)
            stage.SetEditTarget(old_target)
            if layer and layer.identifier in stage.GetSessionLayer().subLayerPaths:
                stage.GetSessionLayer().subLayerPaths.remove(layer.identifier)

    async def correct_async(self,playback_scale=1.):
        # Every run captures a fresh observation. No saved estimates are replayed.
        result=await self.estimate_async()
        if not result or not result['accepted']:return None
        from pickup_correction import plan,clearance,joint_attributes,write_joints,fk
        import omni.kit.app
        from pxr import UsdGeom
        try:
            self.correction_status('PLAN: solving joints from image estimate...')
            await omni.kit.app.get_app().next_update_async()
            frames,target,yaw=plan(result)
            self.correction_status('CHECK: sampled robot / environment clearance...')
            await omni.kit.app.get_app().next_update_async()
            report=clearance(self.stage,frames)
            attrs=joint_attributes(self.stage)
            # This check detects external edits; target generation uses only the estimate.
            source=self.stage.GetPrimAtPath('/World/TestLoad')
            source_matrix=UsdGeom.Xformable(source).ComputeLocalToWorldTransform(0)
            async def animate(path,label):
                start=time.monotonic()
                for elapsed,q in path:
                    if omni.usd.get_context().get_stage()!=self.stage:raise RuntimeError('Stage changed; movement stopped')
                    if UsdGeom.Xformable(source).ComputeLocalToWorldTransform(0)!=source_matrix:
                        raise RuntimeError('Object changed after observation; movement stopped')
                    while time.monotonic()-start<elapsed*playback_scale:
                        await omni.kit.app.get_app().next_update_async()
                    if omni.usd.get_context().get_stage()!=self.stage or UsdGeom.Xformable(source).ComputeLocalToWorldTransform(0)!=source_matrix:
                        raise RuntimeError('Scene changed while waiting; movement stopped')
                    write_joints(attrs,q)
                    self.correction_status(label+f' | {elapsed:.1f}/{path[-1][0]:.1f}s')
            await animate(frames,'CORRECT: moving to estimated pregrasp')
            measured=np.radians([a.Get()*sign for a,sign in zip(attrs,(1,1,-1,-1,-1,-1))])
            position,rotation=fk(measured,(0,0,0))
            residual_mm=float(np.linalg.norm(position-target)*1000)
            actual_yaw=float(np.degrees(np.arctan2(rotation[1,0],rotation[0,0])))
            residual_deg=abs((actual_yaw-yaw+180)%360-180)
            if residual_mm>.2 or residual_deg>.02:raise RuntimeError('Approach tracking verification failed')
            self.correction_status(f'VERIFY: planned target reached ({residual_mm:.3f} mm tracking error). No contact / grasp.')
            until=time.monotonic()+2*playback_scale
            while time.monotonic()<until:await omni.kit.app.get_app().next_update_async()
            duration=frames[-1][0]
            await animate([(duration-t,q) for t,q in reversed(frames)],'RETURN: observation pose')
            report.update(estimated_pose=result['pose'],tracking_error_mm=residual_mm,tracking_error_deg=residual_deg,
                target=target.tolist(),status='PREGRASP_VERIFIED',verification='FK vs estimated target, not true engine pose or physical grasp')
            out=ROOT/'outputs/pickup-corrections';out.mkdir(exist_ok=True)
            (out/(str(time.time_ns())+'.json')).write_text(json.dumps(report,indent=2))
            self.correction_status(f'PREGRASP VERIFIED | {residual_mm:.3f} mm tracking error | returned to observation. Grasp not executed.')
            return report
        except Exception as e:
            self.correction_status('HOLD: '+str(e))
            return None

    def close(self):
        if self.task and not self.task.done():self.task.cancel()
        self.release();self.window.destroy()
        if getattr(self,'evidence_window',None):self.evidence_window.destroy();self.evidence_window=None
        if getattr(self,'robot_view',None):self.robot_view.destroy();self.robot_view=None

def show():
    global lab
    if 'lab' in globals():lab.close()
    lab=PickupLab()
    return lab
