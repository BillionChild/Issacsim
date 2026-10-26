import unittest
from test_editor_runtime import Usd
from pxr import UsdGeom
from support_contact import ROOT,SITES,np,Rotation,engine_triangles,underside,validate_alignment
class SupportTests(unittest.TestCase):
    def test_alignment_rejects_floating_or_rotated_engine(self):
        tool=np.array([.43,-2.2,1.35]);r=Rotation.from_euler('z',180,degrees=True).as_matrix();engine=np.array([0.,-2.2,.7])
        self.assertLess(validate_alignment(engine,np.eye(3),tool,r),1e-8)
        for delta,rot in [(np.array([0,0,.01]),np.eye(3)),(np.zeros(3),Rotation.from_euler('x',5,degrees=True).as_matrix())]:
            with self.assertRaisesRegex(ValueError,'pickup blocked'):validate_alignment(engine+delta,rot,tool,r)
    def test_both_pad_surfaces_match_actual_engine_mesh(self):
        stage=Usd.Stage.Open(str(ROOT/'projects/engine-warehouse/assets/engine_jig.usda'));tri=engine_triangles()
        for side,*_ in SITES:
            m=UsdGeom.Mesh(stage.GetPrimAtPath('/EngineJig/'+side+'/SupportPad'));self.assertTrue(m)
            points=np.array(m.GetPointsAttr().Get());upper=points[:len(points)//2]
            for p in upper[::11]:self.assertAlmostEqual(float(p[2]+.65),underside(tri,.43-p[0],-p[1]),delta=.0001)
            self.assertTrue(stage.GetPrimAtPath('/EngineJig/'+side+'/LowerFinger'))
if __name__=='__main__':unittest.main()
