"""Estimate-driven endpoint, level rejoin, and fail-closed lifecycle tests."""
import unittest,asyncio
from unittest.mock import patch
from test_editor_runtime import Usd,Path
from fanuc_kinematics import np,fk
from build_multi_motion import load_motion
from guided_inbound import build_guided
from level_clamp import LevelClamp
from multi_runtime import MultiRuntime

class GuidedInboundTests(unittest.TestCase):
    def test_compound_estimate_changes_pickup_and_rejoins_level(self):
        result=dict(accepted=True,pose=[30.,15.,2.])
        frames=build_guided(result,load_motion('inbound','A'))
        close=next(f for f in frames if f.owner=='gripper')
        expected=np.array([.03,-2.185,.7])
        np.testing.assert_allclose(close.payload,expected,atol=1e-6)
        clamp=LevelClamp(expected,2.,close)
        for f in frames:
            if f.owner=='gripper':clamp.sample(f)
        seat=next(f for f in frames if f.owner=='cell')
        self.assertLess(clamp.seat(seat)[2],.005)
        self.assertLess(clamp.max_tilt,.25)
        self.assertTrue(all(b.time>a.time for a,b in zip(frames,frames[1:])))
        self.assertGreater(np.linalg.norm(fk(close.q,(0,0,0))[0]-[.43,-2.2,1.35]),.02)

    def test_rejected_estimate_never_starts_robot(self):
        stage=Usd.Stage.Open(str(Path(__file__).resolve().parents[2]/'external_assets/engines/caterham_duratec/usd/warehouse_multi_layout.usda'))
        r=MultiRuntime(stage,vision_required=True);r.tick(100)
        self.assertEqual(r.model.vision_state,'OBSERVE')
        async def reject(*args):return dict(accepted=False,pose=[0,0,0],reason='HOLD: occluded RGB')
        with patch('warehouse_vision.observe',reject):asyncio.run(r.observe_pickup())
        before=r.sim_seconds;r.tick(100)
        self.assertEqual(r.sim_seconds,before);self.assertIsNone(r.model.active)
        self.assertEqual(r.model.vision_state,'HOLD');self.assertIsNone(r.model.cells['A'])
        r.reset();self.assertEqual(r.model.vision_state,'WAITING');self.assertIsNone(r.model.fault)
        r.close()

    def test_reset_invalidates_inflight_observation(self):
        stage=Usd.Stage.Open(str(Path(__file__).resolve().parents[2]/'external_assets/engines/caterham_duratec/usd/warehouse_multi_layout.usda'))
        r=MultiRuntime(stage,vision_required=True);r.tick(100)
        async def stale(*args):
            r.reset()
            return dict(accepted=True,pose=[30,15,2])
        with patch('warehouse_vision.observe',stale):asyncio.run(r.observe_pickup())
        self.assertEqual(r.model.vision_state,'WAITING');self.assertIsNone(r.model.guided_frames)
        r.close()

if __name__=='__main__':unittest.main()
