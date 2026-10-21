"""Readable UI styles and English hover help; no external font dependency."""
import omni.ui as ui

STYLE={
    'Label':{'font_size':18},
    'Button.Label':{'font_size':18},
    'ComboBox':{'font_size':18},
    'CollapsableFrame':{'font_size':18},
}
HELP={
    'Load three-engine demo':'Load the three-engine inbound, repair-return and outbound scenario.\nReview the save prompt before replacing the scene. Then choose a case and press Play.',
    'Apply case':'Apply the selected anomaly to the first engine.\nUse Reset > select case > Apply case. Cases cannot change during playback.',
    'Play':'Start or resume the conveyors and robot.\nThe first engine uses a camera pose estimate for corrected pickup.',
    'Pause':'Pause while keeping the current pose and progress.\nUse this to explain the camera image or correction result.',
    'Reset':'Restart the entire scenario. Keep the selected case, but clear measurements, events and recapture counts.',
    'Monitor':'Open robot recovery progress, seating verification and warehouse inventory.',
    'Robot camera':'Open the live virtual wrist-camera view.\nThe occlusion test mask appears in inference images, not this live viewport.',
    'Overview':'Switch the main viewport to a perspective overview of the process.',
    'Retry observation':'Capture and evaluate a new image at the same position during HOLD.\nThe mask is not removed; remaining occlusion will keep the robot on HOLD.',
    'Clear camera mask + retry':'Remove the simulated camera mask and capture again.\nResume only after a fresh accepted image. This is operator assistance, not robot obstacle removal.',
    'Load single-engine project':'Load the development single-engine scenario.\nUse Load three-engine demo for the continuous portfolio demonstration.',
    'Open pickup anomaly lab':'Open the development lab to test anomaly injection, image estimation and pickup correction separately.',
    'Export timing / performance CSV':'Save current events, performance and verification results under outputs.\nExport before Reset. Existing files with the same names are overwritten.',
    'Request outbound':'Request outbound in single-engine mode.\nFor the three-engine scenario, use manual dispatch in Monitor.',
    'Repair complete -> Reinspect':'Mark repair complete and start reinspection while the single-engine scenario is waiting for repair.',
    'Reload Code + Reset':'Reload motion logic and reset the scenario.\nFor UI changes, toggle the extension OFF > ON instead.',
    'Rebuild + Check Motion':'Regenerate and validate development robot paths.\nNot required for normal playback; generation may take time.',
    'Top camera':'Switch the main viewport to the top-down view.',
    'Auto demo':'Select immediately after Reset. Run the predefined inbound and outbound sequence automatically.',
    'Manual outbound':'Select immediately after Reset. Choose outbound engines manually instead of generating automatic orders.',
    'Request selected engine outbound':'Queue outbound for the selected stored engine.\nProcessing waits for the robot and loading zone. Disabled when a request is unavailable.',
}
CASE_HELP='Choose an anomaly for the first engine.\nnormal: no fault / stop_x: 30 mm X stop error\nlateral_y: 15 mm Y offset / yaw: 2 deg rotation\noccluded: camera-image mask\nx_y, x_yaw, y_yaw, x_y_yaw: combined offsets\ncombined_occluded: combined offsets plus mask\nPress Apply case after selecting.'

def tooltip(text):
    def build():
        with ui.VStack(width=460,spacing=8):
            ui.Label(text,width=460,height=0,word_wrap=True,
                     style={'font_size':18,'color':0xff202020,'margin':12})
    return build

def button(text,**kwargs):
    help_text=kwargs.pop('help_text',HELP.get(text))
    if not help_text and text in ('1x','2x','4x'):
        help_text=f'Set demonstration playback to {text}.\nModel-time cycle measurements remain unchanged.'
    if help_text:kwargs['tooltip_fn']=tooltip(help_text)
    return ui.Button(text,**kwargs)
