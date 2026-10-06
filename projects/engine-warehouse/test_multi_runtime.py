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
        self.assertEqual(r.model.cells,{'A':None,'B':None})
        for name,e in r.model.engines.items():
            self.assertEqual(e['owner'],'carrier')
            v=stage.GetPrimAtPath('/World/Engines/'+name).GetAttribute('xformOp:translate').Get()
            self.assertEqual(tuple(v),e['position'])
        r.reset();self.assertFalse(r.finished);self.assertEqual(r.sim_seconds,0)
        self.assertEqual(stage.GetPrimAtPath('/World/Engines/E2').GetAttribute('visibility').Get(),'invisible')
        r.close();self.assertFalse(stage.GetPrimAtPath('/World/Engines/E1'))

if __name__=='__main__':unittest.main()
