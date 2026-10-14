"""Read-only warehouse monitor. Times come from model events, not wall time."""
import time
import omni.ui as ui


def serial(eid):
    return 'ENG-' + eid[1:].zfill(4)


def snapshot(model):
    rows = {}
    for eid, engine in model.engines.items():
        events = {e['event']: e['time'] for e in model.events if e['engine'] == eid}
        start, stored = events.get('SCENE_ENTRY'), events.get('STORED')
        state = ('OUTBOUND_QUEUED' if eid in model.requests else
                 'OUTBOUND_MOVING' if model.active and model.active[:2]==('outbound',eid) else
                 'SHIPPED' if eid in model.shipped else
                 'CONVEYOR_DISPATCH' if eid in model.dispatches else
                 'PENDING' if not engine['visible'] else
                 engine['cycle'].state if engine['owner'] == 'pallet' else engine['owner'].upper())
        rows[eid] = dict(state=state, vision=engine['cycle'].result or '-',
                         cell=engine['cell'] or '-', start=start, stored=stored,
                         elapsed=None if start is None else (stored if stored is not None else model.time)-start)
    return rows


def seconds(value):
    return '--' if value is None else f'{value:.1f}s'


def recovery_snapshot(model):
    """Presentation only: measured inference and verified checks, never injected offsets."""
    state=model.vision_state
    result=model.vision_result or {}
    check=next((c for c in model.pickup_checks if c['engine']=='E1'),None)
    steps=['WAIT']*4
    if state=='OBSERVE':steps=['ACTIVE','WAIT','WAIT','WAIT']
    elif state=='HOLD':steps=['DONE','HOLD','WAIT','WAIT']
    elif state=='ACCEPTED':steps=['DONE','DONE','ACTIVE','WAIT']
    elif state=='VERIFIED' and check:steps=['DONE']*4
    if model.fault:
        if state=='ACCEPTED':steps[2]='HOLD'
        headline='HOLD | '+model.fault
        tone='hold'
    elif state=='VERIFIED' and check:
        headline='SUCCESS | Corrected pickup and rack seating verified'
        tone='success'
    else:
        headline={'WAITING':'Waiting for first engine',
                  'OBSERVE':'Observing | Capturing and estimating wrist RGB',
                  'ACCEPTED':'Correcting | Estimate accepted; seating not yet verified',
                  'HOLD':'HOLD | Observation rejected'}.get(state,state)
        tone='hold' if state=='HOLD' else 'active'
    estimate='Image estimate: --'
    if result.get('pose') is not None:
        x,y,yaw=result['pose']
        estimate=f'Image estimate: X {x:+.1f} mm | Y {y:+.1f} mm | yaw {yaw:+.2f} deg'
        if not result.get('accepted'):estimate+=' (rejected; not used)'
    observations=len(model.observations)
    outcome='Seat error: -- | Correction not verified'
    if check:
        outcome=f"Seat error: {check['seat_error_m']*1000:.2f} mm | Max lift tilt: {check['max_tilt_deg']:.2f} deg | VERIFIED"
    return dict(steps=steps,tone=tone,headline=headline,estimate=estimate,
                outcome=outcome,attempts=f'Completed observations: {observations} | Recaptures: {max(0,observations-1)}',
                case=model.pickup_case)


