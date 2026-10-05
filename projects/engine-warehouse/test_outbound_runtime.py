import unittest
from test_editor_runtime import Usd,EditorRuntime,Path

class OutboundTests(unittest.TestCase):
    def test_complete_outbound_and_reset(self):
        root=Path(__file__).resolve().parents[2]
        stage=Usd.Stage.Open(str(root/'external_assets/engines/caterham_duratec/usd/warehouse_u_layout_preview.usda'))
        r=EditorRuntime(stage)
        self.assertFalse(r.request_outbound())
        for _ in range(3000):
            if r.cycle.state=='WAIT_REWORK':r.repair()
            r.tick(.1)
            if r.finished:break
        self.assertTrue(r.storage.cell_occupied);self.assertTrue(r.request_outbound())
        self.assertFalse(r.request_outbound())
        states=set();start=r.sim_seconds
        for _ in range(3000):
            r.tick(.05);o=r.outbound;states.add(o.state)
            if o.state=='TRANSFER':self.assertEqual(o.gate_open,1.)
            if o.state in ('OPENING','TRANSFER','CLOSING'):self.assertEqual(o.carrier_y,0.)
            if o.state=='CLOSING':self.assertEqual(o.motion.state,'DONE')
            if o.state in ('DISPATCH','DONE'):self.assertEqual(o.gate_open,0.)
            if r.finished:break
        self.assertEqual(states,{'OPENING','TRANSFER','CLOSING','DISPATCH','DONE'})
        self.assertEqual(o.carrier_y,2.8);self.assertFalse(r.storage.cell_occupied)
        self.assertFalse(r.request_outbound())
        engine=stage.GetPrimAtPath('/World/CarriedEngine').GetAttribute('xformOp:translate').Get()
        self.assertAlmostEqual(engine[1],2.8)
        print('Outbound model seconds:',round(r.sim_seconds-start,3))
        r.reset();self.assertEqual(o.state,'WAITING');self.assertEqual(o.gate_open,0.);self.assertEqual(o.carrier_y,0.)
        self.assertFalse(r.storage.cell_occupied);r.close()

if __name__=='__main__':unittest.main()
