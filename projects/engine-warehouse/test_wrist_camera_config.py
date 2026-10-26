"""Saved runtime cameras can leave an untyped override in the root layer."""
import unittest
from test_editor_runtime import Usd
from pxr import UsdGeom
from wrist_camera import attach,TOOL,CAMERA

class CameraConfigTests(unittest.TestCase):
    def test_saved_override_gets_a_real_calibrated_camera(self):
        stage=Usd.Stage.CreateInMemory();UsdGeom.Xform.Define(stage,TOOL)
        stage.OverridePrim(CAMERA)
        self.assertFalse(stage.GetPrimAtPath(CAMERA).IsA(UsdGeom.Camera))
        attach(stage)
        camera=UsdGeom.Camera(stage.GetPrimAtPath(CAMERA))
        self.assertTrue(camera)
        self.assertEqual(len(camera.GetOrderedXformOps()),1)
        self.assertEqual(camera.GetFocalLengthAttr().Get(),12.)
        expected=Usd.Stage.CreateInMemory();UsdGeom.Xform.Define(expected,TOOL);attach(expected)
        self.assertEqual(camera.GetLocalTransformation(),UsdGeom.Camera(expected.GetPrimAtPath(CAMERA)).GetLocalTransformation())

    def test_existing_camera_is_preserved_and_mounts_disabled(self):
        stage=Usd.Stage.CreateInMemory();UsdGeom.Xform.Define(stage,TOOL);attach(stage)
        camera=UsdGeom.Camera(stage.GetPrimAtPath(CAMERA));camera.GetFocalLengthAttr().Set(15.)
        before=camera.GetLocalTransformation()
        for name in ('CameraBracket','CameraOuterDrop','CameraHousing'):UsdGeom.Cube.Define(stage,TOOL+'/'+name)
        attach(stage);attach(stage)
        self.assertEqual(camera.GetLocalTransformation(),before)
        self.assertEqual(camera.GetFocalLengthAttr().Get(),15.)
        for name in ('CameraBracket','CameraOuterDrop','CameraHousing'):
            self.assertFalse(stage.GetPrimAtPath(TOOL+'/'+name).IsActive())

class RestoreCameraTests(unittest.TestCase):
    def test_restore_resets_navigated_camera_transform_and_lens(self):
        from pxr import Gf
        stage=Usd.Stage.CreateInMemory();UsdGeom.Xform.Define(stage,TOOL);attach(stage)
        camera=UsdGeom.Camera(stage.GetPrimAtPath(CAMERA));expected=camera.GetLocalTransformation()
        camera.MakeMatrixXform().Set(Gf.Matrix4d().SetTranslate(Gf.Vec3d(3,2,1)))
        camera.GetFocalLengthAttr().Set(30.)
        attach(stage,restore=True)
        self.assertEqual(camera.GetLocalTransformation(),expected)
        self.assertEqual(camera.GetFocalLengthAttr().Get(),12.)

if __name__=='__main__':unittest.main()
