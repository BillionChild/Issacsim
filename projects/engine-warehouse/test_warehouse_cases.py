import unittest
from test_multi_cycle import motions
from multi_cycle import MultiCycle
from warehouse_cases import CASES,sensor_image
from fanuc_kinematics import np

class WarehouseCaseTests(unittest.TestCase):
    def test_arrival_pose_is_faulted_without_teleport(self):
        model=MultiCycle(motions(),vision_required=True);model.configure_case('x_y_yaw')
        before=model.engines['E1']['position']
        while model.vision_state!='OBSERVE':
            model.step(1/60);e=model.engines['E1']
            self.assertLess(np.linalg.norm(np.array(e['position'])-before),.009)
            self.assertEqual(e['position'],e['pallet_position'])
            self.assertEqual(e['yaw'],e['pallet_yaw']);before=e['position']
        np.testing.assert_allclose(before,[.03,-2.185,.7]);self.assertEqual(e['yaw'],2.)
        with self.assertRaises(ValueError):model.configure_case('normal')

    def test_estimate_does_not_rotate_engine_before_grip(self):
        model=MultiCycle(motions(),vision_required=True);model.configure_case('yaw');model.step(100)
        frames=motions()['inbound','A'];frames[0].yaw=-10
        model.guided_frames=frames;model.vision_state='ACCEPTED';model.step(.1)
        self.assertEqual(model.engines['E1']['owner'],'pallet')
        self.assertEqual(model.engines['E1']['yaw'],2.)

    def test_retry_is_limited_to_vision_hold_and_reset_restores_mask(self):
        model=MultiCycle(motions(),vision_required=True);model.configure_case('combined_occluded')
        self.assertFalse(model.retry_observation(True));model.step(100)
        model.vision_state='HOLD';model.fault='dark frame'
        self.assertTrue(model.retry_observation());self.assertTrue(model.sensor_occluded)
        model.vision_state='HOLD'
        self.assertTrue(model.retry_observation(True));self.assertFalse(model.sensor_occluded)
        model.reset();self.assertTrue(model.sensor_occluded)
        self.assertEqual(model.pickup_case,'combined_occluded');self.assertEqual(model.observations,[])

    def test_sensor_mask_changes_pixels_without_modifying_source(self):
        rgb=np.full((512,512,4),255,dtype=np.uint8)
        masked=sensor_image(rgb,True)
        self.assertTrue(np.all(rgb==255));self.assertTrue(np.all(masked[128:384,256:384,:3]==0))
        np.testing.assert_array_equal(sensor_image(rgb,False),rgb)

if __name__=='__main__':unittest.main()
