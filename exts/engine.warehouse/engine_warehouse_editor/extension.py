"""Thin Kit host. Reloadable project logic lives outside the extension package."""
import asyncio,sys,types,subprocess
from pathlib import Path
import omni.ext
import omni.ui as ui
import omni.usd
import omni.timeline
import omni.kit.app
import omni.kit.window.file
from omni.kit.viewport.utility import get_active_viewport

ROOT=Path(__file__).resolve().parents[3]
PROJECT=ROOT/'projects/engine-warehouse'
SCENE=ROOT/'external_assets/engines/caterham_duratec/usd/warehouse_u_layout_preview.usda'
MODULES=('fanuc_kinematics','u_loop_cycle','u_storage','u_storage_scene','build_u_storage_demo','editor_runtime')
_instance=None
def get_instance():return _instance


class WarehouseExtension(omni.ext.IExt):
    def on_startup(self,ext_id):
        global _instance
        _instance=self
        self.runtime=None;self.busy=False;self.task=None;self.process=None
        self.context=omni.usd.get_context();self.timeline=omni.timeline.get_timeline_interface()
        self.window=ui.Window('Engine Warehouse',width=450,height=430)
        with self.window.frame:
            with ui.VStack(spacing=7):
                self.info=ui.Label('Load Project to begin. Existing editor stays open.',word_wrap=True)
                ui.Button('Load Project',clicked_fn=self.load)
                with ui.HStack():
                    ui.Button('Play',clicked_fn=self.play)
                    ui.Button('Pause',clicked_fn=self.timeline.pause)
                    ui.Button('Stop / Reset',clicked_fn=self.reset)
                self.speed=1.
                with ui.HStack():
                    for speed in (1.,2.,4.):
                        ui.Button(f'{speed:g}x',clicked_fn=lambda v=speed:self.set_speed(v))
                ui.Button('Export timing / performance CSV',clicked_fn=self.export_metrics)
                self.repair_button=ui.Button('Repair complete -> Reinspect',clicked_fn=self.repair)
                ui.Button('Reload Code + Reset',clicked_fn=self.reload_code)
                ui.Button('Rebuild + Check Motion',clicked_fn=self.rebuild)
                with ui.HStack():
                    ui.Button('Top',clicked_fn=lambda:self.camera('PreviewCamera'))
                    ui.Button('Perspective',clicked_fn=lambda:self.camera('PerspectiveCamera'))
                self.status=ui.Label('Not loaded',word_wrap=True)
                ui.Label('Native editor Play/Pause/Stop also control this demo.',word_wrap=True)
                ui.Label('Simulated vision and kinematic grasp. Stop resets the full demo.',word_wrap=True)
        self.update_sub=omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(self.update,name='engine.warehouse.update')
        self.timeline_sub=self.timeline.get_timeline_event_stream().create_subscription_to_pop(self.timeline_event,name='engine.warehouse.timeline')

    def detach(self):
        if self.runtime:
            old=self.runtime;self.runtime=None;old.close()

    def load(self):
        if self.busy:return
        # Preserve Kit's normal unsaved-scene prompt before replacing a user's stage.
        omni.kit.window.file.prompt_if_unsaved_stage(lambda:self.schedule_load())

    def schedule_load(self):
        if self.busy:return
        self.busy=True
        self.task=asyncio.ensure_future(self.load_async())

    async def load_async(self):
        self.busy=True;self.timeline.stop();self.detach()
        try:
            result=await self.context.open_stage_async(str(SCENE))
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
            for name in MODULES:
                file=PROJECT/(name+'.py');module=types.ModuleType(name);module.__file__=str(file)
                sys.modules[name]=module
                exec(compile(file.read_bytes(),str(file),'exec'),module.__dict__)
            self.runtime=sys.modules['editor_runtime'].EditorRuntime(self.context.get_stage())
            self.timeline.set_end_time(86400.)
            self.info.text='Ready. Play starts infeed; Stop resets. Reload keeps this editor open.'
        except Exception as e:
            self.info.text='Reload stopped: '+str(e)+' (rebuild motion if source changed)'
            print('WAREHOUSE RELOAD ERROR',repr(e),flush=True)

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

    def repair(self):
        if self.runtime and self.timeline.is_playing() and not self.busy:self.runtime.repair()

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
        if not self.runtime or self.busy:
            self.repair_button.enabled=False;return
        try:
            if self.timeline.is_playing():
                dt=max(0.,float(event.payload.get('dt',0.)))
                self.runtime.tick(dt*self.speed,wall_dt=dt)
            c=self.runtime.cycle;r=self.runtime.storage
            status=f'{self.speed:g}x | Model {self.runtime.sim_seconds:.1f}s | {c.state} | Vision {c.result}\nRobot {r.state}: {r.sample().phase}\nCell occupied: {r.cell_occupied}'
            if self.status.text!=status:self.status.text=status
            self.repair_button.enabled=c.state=='WAIT_REWORK' and self.timeline.is_playing()
            if r.state=='DONE' and self.timeline.is_playing():
                self.timeline.pause();self.export_metrics()
        except Exception as e:
            self.timeline.pause();self.info.text='Paused after error: '+str(e)

    def rebuild(self):
        if not self.busy:
            self.busy=True
            self.task=asyncio.ensure_future(self.rebuild_async())

    async def rebuild_async(self):
        self.busy=True;self.timeline.stop();self.detach()
        try:
            (ROOT/'logs').mkdir(exist_ok=True)
            with (ROOT/'logs/editor-motion-build.log').open('w',encoding='utf-8') as log:
                for script in ('build_u_storage_demo.py','check_u_storage.py'):
                    self.info.text='Working: '+script+' (editor remains open)'
                    self.process=subprocess.Popen(['C:/isaacsim/kit/python/python.exe',str(PROJECT/script)],cwd=str(ROOT),stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
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
        if self.window:self.window.destroy();self.window=None
        _instance=None
