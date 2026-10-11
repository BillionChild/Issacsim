import unittest
from test_editor_runtime import Usd
from pickup_anomalies import build
from pickup_correction import plan,clearance,fk,np
class Tests(unittest.TestCase):
    def test_rejection(self):
        for r in ({'accepted':False,'pose':[0,0,0]},{'accepted':True,'pose':[100,0,0]},{'accepted':True,'pose':[0,float('nan'),0]}):
            with self.assertRaises(ValueError):plan(r)
    def test_correction_and_geometry(self):
        from pickup_anomalies import apply_case
        s=Usd.Stage.Open(str(build()))
        for name,pose in [('normal',[0,0,0]),('x_y_yaw',[31,15,1.5])]:
            apply_case(s,name)
            f,target,yaw=plan({'accepted':True,'pose':pose})
            p,r=fk(f[-1][1],(0,0,0))
            self.assertLess(np.linalg.norm(p-target),.0002)
            self.assertLess(abs(np.degrees(np.arctan2(r[1,0],r[0,0]))-(yaw-360 if yaw>180 else yaw)),.02)
            report=clearance(s,f);self.assertEqual(report['result'],'clear')
            print(name,report,flush=True)
if __name__=='__main__':unittest.main()