class Dashboard:
    def __init__(self):
        self.selected='E1'; self.last=0.; self.runtime=None
        self.window=ui.Window('Engine Warehouse Monitor',width=710,height=840)
        with self.window.frame:
            with ui.VStack(spacing=8):
                ui.Label('ENGINE WAREHOUSE | LIVE STATUS',height=26)
                with ui.HStack(height=28):
                    self.auto_button=ui.Button('Auto demo',clicked_fn=lambda:self.mode(False))
                    self.manual_button=ui.Button('Manual outbound',clicked_fn=lambda:self.mode(True))
                self.mode_label=ui.Label('',height=24)
                self.order_button=ui.Button('Request selected engine outbound',height=30,clicked_fn=self.request)
                self.queue=ui.Label('',height=26)
                self.summary=ui.Label('',height=42,word_wrap=True)
                ui.Label('ROBOT PROBLEM SOLVING | ENG-0001 | Wrist RGB',height=22)
                self.recovery_title=ui.Label('',height=38,word_wrap=True)
                self.recovery_steps=[]
                with ui.HStack(height=32,spacing=4):
                    for name in ('Observe','Estimate','Correct / grip','Verify seat'):
                        self.recovery_steps.append(ui.Button(name,enabled=False))
                self.recovery_estimate=ui.Label('',height=34,word_wrap=True)
                self.recovery_outcome=ui.Label('',height=34,word_wrap=True)
                self.recovery_attempts=ui.Label('',height=24)
                ui.Label('First engine only | Mask clearing is operator-assisted | Kinematic verification',height=22)
                ui.Label('Rack front view | select a cell or engine',height=20)
                self.cells={}
                for left,right in (('Left upper','B'),('Left lower','A')):
                    with ui.HStack(height=55,spacing=8):
                        ui.Button(left+'\nEMPTY (unused)',enabled=False)
                        self.cells[right]=ui.Button('',clicked_fn=lambda c=right:self.select_cell(c))
                ui.Label('Serial | location/state | vision | cell',height=20)
                self.rows={}
                for eid in ('E1','E2','E3'):
                    self.rows[eid]=ui.Button('',height=30,clicked_fn=lambda e=eid:self.select(e))
                self.detail=ui.Label('',height=75,word_wrap=True)
                ui.Label('Recent events (simulation time)',height=20)
                self.events=ui.Label('',word_wrap=True)
                ui.Label('Demo serials | simulated vision | times reset with Stop / Reset',height=24)
        self.update(None,force=True)

    def mode(self,manual):
        if self.runtime and getattr(self.runtime,'is_multi',False):
            self.runtime.model.set_manual(manual)
            self.update(self.runtime,force=True)

    def request(self):
        if self.runtime and getattr(self.runtime,'is_multi',False):
            self.runtime.model.request_outbound(self.selected)
            self.update(self.runtime,force=True)

    def show(self):
        self.window.visible=True

    def select(self,eid):
        self.selected=eid;self.update(self.runtime,force=True)

    def select_cell(self,cell):
        if self.runtime and getattr(self.runtime,'is_multi',False):
            eid=self.runtime.model.cells[cell]
            if eid:self.select(eid)

    def update(self,runtime,force=False):
        now=time.monotonic()
        if not force and runtime is self.runtime and now-self.last<.25:return
        self.last=now;self.runtime=runtime
        if not runtime or not getattr(runtime,'is_multi',False):
            self.recovery_title.text='Load three-engine scenario to observe recovery.'
            self.recovery_title.set_style({'color':0xffdddddd})
            self.recovery_estimate.text=self.recovery_outcome.text=self.recovery_attempts.text=''
            self.update_recovery_steps(['WAIT']*4)
            self.auto_button.enabled=False;self.manual_button.enabled=False;self.order_button.enabled=False
            self.mode_label.text='';self.queue.text=''
            self.summary.text='Load three-engine scenario to view live inventory.'
            for cell,button in self.cells.items():button.text=cell+' | --';button.enabled=False
            for eid,button in self.rows.items():button.text=serial(eid)+' | --';button.enabled=False
            self.detail.text='No three-engine scenario connected.';self.events.text=''
            return
        model=runtime.model;rows=snapshot(model)
        recovery=recovery_snapshot(model)
        colors={'active':0xffffb45c,'hold':0xff49a7ff,'success':0xff7bd57b}
        self.recovery_title.text=recovery['case']+' | '+recovery['headline']
        self.recovery_title.set_style({'color':colors[recovery['tone']]})
        self.update_recovery_steps(recovery['steps'])
        self.recovery_estimate.text=recovery['estimate']
        self.recovery_outcome.text=recovery['outcome']
        self.recovery_attempts.text=recovery['attempts']
        self.auto_button.enabled=self.manual_button.enabled=model.time==0
        self.mode_label.text=('MANUAL OUTBOUND' if model.manual else 'AUTO DEMO')+' | Reset before changing mode'
        self.order_button.enabled=model.can_request(self.selected)
        self.queue.text='Outbound queue: '+(' -> '.join(serial(e) for e in model.requests) or '--')
        waiting=sum(e['visible'] and e['owner']=='pallet' for e in model.engines.values())
        repair=sum(r['state']=='WAIT_REWORK' for r in rows.values())
        occupied=sum(e is not None for e in model.cells.values())
        self.summary.text=(f'Model {model.time:.1f}s | Infeed / waiting {waiting} | Repair {repair}\n'
                           f'Stored {occupied}/4 (2 scheduled cells) | Shipped {len(model.shipped)}')
        for cell,button in self.cells.items():
            eid=model.cells[cell];button.enabled=bool(eid)
            button.text=f'{cell} | '+(serial(eid) if eid else 'EMPTY')
            button.set_style({'background_color':0xff486335 if eid else 0xff383838})
        for eid,button in self.rows.items():
            row=rows[eid];button.enabled=True
            button.text=f"{serial(eid)} | {row['state']} | {row['vision']} | {row['cell']}"
        row=rows[self.selected]
        self.detail.text=(f"Selected: {serial(self.selected)} | {row['state']} | Cell {row['cell']}\n"
                          f"Infeed entry: {seconds(row['start'])} | Stored: {seconds(row['stored'])}\n"
                          f"Entry to storage{' (running)' if row['stored'] is None else ''}: {seconds(row['elapsed'])}")
        self.events.text='\n'.join(f"{e['time']:6.1f}s  {serial(e['engine'])}  {e['event']}" for e in model.events[-7:])

    def update_recovery_steps(self,steps):
        colors={'WAIT':0xff383838,'ACTIVE':0xff925b25,'DONE':0xff426b35,'HOLD':0xff2767a0}
        for button,name,state in zip(self.recovery_steps,('1 Observe','2 Estimate','3 Correct / grip','4 Verify seat'),steps):
            button.text=name+'\n'+state
            button.set_style({'background_color':colors[state],'color':0xffeeeeee})

    def close(self):
        self.runtime=None;self.window.destroy()
