"""Deterministic three-engine demo; all motion is kinematic.

Events are dictionaries with time (seconds), event, and engine (E1..E3).
Engine owner is pallet/gripper/cell/carrier; each engine has one owner.
Empty pallet routing is opt-in until the return route is approved.
"""
import math
from u_loop_cycle import ULoopCycle
from u_storage import StorageTransfer
from outbound_cycle import OutboundCycle


class MultiCycle:
    SPEED = .4
    SHIP_Y = {'E1': 5.4, 'E3': 4.1, 'E2': 2.8}

    def __init__(self, motions, empty_pallet_route=False):
        self.motions = motions
        self.empty_pallet_route = empty_pallet_route
        for kind in ('inbound', 'outbound'):
            for cell in ('A', 'B'):
                frames = motions[kind, cell]
                if not frames or frames[0].time != 0 or any(b.time <= a.time for a,b in zip(frames, frames[1:])):
                    raise ValueError('Motion frames must start at zero and increase strictly')
        self.manual = False
        self.reset()

    def reset(self):
        self.requests = []; self.ship_targets = {}
        self.time = 0.; self.events = []; self.cells = {'A': None, 'B': None}
        self.engines = {}
        for i, script in enumerate((('OK',), ('FAIL','OK'), ('OK',)), 1):
            cycle = ULoopCycle(script)
            self.engines[f'E{i}'] = dict(cycle=cycle, owner='pallet', cell=None,
                position=cycle.position, yaw=0., pallet_position=cycle.position, pallet_visible=i==1, visible=i==1)
        self.carriers = {f'C{i+1}': dict(position=(2.5+i*1.3,0.,.7), engine=None,gate_open=0.) for i in range(4)}
        self.robot_frame = self.motions['inbound','A'][0]
        self.phase = 'E1_INFEED'; self.done = False; self.active = None
        self.stage = 0; self.shipped = []; self.empty_routes = {}; self._seen = set()
        self.engines['E1']['cycle'].start()
        self._event('SCENE_ENTRY','E1')

    def set_manual(self, manual):
        # Mode changes are only accepted before playback / after Reset.
        if self.time != 0:return False
        self.manual = bool(manual)
        self.requests.clear()
        return True

    def can_request(self, eid):
        return (self.manual and eid in self.engines
                and self.engines[eid]['owner']=='cell'
                and eid not in self.requests and eid not in self.shipped
                and not (self.active and self.active[:2]==('outbound',eid)))

    def request_outbound(self, eid):
        if not self.can_request(eid):return False
        self.requests.append(eid);self._event('OUTBOUND_REQUEST',eid)
        return True

    def _manual_schedule(self):
        if self.active:return
        e=self.engines['E2']
        if e['owner']=='pallet':
            for cell,occupant in self.cells.items():
                if occupant is None and self._inbound('E2',cell):return
        self.done=len(self.shipped)==3 and not any(self.empty_routes.values())
        self.phase='DONE' if self.done else 'WAITING_FOR_ORDER_OR_FREE_CELL'

    def _event(self, event, engine):
        self.events.append(dict(time=self.time, event=event, engine=engine))

    def _inbound(self, eid, cell):
        transfer = StorageTransfer(self.motions['inbound',cell])
        if self.active or self.cells[cell] is not None or not transfer.try_start(self.engines[eid]['cycle']):
            return False
        self.active = ('inbound',eid,cell,transfer,None)
        self._event('INBOUND_START',eid)
        return True

    def _outbound(self, eid):
        cid = next((c for c,v in self.carriers.items() if v['engine'] is None and math.dist(v['position'],(2.5,0.,.7)) < 1e-8),None)
        if self.active or cid is None:return False
        cell = self.engines[eid]['cell']
        transfer = OutboundCycle(self.motions['outbound',cell])
        if not transfer.start(self.cells[cell]==eid,True):return False
        self.ship_targets[eid] = 5.4-1.3*len(self.shipped)
        self.active = ('outbound',eid,cell,transfer,cid)
        self._event('OUTBOUND_START',eid)
        return True

    def _empty_step(self, dt):
        for eid, route in list(self.empty_routes.items()):
            if not route:continue
            e = self.engines[eid]; target = route[0]
            # Empty pallets queue east of the occupied repair station.
            if target[1] == -3.6 and target[0] < 1.3 and self.engines['E2']['cycle'].state == 'WAIT_REWORK':continue
            p = e['pallet_position']; d = math.dist(p,target)
            candidate=target if d <= self.SPEED*dt else tuple(a+(b-a)*self.SPEED*dt/d for a,b in zip(p,target))
            if any(other_id!=eid and other['pallet_visible'] and math.dist(candidate,other['pallet_position'])<1.2 for other_id,other in self.engines.items()):continue
            e['pallet_position']=candidate
            if candidate==target:route.pop(0)
            if not route:
                e['pallet_visible']=False;self._event('EMPTY_PALLET_EXIT',eid)

    def _tick(self,dt):
        self.time += dt
        for eid,e in self.engines.items():
            if e['owner']=='pallet':
                c=e['cycle']; old=c.state;c.step(dt)
                e['position']=c.position;e['pallet_position']=c.position
                if c.state != old and c.state in ('WAIT_REWORK','TO_PICKUP'):
                    self._event('WAIT_REWORK' if c.state=='WAIT_REWORK' else 'INSPECTION_OK',eid)
        if self.active:
            kind,eid,cell,t,cid=self.active;e=self.engines[eid]
            t.step(dt)
            if kind=='inbound' or t.state in ('TRANSFER','CLOSING','DISPATCH','DONE'):
                f=t.sample() if kind=='inbound' else t.motion.sample()
                self.robot_frame=f;owner='carrier' if f.owner=='outbound' else f.owner
                if e['owner']=='pallet' and owner!='pallet' and self.empty_pallet_route:
                    self.empty_routes[eid]=[(2.5,-2.2,.7),(2.5,-3.6,.7),(1.3,-3.6,.7),(-2.5,-3.6,.7),(-4.5,-3.6,.7)]
                e['owner']=owner
                e['position']=e['pallet_position'] if owner=='pallet' else tuple(float(v) for v in f.payload)
                e['yaw']=float(f.yaw)
                if owner=='cell':
                    e['cell']=cell;self.cells[cell]=eid
                    if ('STORED',eid) not in self._seen:
                        self._seen.add(('STORED',eid));self._event('STORED',eid)
                elif kind=='outbound':
                    self.cells[cell]=None;e['cell']=None
                if owner=='carrier':self.carriers[cid]['engine']=eid
            if kind=='outbound':
                carrier=self.carriers[cid];carrier['gate_open']=t.gate_open
                if t.state in ('DISPATCH','DONE'):
                    y=min(self.ship_targets[eid],carrier['position'][1]+self.SPEED*dt)
                    carrier['position']=(2.5,y,.7)
                if e['owner']=='carrier':
                    p=carrier['position']; e['position']=(p[0],p[1],float(self.motions['outbound',cell][-1].payload[2]))
                finished=t.state=='DONE' and carrier['position'][1]>=self.ship_targets[eid]-1e-9
            else:finished=t.state=='DONE'
            self.phase=f'{eid}_{kind.upper()}_{t.state}'
            if finished:
                self._event('ROBOT_READY' if kind=='inbound' else 'OUTBOUND_DONE',eid)
                if kind=='outbound':self.shipped.append(eid)
                self.active=None
        # Empty feed carriers maintain their 1.3 m pitch; only advance after dispatch clears.
        moving=[v for v in self.carriers.values() if v['engine'] is not None and v['position'][1]<1.3-1e-9]
        if not moving:
            empty=[v for v in self.carriers.values() if v['engine'] is None]
            for i,c in enumerate(empty):
                x=max(2.5+i*1.3,c['position'][0]-self.SPEED*dt)
                c['position']=(x,0.,.7)
        self._empty_step(dt)
        if self.manual and not self.active and self.requests and self._outbound(self.requests[0]):
            self.requests.pop(0)
            return
        e1,e2,e3=(self.engines[e] for e in ('E1','E2','E3'))
        if self.stage==0 and self._inbound('E1','A'):self.stage=1
        elif self.stage==1 and not self.active:
            e2['visible']=True;e2['pallet_visible']=True
            e2['cycle'].start();self._event('SCENE_ENTRY','E2');self.stage=2;self.phase='E2_INFEED'
        elif self.stage==2 and e2['cycle'].state=='WAIT_REWORK':
            e3['visible']=True;e3['pallet_visible']=True
            e3['cycle'].start();self._event('SCENE_ENTRY','E3');self.stage=3;self.phase='E3_INFEED'
        elif self.stage==3 and self._inbound('E3','B'):self.stage=4
        elif self.stage==4 and not self.active:
            e2['cycle'].complete_rework();self._event('REWORK_COMPLETE','E2');self.stage=5
        elif self.manual and self.stage>=5:self._manual_schedule()
        elif self.stage==5 and e2['cycle'].state=='TO_PICKUP' and self._outbound('E1'):self.stage=6
        elif self.stage==6 and 'E1' in self.shipped and self._inbound('E2','A'):self.stage=7
        elif self.stage==7 and not self.active and self._outbound('E3'):self.stage=8
        elif self.stage==8 and 'E3' in self.shipped and self._outbound('E2'):self.stage=9
        elif self.stage==9 and 'E2' in self.shipped:
            self.phase='EMPTY_PALLET_RETURN' if any(self.empty_routes.values()) else 'DONE'
            self.done=self.phase=='DONE'

    @property
    def summary(self):
        return dict(phase=self.phase,done=self.done,time=self.time,shipped=list(self.shipped),
                    cells=dict(self.cells),events=[dict(event) for event in self.events])

    def step(self, dt):
        if not math.isfinite(dt) or dt<0:raise ValueError('dt must be finite and nonnegative')
        while dt>1e-12 and not self.done:
            used=min(dt,1/60);self._tick(used);dt-=used
