import os,sys,unittest
from pathlib import Path
lib=next(Path('C:/isaacsim/extscache').glob('omni.usd.libs-*'));sys.path.insert(0,str(lib));dll=os.add_dll_directory(str(lib/'bin'))
from pxr import Usd,Sdf
from editor_runtime import EditorRuntime

class RuntimeTests(unittest.TestCase):
    def test_reset_and_repeated_attach_preserve_user_layer(self):
        root=Path(__file__).resolve().parents[2]
        s=Usd.Stage.Open(str(root/'external_assets/engines/caterham_duratec/usd/warehouse_u_layout_preview.usda'))
        user=Sdf.Layer.CreateAnonymous('user');s.GetSessionLayer().subLayerPaths.append(user.identifier)
        for _ in range(3):
            target=s.GetEditTarget().GetLayer()
            r=EditorRuntime(s)
            self.assertEqual(s.GetEditTarget().GetLayer(),target)
            r.tick(1.);self.assertEqual(r.cycle.state,'INFEED')
            r.reset();self.assertEqual(r.cycle.state,'IDLE');self.assertFalse(r.storage.cell_occupied)
            r.close()
            self.assertEqual(list(s.GetSessionLayer().subLayerPaths),[user.identifier])
            self.assertFalse(s.GetPrimAtPath('/World/CarriedEngine'))

if __name__=='__main__':unittest.main()
