"""Single-pallet U loop. Inspection outcomes are simulated, never inferred.

Repair completion only releases the pallet for reinspection; it cannot grant OK.
No second pallet is spawned, so the shared vision junction has one occupant.
"""
from collections import deque
import math


class ULoopCycle:
    VISION=(-2.5,-2.2,.7)
    PICKUP=(0.,-2.2,.7)
    SPEED=.4

    def __init__(self, inspection_results=('FAIL','OK')):
        self.script=tuple(inspection_results)
        if any(r not in ('OK','FAIL') for r in self.script):
            raise ValueError('Inspection outcomes must be OK or FAIL')
        self.reset()

    def reset(self):
        self.state='IDLE'; self.position=(-2.5,2.8,.7)
        self.result='PENDING'; self.inspections=0
        self.results=deque(self.script)
        self.elapsed=0.; self.duration=0.; self.target=self.position; self.origin=self.position

    @property
    def pickup_allowed(self):
        return self.state=='READY_PICKUP' and self.result=='OK' and self.position==self.PICKUP

    def _enter(self,state,target,duration=None):
        self.state=state;self.origin=self.position;self.target=target;self.elapsed=0.
        self.duration=duration if duration is not None else math.dist(self.origin,target)/self.SPEED

    def start(self):
        if self.state=='IDLE':self._enter('INFEED',self.VISION)

    def complete_rework(self):
        if self.state!='WAIT_REWORK':return False
        self.result='PENDING'
        self._enter('RETURN_WEST',(-2.5,-3.6,.7))
        return True

    def _next(self):
        if self.state in ('INFEED','RETURN_VISION'):
            self._enter('INSPECT',self.VISION,2.)
        elif self.state=='INSPECT':
            self.inspections+=1
            self.result=self.results.popleft() if self.results else 'FAIL'
            self._enter('TO_PICKUP' if self.result=='OK' else 'PASS_PICKUP',self.PICKUP)
        elif self.state=='TO_PICKUP':self._enter('READY_PICKUP',self.PICKUP,0.)
        elif self.state=='PASS_PICKUP':self._enter('TO_EAST_TURN',(2.5,-2.2,.7))
        elif self.state=='TO_EAST_TURN':self._enter('LOOP_SOUTH',(2.5,-3.6,.7))
        elif self.state=='LOOP_SOUTH':self._enter('TO_REWORK',(0.,-3.6,.7))
        elif self.state=='TO_REWORK':self._enter('WAIT_REWORK',self.position,0.)
        elif self.state=='RETURN_WEST':self._enter('RETURN_VISION',self.VISION)

    def step(self,dt):
        if not math.isfinite(dt) or dt<0:raise ValueError('dt must be finite and nonnegative')
        while dt>0 and self.state not in ('IDLE','WAIT_REWORK','READY_PICKUP'):
            used=min(dt,self.duration-self.elapsed)
            self.elapsed+=used;dt-=used
            t=min(1.,self.elapsed/self.duration)
            self.position=tuple(a+t*(b-a) for a,b in zip(self.origin,self.target))
            if self.elapsed>=self.duration:
                self.position=self.target
                self._next()
