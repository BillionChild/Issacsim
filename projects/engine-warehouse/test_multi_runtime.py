"""USD ownership, reset and separate-scene regression for three engines."""
import unittest
from test_editor_runtime import Usd,Path
from multi_runtime import MultiRuntime

class MultiRuntimeTests(unittest.TestCase):
    def test_full_replay_and_layer_cleanup(self):
        p=Path(__file__).resolve().parents[2]/'external_assets/engines/caterham_duratec/usd/warehouse_multi_layout.usda'
        stage=Usd.Stage.Open(str(p));r=MultiRuntime(stage)
        self.assertEqual(len(r.model.engines),3);self.assertEqual(len(r.model.carriers),4)
        r.tick(1200)
        self.assertTrue(r.finished);self.assertEqual(r.model.shipped,['E1','E3','E2'])
        self.assertEqual([v['engine'] for v in r.model.pickup_checks],['E1','E3','E2'])
        for result in r.model.pickup_checks:
            self.assertLess(result['max_tilt_deg'],.25)
            self.assertLess(result['seat_error_m'],.005)
        events=[(v['event'],v['engine']) for v in r.model.events]
        for eid in ('E1','E2','E3'):
            self.assertLess(events.index(('PIN_CLAMP_LOCKED',eid)),events.index(('LEVEL_PICKUP_VERIFIED',eid)))
            self.assertLess(events.index(('LEVEL_PICKUP_VERIFIED',eid)),events.index(('PIN_CLAMP_RELEASED',eid)))
            self.assertLess(events.index(('PIN_CLAMP_RELEASED',eid)),events.index(('STORED',eid)))
        self.assertEqual(r.model.cells,{'A':None,'B':None})
        for name,e in r.model.engines.items():
            self.assertEqual(e['owner'],'carrier')
            v=stage.GetPrimAtPath('/World/Engines/'+name).GetAttribute('xformOp:translate').Get()
            self.assertEqual(tuple(v),e['position'])
        r.reset();self.assertFalse(r.finished);self.assertEqual(r.sim_seconds,0)
        self.assertIsNone(r.model.clamp);self.assertEqual(r.model.pickup_checks,[])
        self.assertEqual(stage.GetPrimAtPath('/World/Engines/E2').GetAttribute('visibility').Get(),'invisible')
        r.close();self.assertFalse(stage.GetPrimAtPath('/World/Engines/E1'))

    def test_tilt_in_route_holds_before_storage(self):
        from build_multi_motion import load_motion
        from multi_cycle import MultiCycle
        from fanuc_kinematics import np
        motions={(kind,cell):load_motion(kind,cell) for kind in ('inbound','outbound') for cell in ('A','B')}
        lifting=[f for f in motions['inbound','A'] if f.phase=='LIFT_ENGINE']
        lifting[len(lifting)//2].q[3]+=np.radians(5)
        model=MultiCycle(motions,level_pickup=True)
        model.step(1200)
        self.assertIsNotNone(model.fault)
        self.assertIn('tilt',model.fault)
        self.assertIsNone(model.cells['A'])
        self.assertEqual(model.engines['E1']['owner'],'gripper')
        self.assertFalse(any(v['event']=='STORED' for v in model.events))
        stopped=model.time;model.step(10);self.assertEqual(model.time,stopped)

if __name__=='__main__':unittest.main()
