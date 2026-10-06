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
        state = ('SHIPPED' if eid in model.shipped else
                 'PENDING' if not engine['visible'] else
                 engine['cycle'].state if engine['owner'] == 'pallet' else engine['owner'].upper())
        rows[eid] = dict(state=state, vision=engine['cycle'].result or '-',
                         cell=engine['cell'] or '-', start=start, stored=stored,
                         elapsed=None if start is None else (stored if stored is not None else model.time)-start)
    return rows


def seconds(value):
    return '--' if value is None else f'{value:.1f}s'


class Dashboard:
    def __init__(self):
        self.selected='E1'; self.last=0.; self.runtime=None
        self.window=ui.Window('Engine Warehouse Monitor',width=650,height=580)
        with self.window.frame:
            with ui.VStack(spacing=8):
                ui.Label('ENGINE WAREHOUSE | LIVE STATUS',height=26)
                self.summary=ui.Label('',height=42,word_wrap=True)
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
            self.summary.text='Load three-engine scenario to view live inventory.'
            for cell,button in self.cells.items():button.text=cell+' | --';button.enabled=False
            for eid,button in self.rows.items():button.text=serial(eid)+' | --';button.enabled=False
            self.detail.text='No three-engine scenario connected.';self.events.text=''
            return
        model=runtime.model;rows=snapshot(model)
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

    def close(self):
        self.runtime=None;self.window.destroy()
