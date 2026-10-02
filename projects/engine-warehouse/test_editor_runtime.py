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

class TimingTests(unittest.TestCase):
    def run_cycle(self,dt):
        root=Path(__file__).resolve().parents[2]
        stage=Usd.Stage.Open(str(root/'external_assets/engines/caterham_duratec/usd/warehouse_u_layout_preview.usda'))
        r=EditorRuntime(stage)
        for _ in range(30000):
            if r.cycle.state=='WAIT_REWORK':r.repair()
            r.tick(dt,wall_dt=dt)
            if r.storage.state=='DONE':break
        self.assertEqual(r.storage.state,'DONE')
        # Wait time depends on when an operator presses repair; exclude it.
        duration=r.sim_seconds-r.phase_seconds.get('WAIT_REWORK',0.)
        self.assertTrue(r.storage.cell_occupied)
        r.close();return duration

    def test_variable_frame_rates_preserve_process_time(self):
        times=[self.run_cycle(dt) for dt in (1/60,1/20,.2)]
        self.assertLess(max(times)-min(times),.1)
        print('Model duration excluding manual wait:',times)

    def test_stationary_scene_does_not_reauthor_transforms(self):
        root=Path(__file__).resolve().parents[2]
        stage=Usd.Stage.Open(str(root/'external_assets/engines/caterham_duratec/usd/warehouse_u_layout_preview.usda'))
        r=EditorRuntime(stage);before=r.adapter.writes
        r.apply();self.assertEqual(r.adapter.writes,before)
        r.tick(.01);self.assertEqual(r.adapter.writes-before,2)
        r.close()

if __name__=='__main__':unittest.main()
