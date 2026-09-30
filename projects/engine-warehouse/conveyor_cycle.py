"""Deterministic, single-pallet demonstration; vision outcomes are simulated."""
class ConveyorCycle:
    # State, duration, endpoint. The next state is entered only after duration.
    phases = [
        ('INFEED',3.,(0,0,.7)), ('INSPECT',2.,(0,0,.7)),
        ('LIFT_NG',.5,(0,0,.715)), ('TO_BUFFER',4.,(0,1.1,.715)),
        ('LOWER_BUFFER',.5,(0,1.1,.7)), ('WAIT_REWORK',0,(0,1.1,.7)),
        ('LIFT_RETURN',.5,(0,1.1,.715)), ('RETURN',4.,(0,0,.715)),
        ('LOWER_MAIN',.5,(0,0,.7)), ('REINSPECT',2.,(0,0,.7)),
        ('TO_PICKUP',3.,(.75,0,.7)), ('DONE',0,(.75,0,.7)),
    ]

    def __init__(self): self.reset()

    def reset(self):
        self.state='IDLE';self.result='PENDING';self.position=(-.75,0,.7)
        self.pickup_allowed=False;self.index=-1;self.elapsed=0
        self.origin=self.position

    def _enter(self,index):
        self.index=index;self.state=self.phases[index][0]
        self.elapsed=0;self.origin=self.position
        if self.state=='LIFT_NG':self.result='NG'
        if self.state=='TO_PICKUP':self.result='OK'
        self.pickup_allowed=self.state=='DONE' and self.result=='OK'

    def start(self):
        if self.state=='IDLE':self._enter(0)

    def complete_rework(self):
        if self.state!='WAIT_REWORK':return False
        self.result='PENDING';self._enter(self.index+1);return True

    def step(self,dt):
        if dt<0:raise ValueError('dt must be nonnegative')
        while dt>0 and self.state not in ('IDLE','WAIT_REWORK','DONE'):
            _,duration,target=self.phases[self.index]
            used=min(dt,duration-self.elapsed);self.elapsed+=used;dt-=used
            fraction=min(1.,self.elapsed/duration)
            self.position=tuple(a+(b-a)*fraction for a,b in zip(self.origin,target))
            if self.elapsed>=duration:
                self.position=target;self._enter(self.index+1)
