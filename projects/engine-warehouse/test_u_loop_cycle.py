import unittest
from u_loop_cycle import ULoopCycle


class ULoopTests(unittest.TestCase):
    def advance(self, c, state):
        for _ in range(10000):
            if c.state == state: return
            c.step(.02)
        self.fail((c.state, state))

    def test_fail_passes_pickup_then_waits_for_human(self):
        c=ULoopCycle(); c.start()
        self.advance(c,'PASS_PICKUP')
        self.assertEqual(c.result,'FAIL'); self.assertFalse(c.pickup_allowed)
        self.advance(c,'TO_EAST_TURN')
        self.assertEqual(c.origin,(0.,-2.2,.7))
        self.assertGreaterEqual(c.position[0],0.)
        self.advance(c,'WAIT_REWORK'); p=c.position
        c.step(1000)
        self.assertEqual(c.position,p); self.assertEqual(c.state,'WAIT_REWORK')
        self.assertFalse(c.pickup_allowed)
        self.assertTrue(c.complete_rework())
        self.assertEqual(c.result,'PENDING')
        self.assertFalse(c.complete_rework())
        self.advance(c,'INSPECT')
        self.assertEqual(c.position,(-2.5,-2.2,.7)); self.assertFalse(c.pickup_allowed)
        self.advance(c,'READY_PICKUP')
        self.assertEqual(c.position,(0.,-2.2,.7)); self.assertTrue(c.pickup_allowed)
        self.assertEqual(c.inspections,2)

    def test_reinspection_can_fail_again(self):
        c=ULoopCycle(('FAIL','FAIL','OK'));c.start()
        for count in (1,2):
            self.advance(c,'WAIT_REWORK')
            self.assertEqual(c.inspections,count)
            self.assertFalse(c.pickup_allowed)
            c.complete_rework()
        self.advance(c,'READY_PICKUP')
        self.assertEqual(c.inspections,3)

    def test_segments_stay_on_loop_and_reset_clears_permission(self):
        c=ULoopCycle();c.start()
        for _ in range(10000):
            if c.state=='WAIT_REWORK':c.complete_rework()
            c.step(.02)
            x,y,_=c.position
            on_route = (abs(x+2.5)<1e-8 and -3.6<=y<=2.8) or (abs(x-2.5)<1e-8 and -3.6<=y<=-2.2) or ((abs(y+2.2)<1e-8 or abs(y+3.6)<1e-8) and -2.5<=x<=2.5)
            self.assertTrue(on_route,c.position)
            self.assertEqual(c.position[2],.7)
            if c.state=='READY_PICKUP':break
        self.assertTrue(c.pickup_allowed)
        c.reset();self.assertFalse(c.pickup_allowed)
        self.assertEqual(c.result,'PENDING');self.assertEqual(c.inspections,0)
        self.assertFalse(c.complete_rework())
        with self.assertRaises(ValueError):c.step(-.1)

    def test_ok_can_go_directly_and_missing_result_fails_closed(self):
        c=ULoopCycle(('OK',));c.start();c.step(1000)
        self.assertEqual(c.state,'READY_PICKUP')
        c=ULoopCycle(());c.start();c.step(1000)
        self.assertEqual(c.state,'WAIT_REWORK');self.assertFalse(c.pickup_allowed)


if __name__=='__main__':unittest.main()
