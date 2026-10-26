"""Explanation UI, intentionally outside the robot sensor scene."""
from pathlib import Path
import omni.ui as ui
from .ui_help import STYLE,button

class CorrectionView:
    def __init__(self,resume):
        self.window=None;self.key=None;self.resume=resume
    def show(self):
        if self.window:self.window.visible=True
    def present(self,runtime,paused=False):
        from correction_story import comparison_image,command_delta
        self.close()
        self.key=(id(runtime),runtime.generation)
        result=runtime.model.vision_result or {}
        folder=Path(__file__).resolve().parents[3]/'outputs/correction-stories'
        folder.mkdir(parents=True,exist_ok=True)
        import time
        image=comparison_image(result,folder/f'observation-{time.time_ns()}.png')
        delta=command_delta(runtime.model)
        target='No accepted estimate: robot must hold.' if delta is None else (
            f'COMMANDED GRIP CHANGE | X {delta[0]:+.1f}  Y {delta[1]:+.1f}  Z {delta[2]:+.1f} mm\n'
            f'World rotation delta | X {delta[3]:+.2f}  Y {delta[4]:+.2f}  Z {delta[5]:+.2f} deg')
        self.window=ui.Window('Engine correction | observe - adapt - verify',width=1000,height=850)
        with self.window.frame:
            with ui.ScrollingFrame():
                with ui.VStack(spacing=8,style=STYLE):
                    self.title=ui.Label('',height=34,style={'font_size':24})
                    self.detail=ui.Label('',height=52,word_wrap=True)
                    ui.Image(image,width=960,height=568)
                    ui.Label(target,height=56,word_wrap=True)
                    self.pause_label=ui.Label('PAUSED FOR EXPLANATION' if paused else 'Correction playback',height=28)
                    self.continue_button=button('Continue corrected pickup',height=40,clicked_fn=self.continue_pickup,
                        help_text='Resume the robot: approach the estimated engine pose, grip, lift clear, then level in air.')
                    self.continue_button.enabled=bool(result.get('accepted') and not runtime.model.fault)
        self.update(runtime)
    def continue_pickup(self):
        self.pause_label.text='Correction playback'
        self.resume()
    def update(self,runtime):
        if not self.window:return
        if runtime is None or self.key!=(id(runtime),runtime.generation):
            self.close();return
        from correction_story import story
        state=story(runtime.model)
        self.title.text=state['title'];self.detail.text=state['detail']
        self.continue_button.enabled=bool((runtime.model.vision_result or {}).get('accepted') and not runtime.model.fault and not state['verified'])
    def close(self):
        if self.window:self.window.destroy()
        self.window=None;self.key=None
