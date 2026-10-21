"""Thin Kit host. Reloadable project logic lives outside the extension package."""
import asyncio,sys,types,subprocess
from pathlib import Path
from .dashboard import Dashboard
import omni.ext
import omni.ui as ui
from .ui_help import STYLE, CASE_HELP, tooltip, button
import omni.usd
import omni.timeline
import omni.kit.app
import omni.kit.window.file
from omni.kit.viewport.utility import get_active_viewport

ROOT=Path(__file__).resolve().parents[3]
PROJECT=ROOT/'projects/engine-warehouse'
MULTI_SCENE=ROOT/'external_assets/engines/caterham_duratec/usd/warehouse_multi_layout.usda'
SCENE=ROOT/'external_assets/engines/caterham_duratec/usd/warehouse_u_layout_preview.usda'
MODULES=('fanuc_kinematics','u_loop_cycle','u_storage','wrist_camera','u_storage_scene','build_u_storage_demo','u_outbound','build_u_outbound_demo','outbound_cycle','editor_runtime')
_instance=None
def get_instance():return _instance


class WarehouseExtension(omni.ext.IExt):
    def on_startup(self,ext_id):
        global _instance
        _instance=self
        self.runtime=None;self.busy=False;self.task=None;self.process=None;self.multi=False
        self.context=omni.usd.get_context();self.timeline=omni.timeline.get_timeline_interface()
        self.dashboard=Dashboard()
        if str(PROJECT) not in sys.path:sys.path.insert(0,str(PROJECT))
        from warehouse_cases import CASES
        self.case_names=list(CASES)
        self.window=ui.Window('Engine Warehouse',width=610,height=590)
        with self.window.frame:
            with ui.VStack(spacing=6,style=STYLE):
                ui.Label('ENGINE WAREHOUSE | DEMO CONTROL',height=36)
                button('Load three-engine demo',height=36,clicked_fn=self.load_multi)
                ui.Label('First-engine case | select before Play',height=36)
                with ui.HStack(height=36):
                    self.case_combo=ui.ComboBox(0,*self.case_names,tooltip_fn=tooltip(CASE_HELP))
                    button('Apply case',clicked_fn=self.apply_case)
                with ui.HStack(height=36):
                    button('Play',clicked_fn=self.play)
                    button('Pause',clicked_fn=self.timeline.pause)
                    button('Reset',clicked_fn=self.reset)
                self.speed=1.
                with ui.HStack(height=36):
                    ui.Label('Playback',width=110)
                    for speed in (1.,2.,4.):
                        button(f'{speed:g}x',clicked_fn=lambda v=speed:self.set_speed(v))
                with ui.HStack(height=36):
                    button('Monitor',clicked_fn=self.dashboard.show)
                    button('Robot camera',clicked_fn=self.open_robot_camera)
                    button('Overview',clicked_fn=lambda:self.camera('PerspectiveCamera'))
                self.info=ui.Label('Load demo, choose a case, then Play.',height=64,word_wrap=True)
                self.recovery_controls=ui.HStack(height=36,visible=False)
                with self.recovery_controls:
                    button('Retry observation',clicked_fn=lambda:self.retry_vision(False))
                    button('Clear camera mask + retry',clicked_fn=lambda:self.retry_vision(True))
                self.advanced=ui.CollapsableFrame('Advanced | development / manual controls',collapsed=True,height=0,tooltip_fn=tooltip('Expand development and individual test tools.\nNot needed for normal demonstration playback.'))
                with self.advanced:
                    with ui.ScrollingFrame(height=360):
                        with ui.VStack(spacing=5):
                            button('Load single-engine project',height=36,clicked_fn=self.load)
                            button('Open pickup anomaly lab',height=36,clicked_fn=self.open_pickup_lab)
                            button('Export timing / performance CSV',height=36,clicked_fn=self.export_metrics)
                            self.outbound_button=button('Request outbound',height=36,clicked_fn=self.request_outbound)
                            self.repair_button=button('Repair complete -> Reinspect',height=36,clicked_fn=self.repair)
                            button('Reload Code + Reset',height=36,clicked_fn=self.reload_code)
                            button('Rebuild + Check Motion',height=36,clicked_fn=self.rebuild)
                            button('Top camera',height=36,clicked_fn=lambda:self.camera('PreviewCamera'))
                            self.status=ui.Label('Not loaded',height=130,word_wrap=True)
        self.update_sub=omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(self.update,name='engine.warehouse.update')
        self.timeline_sub=self.timeline.get_timeline_event_stream().create_subscription_to_pop(self.timeline_event,name='engine.warehouse.timeline')

    def open_robot_camera(self):
        if str(PROJECT) not in sys.path:sys.path.insert(0,str(PROJECT))
        from wrist_camera import open_view
        if getattr(self,'robot_view',None):self.robot_view.destroy()
        self.robot_view=open_view()

    def open_pickup_lab(self):
        if str(PROJECT) not in sys.path:sys.path.insert(0,str(PROJECT))
        from pickup_capture_editor import show
        self.pickup_lab=show()

    def detach(self):
        if self.runtime:
            old=self.runtime;self.runtime=None;old.close()

    def load(self):
        if self.busy:return
        # Preserve Kit's normal unsaved-scene prompt before replacing a user's stage.
        omni.kit.window.file.prompt_if_unsaved_stage(lambda:self.schedule_load())

    def load_multi(self):
        if not self.busy:omni.kit.window.file.prompt_if_unsaved_stage(lambda:self.schedule_load(True))

    def schedule_load(self,multi=False):
        if self.busy:return
        self.multi=multi;self.busy=True
        self.task=asyncio.ensure_future(self.load_async())

    async def load_async(self):
        self.busy=True;self.timeline.stop();self.detach()
        try:
            result=await self.context.open_stage_async(str(MULTI_SCENE if self.multi else SCENE))
            if isinstance(result,tuple) and not result[0]:raise RuntimeError(str(result))
            self.busy=False;self.reload_code();self.camera('PreviewCamera')
        except Exception as e:self.info.text='Load failed: '+str(e)
        finally:self.busy=False

    def reload_code(self):
        if self.busy:return
        self.timeline.stop();self.detach()
        try:
            if str(PROJECT) not in sys.path:sys.path.insert(0,str(PROJECT))
            # Compile current source directly: no same-second .pyc cache surprises.
            self.multi=bool(self.context.get_stage().GetDefaultPrim().GetAttribute('demo:multiEngine').Get())
            modules=MODULES+('warehouse_cases','build_multi_motion','level_clamp','pickup_perception','pickup_correction','guided_inbound','warehouse_vision','multi_cycle','multi_scene','multi_runtime') if self.multi else MODULES
            for name in modules:
                file=PROJECT/(name+'.py');module=types.ModuleType(name);module.__file__=str(file)
                sys.modules[name]=module
                exec(compile(file.read_bytes(),str(file),'exec'),module.__dict__)
            self.runtime=sys.modules['multi_runtime'].MultiRuntime(self.context.get_stage(),vision_required=True) if self.multi else sys.modules['editor_runtime'].EditorRuntime(self.context.get_stage())
            if self.multi:self.runtime.model.configure_case(self.case_names[self.case_combo.model.get_item_value_model().as_int])
            self.timeline.set_end_time(86400.)
            self.info.text='Ready. Play starts infeed; Stop resets. Reload keeps this editor open.'
        except Exception as e:
            self.info.text='Reload stopped: '+str(e)+' (rebuild motion if source changed)'
            print('WAREHOUSE RELOAD ERROR',repr(e),flush=True)

    def apply_case(self):
        if self.busy or not self.runtime or not self.multi:return
        try:
            name=self.case_names[self.case_combo.model.get_item_value_model().as_int]
            self.runtime.model.configure_case(name)
            self.info.text='First engine case: '+name+'. Play to run.'
        except ValueError as exc:self.info.text=str(exc)

    def retry_vision(self,clear_sensor):
        if self.busy or not self.runtime or not self.multi:return
        if self.runtime.model.retry_observation(clear_sensor):
            self.info.text='Re-observing at pickup; no reset or pose correction from truth.'
            self.timeline.play()
        else:self.info.text='Retry is available only for a vision HOLD before pickup.'

    def set_speed(self,value):
        self.speed=value
        self.info.text=f'Test playback {value:g}x. Model cycle times are unchanged.'

    def export_metrics(self):
        if self.runtime:self.info.text='Saved: '+str(self.runtime.export_metrics())

    def play(self):
        if self.runtime and not self.busy:self.timeline.play()

    def reset(self):
        self.timeline.stop()
        if self.runtime:self.runtime.reset()

    def request_outbound(self):
        if self.runtime and not self.multi and not self.busy and self.runtime.request_outbound():self.timeline.play()

    def repair(self):
        if self.runtime and not self.multi and self.timeline.is_playing() and not self.busy:self.runtime.repair()

    def camera(self,name):
        viewport=get_active_viewport()
        if self.runtime and viewport:viewport.camera_path='/World/'+name

    def timeline_event(self,event):
        if event.type==int(omni.timeline.TimelineEventType.STOP) and self.runtime:
            if self.context.get_stage()==self.runtime.stage:self.runtime.reset()
            else:self.detach()

    def update(self,event):
        if self.runtime and self.context.get_stage()!=self.runtime.stage:
            self.detach();self.info.text='Stage changed. Load Project to reconnect.'
        self.dashboard.update(self.runtime)
        self.recovery_controls.visible=bool(self.runtime and self.multi and self.runtime.model.vision_state=='HOLD')
        if not self.runtime or self.busy:
            self.repair_button.enabled=False;self.outbound_button.enabled=False;return
        try:
            if self.timeline.is_playing():
                dt=max(0.,float(event.payload.get('dt',0.)))
                self.runtime.tick(dt*self.speed,wall_dt=dt)
            if self.multi:
                if self.runtime.model.vision_state=='OBSERVE' and self.timeline.is_playing():
                    self.busy=True;self.task=asyncio.ensure_future(self.observe_first_engine())
                self.status.text=f'{self.speed:g}x | Model {self.runtime.sim_seconds:.1f}s\n'+self.runtime.status()
                self.repair_button.enabled=False;self.outbound_button.enabled=False
                if self.runtime.finished and self.timeline.is_playing():self.timeline.pause();self.export_metrics()
                return
            c=self.runtime.cycle;r=self.runtime.storage
            status=f'{self.speed:g}x | Model {self.runtime.sim_seconds:.1f}s | {c.state} | Vision {c.result}\nRobot {r.state}: {self.runtime.phase()}\nCell occupied: {r.cell_occupied}'
            if self.status.text!=status:self.status.text=status
            self.repair_button.enabled=c.state=='WAIT_REWORK' and self.timeline.is_playing()
            self.outbound_button.enabled=r.state=='DONE' and r.cell_occupied and self.runtime.outbound.state=='WAITING'
            if self.runtime.finished and self.timeline.is_playing():
                self.timeline.pause();self.export_metrics()
        except Exception as e:
            self.timeline.pause();self.info.text='Paused after error: '+str(e)

    async def observe_first_engine(self):
        runtime=self.runtime
        self.busy=True;self.info.text='OBSERVE: '+runtime.model.pickup_case+' | wrist RGB; robot held at idle.'
        try:
            await runtime.observe_pickup()
            if self.runtime is not runtime:return
            self.info.text=runtime.model.fault or runtime.vision_message
            if runtime.model.fault:
                self.timeline.pause();self.export_metrics()
            result=runtime.model.vision_result
            if result and result.get('evidence'):
                if getattr(self,'vision_evidence',None):self.vision_evidence.destroy()
                self.vision_evidence=ui.Window('Warehouse vision | first engine',width=540,height=620)
                with self.vision_evidence.frame:
                    with ui.VStack():
                        ui.Label(self.info.text,height=65,word_wrap=True)
                        ui.Image(result['evidence'],width=512,height=512)
                        ui.Label('Actual warehouse RGB -> learned estimate -> corrected pickup',height=36)
        finally:self.busy=False

    def rebuild(self):
        if not self.busy:
            self.busy=True
            self.task=asyncio.ensure_future(self.rebuild_async())

    async def rebuild_async(self):
        self.busy=True;self.timeline.stop();self.detach()
        try:
            (ROOT/'logs').mkdir(exist_ok=True)
            with (ROOT/'logs/editor-motion-build.log').open('w',encoding='utf-8') as log:
                scripts=('build_u_storage_demo.py','check_u_storage.py','build_u_outbound_demo.py','check_u_storage.py --outbound')
                if self.multi:scripts+=('build_multi_motion.py','check_multi_motion.py','check_multi_layout.py')
                for script in scripts:
                    self.info.text='Working: '+script+' (editor remains open)'
                    self.process=subprocess.Popen(['C:/isaacsim/kit/python/python.exe',str(PROJECT/script.split()[0]),*script.split()[1:]],cwd=str(ROOT),stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                    while self.process.poll() is None:await asyncio.sleep(.2)
                    if self.process.returncode:raise RuntimeError('See logs/editor-motion-build.log')
                    self.process=None
            self.busy=False;self.reload_code()
        except asyncio.CancelledError:raise
        except Exception as e:self.info.text='Rebuild failed: '+str(e)
        finally:self.busy=False

    def on_shutdown(self):
        global _instance
        self.update_sub=None;self.timeline_sub=None
        if self.task and not self.task.done():self.task.cancel()
        if self.process and self.process.poll() is None:self.process.terminate()
        self.detach()
        self.dashboard.close()
        if getattr(self,'vision_evidence',None):self.vision_evidence.destroy()
        if getattr(self,'robot_view',None):self.robot_view.destroy();self.robot_view=None
        if getattr(self,'pickup_lab',None):self.pickup_lab.close()
        if self.window:self.window.destroy();self.window=None
        _instance=None
