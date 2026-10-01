import unittest
from fanuc_kinematics import np, fk, LOW, HIGH
from u_loop_cycle import ULoopCycle
from u_storage import StorageTransfer, build_transfer, IDLE, CELL

class StorageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.frames=build_transfer()

    def test_permission_is_gated_and_consumed_once(self):
        c=ULoopCycle();r=StorageTransfer(self.frames)
        self.assertFalse(r.try_start(c))
        c.start();c.step(1000)
        self.assertEqual(c.state,'WAIT_REWORK');self.assertFalse(r.try_start(c))
        np.testing.assert_allclose(r.sample().q,IDLE)
        c.complete_rework();c.step(9.8)
        self.assertFalse(r.try_start(c))
        c.step(1000);self.assertTrue(r.try_start(c));self.assertFalse(r.try_start(c))
        r.step(1000)
        self.assertEqual(r.state,'DONE');self.assertTrue(r.cell_occupied)
        self.assertFalse(r.try_start(c))
        r.reset();self.assertFalse(r.cell_occupied);np.testing.assert_allclose(r.sample().q,IDLE)

    def test_carried_pose_and_continuity(self):
        for a,b in zip(self.frames,self.frames[1:]):
            self.assertTrue(np.all(b.q>=LOW-1e-7) and np.all(b.q<=HIGH+1e-7))
            self.assertLessEqual(np.max(np.abs(np.degrees(b.q-a.q)))/(b.time-a.time),20.001)
            self.assertLess(np.linalg.norm(b.payload-a.payload),.025)
            if b.owner=='gripper':
                p,r=fk(b.q,(0,0,0))
                np.testing.assert_allclose(r[:,2],[0,0,1],atol=2e-4)
                np.testing.assert_allclose(b.payload,p+r@[.43,0,-.65],atol=1e-6)
                self.assertEqual(b.opening,0.)
        last=self.frames[-1]
        np.testing.assert_allclose(last.payload,CELL,atol=2e-4)
        np.testing.assert_allclose(last.q,IDLE)
        self.assertEqual(last.owner,'cell')

if __name__=='__main__':unittest.main()
