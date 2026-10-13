"""Virtual wrist camera: fixed calibration, without physical mounting geometry."""
from pxr import UsdGeom,Gf

TOOL='/World/Robot/Base/J1/J2/J3/J4/J5/J6/EngineJig'
CAMERA=TOOL+'/WristCamera'

def attach(stage):
    if not stage.GetPrimAtPath(TOOL):raise RuntimeError('FANUC tool is missing')
    # Suppress mounts in older referenced/saved scenes as well as new scenes.
    # Keep the Camera prim and its calibrated transform/lens unchanged.
    for name in ('CameraBracket','CameraOuterDrop','CameraHousing'):
        path=TOOL+'/'+name
        if stage.GetPrimAtPath(path):stage.OverridePrim(path).SetActive(False)
    if stage.GetPrimAtPath(CAMERA):return CAMERA
    # Tool-local optical axis covers the pallet at hover and during approach.
    eye=Gf.Vec3d(.43,.75,-.3);target=Gf.Vec3d(.43,0,-1.05)
    cam=UsdGeom.Camera.Define(stage,CAMERA)
    view=Gf.Matrix4d();view.SetLookAt(eye,target,Gf.Vec3d(0,0,1))
    cam.AddTransformOp().Set(view.GetInverse())
    cam.CreateFocalLengthAttr(12.)
    cam.CreateHorizontalApertureAttr(20.955);cam.CreateVerticalApertureAttr(20.955)
    cam.CreateClippingRangeAttr(Gf.Vec2f(.02,20.))
    return CAMERA

def open_view():
    from omni.kit.viewport.utility import create_viewport_window
    window=create_viewport_window('Robot Camera',width=520,height=560)
    window.viewport_api.camera_path=CAMERA
    window.viewport_api.resolution=(512,512)
    return window
