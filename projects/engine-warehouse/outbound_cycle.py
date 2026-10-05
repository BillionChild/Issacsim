"""Single outbound order: gate open, transfer, gate close, carrier departure."""
from u_storage import StorageTransfer

class OutboundCycle:
    def __init__(self,frames):
        self.motion=StorageTransfer(frames);self.reset()
    def reset(self):
        self.motion.reset();self.state='WAITING';self.elapsed=0.;self.gate_open=0.;self.carrier_y=0.
    def start(self,cell_occupied,robot_ready):
        if self.state!='WAITING' or not cell_occupied or not robot_ready:return False
        self.state='OPENING';self.elapsed=0.;return True
    def step(self,dt):
        if self.state in ('WAITING','DONE'):return
        self.elapsed+=dt
        if self.state=='OPENING':
            self.gate_open=min(1.,self.elapsed/2.)
            if self.gate_open>=1.:self.state='TRANSFER';self.motion.state='MOVING';self.elapsed=0.
        elif self.state=='TRANSFER':
            self.motion.step(dt)
            if self.motion.state=='DONE':self.state='CLOSING';self.elapsed=0.
        elif self.state=='CLOSING':
            self.gate_open=max(0.,1.-self.elapsed/2.)
            if self.gate_open<=0.:self.state='DISPATCH';self.elapsed=0.
        elif self.state=='DISPATCH':
            self.carrier_y=min(2.8,self.elapsed*.4)
            if self.carrier_y>=2.8:self.state='DONE'
    def phase(self):
        return self.motion.sample().phase if self.state=='TRANSFER' else 'OUT_'+self.state
