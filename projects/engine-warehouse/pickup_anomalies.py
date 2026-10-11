"""Observation-only pickup cases. Never import this truth into a pose estimator."""
from pathlib import Path
from pxr import Usd, UsdGeom, Gf

ROOT=Path(__file__).resolve().parents[2]
FOLDER=ROOT/'external_assets/engines/caterham_duratec/usd'
OUTPUT=FOLDER/'pickup_anomaly_preview.usda'
CAMERA='/World/PickupCamera'
# Metres/degrees: experimental perturbations, not robot correction limits.
CASES={
    'normal':(0.,0.,0.,False),
    'stop_x':(.03,0.,0.,False),
    'lateral_y':(0.,.015,0.,False),
    'yaw':(0.,0.,2.,False),
    'occluded':(0.,0.,0.,True),
    'x_y':(.03,.015,0.,False),
    'x_yaw':(.03,0.,2.,False),
    'y_yaw':(0.,.015,2.,False),
    'x_y_yaw':(.03,.015,2.,False),
    'combined_occluded':(.03,.015,2.,True),
}

def build():
    s=Usd.Stage.CreateNew(str(OUTPUT)) if not OUTPUT.exists() else Usd.Stage.Open(str(OUTPUT))
    s.GetRootLayer().Clear()
    world=UsdGeom.Xform.Define(s,'/World');s.SetDefaultPrim(world.GetPrim())
    world.GetPrim().GetReferences().AddReference(str(FOLDER/'warehouse_multi_layout.usda'))
    # Do not let the warehouse extension attach its scheduler to this test stage.
    from pxr import Sdf
    world.GetPrim().CreateAttribute('demo:multiEngine',Sdf.ValueTypeNames.Bool).Set(False)
    for path in ('InlineLoad','CarriedEngine'):
        s.OverridePrim('/World/'+path).SetActive(False)
    UsdGeom.SetStageUpAxis(s,'Z');UsdGeom.SetStageMetersPerUnit(s,1.)
    load=UsdGeom.Xform.Define(s,'/World/TestLoad')
    load.GetPrim().GetReferences().AddReference(str(FOLDER/'engine_supported_preview.usda'))
    for name in ('Light','PreviewCamera'):
        s.OverridePrim('/World/TestLoad/'+name).SetActive(False)
    load.ClearXformOpOrder();load.AddTranslateOp();load.AddRotateZOp()
    cam=UsdGeom.Camera.Define(s,CAMERA)
    cam.AddTranslateOp().Set(Gf.Vec3d(0,-2.2,3.2))
    cam.CreateFocalLengthAttr(24.)
    cam.CreateHorizontalApertureAttr(20.955)
    cam.CreateVerticalApertureAttr(20.955)
    cam.CreateClippingRangeAttr(Gf.Vec2f(.05,20.))
    s.SetStartTimeCode(0);s.SetEndTimeCode(86400)
    from wrist_camera import attach
    attach(s)
    apply_case(s,'normal');s.GetRootLayer().Save()
    return OUTPUT

def apply_case(stage,name):
    x,y,yaw,masked=CASES[name]
    p=stage.GetPrimAtPath('/World/TestLoad')
    if not p:raise RuntimeError('Load pickup anomaly scene first')
    p.GetAttribute('xformOp:translate').Set(Gf.Vec3d(x,-2.2+y,.7))
    p.GetAttribute('xformOp:rotateZ').Set(yaw)
    return dict(dx_m=x,dy_m=y,yaw_deg=yaw,observation_mask=masked)

def mask_observation(rgb,depth,enabled):
    rgb=rgb.copy();depth=depth.copy()
    if enabled:
        h,w=depth.shape[:2]
        rgb[h//4:3*h//4,w//2:3*w//4,:3]=0
        depth[h//4:3*h//4,w//2:3*w//4]=float('nan')
    return rgb,depth
