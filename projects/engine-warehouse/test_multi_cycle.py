import math
import unittest
from fanuc_kinematics import np
from u_storage import Frame
from multi_cycle import MultiCycle


def motions():
    result={}
    for cell,z in [('A',.66),('B',1.66)]:
        for kind,owners,positions in [
            ('inbound',['pallet','gripper','cell','cell'],[(0,-2.2,.7),(1,0,2),(.6,3,z),(.6,3,z)]),
            ('outbound',['cell','gripper','outbound','outbound'],[(.6,3,z),(1,0,2),(2.5,0,.85),(2.5,0,.85)])]:
            result[kind,cell]=[Frame(float(i),str(i),np.zeros(6),.12,np.array(p,dtype=float),0.,o) for i,(o,p) in enumerate(zip(owners,positions))]
    return result


class MultiCycleTests(unittest.TestCase):
    def test_sequence_ownership_spacing_and_reset(self):
        model=MultiCycle(motions(),empty_pallet_route=True)
        for _ in range(24000):
            model.step(1/60)
            self.assertLessEqual(sum(e['owner']=='gripper' for e in model.engines.values()),1)
            for cell,eid in model.cells.items():
                if eid:self.assertEqual(model.engines[eid]['owner'],'cell')
            carriers=list(model.carriers.values())
            for i,a in enumerate(carriers):
                for b in carriers[i+1:]:self.assertGreaterEqual(math.dist(a['position'],b['position']),1.3-1e-8)
            if model.done:break
        self.assertTrue(model.done)
        self.assertEqual(model.shipped,['E1','E3','E2'])
        self.assertTrue(all(e['visible'] for e in model.engines.values()))
        self.assertTrue(all(not e['pallet_visible'] for e in model.engines.values()))
        self.assertEqual(sum(e['event']=='EMPTY_PALLET_EXIT' for e in model.events),3)
        self.assertEqual(model.cells,{'A':None,'B':None})
        self.assertEqual(model.carriers['C4']['position'],(2.5,0.,.7))
        self.assertIsNone(model.carriers['C4']['engine'])
        self.assertEqual([model.carriers[c]['engine'] for c in ('C1','C2','C3')],['E1','E3','E2'])
        for cid,eid in [('C1','E1'),('C2','E3'),('C3','E2')]:
            self.assertAlmostEqual(model.carriers[cid]['position'][1],model.SHIP_Y[eid])
            self.assertEqual(model.carriers[cid]['gate_open'],0.)
        events=[(e['event'],e['engine']) for e in model.events]
        self.assertLess(events.index(('WAIT_REWORK','E2')),events.index(('STORED','E3')))
        self.assertLess(events.index(('ROBOT_READY','E3')),events.index(('REWORK_COMPLETE','E2')))
        self.assertLess(events.index(('OUTBOUND_DONE','E1')),events.index(('INBOUND_START','E2')))
        first=list(model.events)
        model.reset();model.step(400)
        self.assertEqual(first,model.events)

    def test_real_routes_pallet_nonoverlap_and_opening_continuity(self):
        from build_multi_motion import load_motion, cache_path
        keys=[(kind,cell) for kind in ('inbound','outbound') for cell in ('A','B')]
        if not all(cache_path(*key).exists() for key in keys):
            self.skipTest('Offline motion caches are not available')
        model=MultiCycle({key:load_motion(*key) for key in keys},empty_pallet_route=True)
        for _ in range(24000):
            before={eid:e['position'] for eid,e in model.engines.items()}
            model.step(.05)
            visible=[e for e in model.engines.values() if e['pallet_visible']]
            for i,a in enumerate(visible):
                for b in visible[i+1:]:
                    dx=abs(a['pallet_position'][0]-b['pallet_position'][0])
                    dy=abs(a['pallet_position'][1]-b['pallet_position'][1])
                    self.assertTrue(dx>=.8-1e-8 or dy>=.8-1e-8, (model.time,a['pallet_position'],b['pallet_position']))
            for e in model.engines.values():
                if e['owner']=='pallet':self.assertEqual(e['position'],e['pallet_position'])
            if model.active and model.active[0]=='outbound' and model.active[3].state=='OPENING':
                eid=model.active[1]
                self.assertEqual(before[eid],model.engines[eid]['position'])
            if model.done:break
        self.assertTrue(model.done)

    def test_manual_orders_wait_fifo_reset_and_spacing(self):
        model=MultiCycle(motions(),empty_pallet_route=True)
        self.assertTrue(model.set_manual(True))
        self.assertFalse(model.request_outbound('E2'))
        model.step(150)
        self.assertEqual(model.shipped,[])
        self.assertFalse(model.set_manual(False))
        self.assertTrue(model.request_outbound('E3'))
        self.assertFalse(model.request_outbound('E3'))
        self.assertTrue(model.request_outbound('E1'))
        for _ in range(12000):
            model.step(.05)
            if model.can_request('E2'):model.request_outbound('E2')
            carriers=list(model.carriers.values())
            for i,a in enumerate(carriers):
                for b in carriers[i+1:]:
                    self.assertGreaterEqual(math.dist(a['position'],b['position']),1.3-1e-8)
            if model.done:break
        self.assertTrue(model.done)
        self.assertEqual(model.shipped,['E3','E1','E2'])
        self.assertEqual(model.requests,[])
        model.reset()
        self.assertTrue(model.manual)
        self.assertEqual(model.requests,[])
        self.assertTrue(model.set_manual(False))

    def test_request_during_robot_return_waits(self):
        model=MultiCycle(motions())
        model.set_manual(True)
        while model.engines['E1']['owner']!='cell':model.step(.05)
        active=model.active
        self.assertTrue(model.request_outbound('E1'))
        self.assertIs(model.active,active)
        self.assertFalse(model.request_outbound('E1'))
        model.step(.05)
        self.assertEqual(model.active[0],'inbound')

    def test_dt_validation_and_zero(self):
        model=MultiCycle(motions())
        for dt in [-1,float('nan'),float('inf')]:
            with self.assertRaises(ValueError):model.step(dt)
        model.step(0);self.assertEqual(model.time,0)
        self.assertEqual([eid for eid,e in model.engines.items() if e['visible']],['E1'])
        self.assertEqual([eid for eid,e in model.engines.items() if e['pallet_visible']],['E1'])

    def test_request_e1_while_e2_to_pickup(self):
        model=MultiCycle(motions())
        for _ in range(24000):
            model.step(1/60)
            if model.active and model.active[:2]==('outbound','E1'):
                self.assertEqual(model.engines['E2']['cycle'].state,'TO_PICKUP');break
        else:self.fail('E1 outbound never started')

if __name__=='__main__':unittest.main()
