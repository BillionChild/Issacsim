"""Build four genuine IK routes for the existing right rack cells, offline."""
import hashlib
from pathlib import Path
from fanuc_kinematics import np
from u_storage import Frame, build_transfer as inbound
from u_outbound import build_transfer as outbound
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
CELLS={'A':np.array([.6,3.,.66]),'B':np.array([.6,3.,1.66])}
FIELDS=('time','phase','q','opening','payload','yaw','owner')

def fingerprint():
    names=('build_multi_motion.py','u_storage.py','u_outbound.py','fanuc_kinematics.py')
    return hashlib.sha256(b''.join((HERE/name).read_bytes() for name in names)).hexdigest()

def cache_path(kind,cell):
    if kind not in ('inbound','outbound') or cell not in CELLS:raise ValueError('Expected inbound/outbound and A/B')
    return ROOT/'outputs'/f'multi_{kind}_{cell}_motion.npz'

def load_motion(kind,cell):
    with np.load(cache_path(kind,cell),allow_pickle=False) as data:
        if str(data['fingerprint'])!=fingerprint():raise RuntimeError('Motion source changed; rerun build_multi_motion.py')
        return [Frame(float(t),str(phase),q.copy(),float(gap),p.copy(),float(yaw),str(owner)) for t,phase,q,gap,p,yaw,owner in zip(*(data[key] for key in FIELDS))]

def build():
    (ROOT/'outputs').mkdir(exist_ok=True)
    for kind,builder in (('inbound',inbound),('outbound',outbound)):
        for cell,position in CELLS.items():
            frames=builder(position)
            np.savez_compressed(cache_path(kind,cell),fingerprint=fingerprint(),**{key:np.array([getattr(f,key) for f in frames]) for key in FIELDS})
            print(f'{kind} {cell}: {len(frames)} frames, {frames[-1].time:.2f}s',flush=True)
if __name__=='__main__':build()
