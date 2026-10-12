"""Regression: a stable hold must not hide a transient tilt during pickup."""
import unittest
from test_editor_runtime import Usd
from pxr import UsdGeom,Gf
from grasp_contact import ContactTrial,np

class PoseMetricsTests(unittest.TestCase):
    def trial(self):
        stage=Usd.Stage.CreateInMemory()
        engine=UsdGeom.Xform.Define(stage,'/Engine')
        rotation=engine.AddRotateXOp()
        rotation.Set(0.)
        trial=ContactTrial.__new__(ContactTrial)
        trial.stage=stage;trial.engine=engine.GetPrim();trial.center=Gf.Vec3d(0)
        trial.initial=trial.position();trial.initial_rotation=trial.rotation()
        trial.lifted=np.array([0.,0.,.2]);trial.hold=[trial.lifted.copy()]*5
        trial.fixture_released=True;trial.grip=object();trial.seat_error=0.
        trial.pose_samples=[trial.pose_error()]
        return trial,rotation

    def test_transient_tilt_is_rejected_after_stable_hold_and_reseat(self):
        trial,rotation=self.trial()
        rotation.Set(3.)
        trial.pose_samples.append(trial.pose_error())
        rotation.Set(0.)
        trial.pose_samples.append(trial.pose_error())
        report=trial.report()
        self.assertAlmostEqual(report['max_rotation_change_deg'],3.,places=4)
        self.assertFalse(report['success'])

    def test_unchanged_pose_passes(self):
        trial,_=self.trial()
        self.assertTrue(trial.report()['success'])

if __name__=='__main__':unittest.main()
