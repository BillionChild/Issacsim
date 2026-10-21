import unittest
from test_editor_runtime import Usd  # Local USD bootstrap for offline checks.
from fanuc_kinematics import np,Rotation,fk
from build_multi_motion import load_motion
from engine_guided import build_engine_guided,GRIP_OFFSET,R180
from level_clamp import LevelClamp
from multi_cycle import MultiCycle
from warehouse_cases import ENGINE_CASES
from test_multi_cycle import motions

class EnginePoseTests(unittest.TestCase):
    def test_depth_crop_excludes_pallet_and_rejects_missing_engine(self):
        from engine_depth import engine_surface,register,world_points
        p=np.array([[0,-2.2,.72],[0,-2.2,1.3],[2,-2.2,1.3]])
        np.testing.assert_allclose(engine_surface(p),[[0,-2.2,1.3]])
        np.testing.assert_allclose(world_points(np.full((3,3),2.),np.eye(4),100)[4],[0,0,-2])
        with self.assertRaisesRegex(ValueError,'insufficient'):register(p,p)

    def test_engine_fault_does_not_move_pallet_or_trigger_repair(self):
        for name,pose in ENGINE_CASES.items():
            m=MultiCycle(motions(),vision_required=True);m.configure_case(name);m.step(100)
            e=m.engines['E1']
            np.testing.assert_allclose(e['pallet_position'],[0,-2.2,.7])
            self.assertEqual(e['pallet_yaw'],0)
            np.testing.assert_allclose(e['position'],np.array([0,-2.2,.7])+np.array(pose[:3])/1000)
            np.testing.assert_allclose([e['roll'],e['pitch'],e['yaw']],pose[3:])
            self.assertEqual(e['cycle'].result,'OK')
            self.assertFalse(any(v['event']=='WAIT_REWORK' and v['engine']=='E1' for v in m.events))
            before=e['position'];m.guided_frames=motions()['inbound','A'];m.vision_state='ACCEPTED'
            m.step(.1)
            self.assertEqual(e['owner'],'pallet');self.assertEqual(e['position'],before)

    def test_grip_follows_engine_then_levels_before_seating(self):
        pose=np.array([20,-12,20,1.5,-1,2.])
        frames=build_engine_guided(dict(accepted=True,pose6=pose),load_motion('inbound','A'))
        closed=next(f for f in frames if f.owner=='gripper')
        p,r=fk(closed.q,(0,0,0));expected=np.array([0,-2.2,.7])+pose[:3]/1000
        np.testing.assert_allclose(p+r@GRIP_OFFSET,expected,atol=.0002)
        np.testing.assert_allclose(r@R180,Rotation.from_euler('xyz',pose[3:],degrees=True).as_matrix(),atol=.0002)
        clamp=LevelClamp(expected,pose[5],closed,pose[3],pose[4])
        for f in frames:
            if f.owner=='gripper':clamp.sample(f)
        seat=next(f for f in frames if f.owner=='cell')
        self.assertLess(clamp.seat(seat)[2],.005);self.assertLess(clamp.tilt,.25)
        self.assertGreater(clamp.max_tilt,1.)
        self.assertTrue(all(b.time>a.time for a,b in zip(frames,frames[1:])))

    def test_unleveled_engine_cannot_pass_seat_check(self):
        frames=load_motion('inbound','A');f=next(f for f in frames if f.owner=='gripper')
        clamp=LevelClamp(f.payload,f.yaw,f,2.,0.)
        with self.assertRaisesRegex(ValueError,'not leveled'):clamp.seat(f)

    def test_invalid_estimate_never_plans(self):
        for result in ({'accepted':False,'pose6':[0]*6},{'accepted':True,'pose6':[0,0,0,20,0,0]}):
            with self.assertRaises(ValueError):build_engine_guided(result,[])

if __name__=='__main__':unittest.main()
