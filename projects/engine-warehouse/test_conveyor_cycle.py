import unittest
from conveyor_cycle import ConveyorCycle

class CycleTests(unittest.TestCase):
    def advance_to(self, cycle, target):
        for _ in range(2000):
            if cycle.state == target: return
            cycle.step(.05)
        self.fail(f'Did not reach {target}: {cycle.state}')

    def test_rework_gate_and_pickup_permission(self):
        c=ConveyorCycle();c.start()
        self.assertFalse(c.complete_rework())
        self.advance_to(c,'WAIT_REWORK')
        self.assertAlmostEqual(c.position[1],1.1)
        for _ in range(100): c.step(.1)
        self.assertEqual(c.state,'WAIT_REWORK')
        self.assertFalse(c.pickup_allowed)
        self.assertTrue(c.complete_rework())
        self.advance_to(c,'REINSPECT')
        self.assertFalse(c.pickup_allowed)
        self.advance_to(c,'DONE')
        self.assertTrue(c.pickup_allowed)
        self.assertEqual(c.result,'OK')
        self.assertEqual(c.position,(.75,0,.7))

    def test_reset_and_idle(self):
        c=ConveyorCycle();c.step(100)
        self.assertEqual(c.state,'IDLE')
        c.start();c.step(1);c.reset()
        self.assertEqual(c.position,(-.75,0,.7))
        self.assertEqual(c.result,'PENDING')
        self.assertFalse(c.pickup_allowed)

    def test_path_stays_in_bounds_and_only_lifts_for_side_transfer(self):
        c=ConveyorCycle();c.start()
        for _ in range(2000):
            if c.state=='WAIT_REWORK':c.complete_rework()
            c.step(.03)
            x,y,z=c.position
            self.assertTrue(-.75<=x<=.75 and 0<=y<=1.1 and .7<=z<=.715)
            if y>0:self.assertAlmostEqual(x,0)
            if c.state=='DONE':break
        self.assertEqual(c.state,'DONE')

if __name__=='__main__':unittest.main()
