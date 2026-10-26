"""Correction explanation must use estimates and commands, never injected truth."""
import unittest,tempfile
from pathlib import Path
from types import SimpleNamespace as NS
from correction_story import story,command_delta,comparison_image,np

class StoryTests(unittest.TestCase):
    def model(self):
        frame=NS(owner='gripper',q=np.zeros(6))
        return NS(vision_result={'accepted':True,'pose6':[12,-4,8,1,-2,2]},robot_frame=NS(phase='LIFT_ENGINE_POSE'),pickup_checks=[],fault=None,engines={'E1':{'owner':'gripper','position':(999,999,999)}},motions={('inbound','A'):[frame]},guided_frames=[frame])
    def test_lift_and_success_are_distinct(self):
        m=self.model();self.assertIn('CURRENT POSE',story(m)['title']);self.assertFalse(story(m)['verified'])
        m.pickup_checks=[{'engine':'E2','seat_error_m':0}];self.assertFalse(story(m)['verified'])
        m.pickup_checks.append({'engine':'E1','seat_error_m':.001});self.assertTrue(story(m)['verified'])
        m.fault='Lost grip';self.assertFalse(story(m)['verified'])
    def test_commands_not_injected_engine_coordinates(self):
        m=self.model();self.assertTrue(np.allclose(command_delta(m),0))
        m.engines['E1']['position']=(0,0,0);self.assertTrue(np.allclose(command_delta(m),0))
        m.vision_result['accepted']=False;self.assertIsNone(command_delta(m))
    def test_evidence_can_be_absent_or_rejected(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as d:
            for i,r in enumerate([self.model().vision_result,{'accepted':False,'pose6':None}]):
                p=Path(d)/f'{i}.png';comparison_image(r,p)
                with Image.open(p) as im:self.assertEqual(im.size,(1100,650))

if __name__=='__main__':unittest.main()
