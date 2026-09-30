"""Static inlet roller conveyor with a one-pallet lateral rework buffer."""
import os,sys
from pathlib import Path
p=next(Path('C:/isaacsim/extscache').glob('omni.usd.libs-*'));sys.path.insert(0,str(p));dll=os.add_dll_directory(str(p/'bin'))
from pxr import Usd,UsdGeom,UsdShade,UsdLux,Gf,Sdf
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
asset=HERE/'assets/inlet_conveyor.usda'
s=Usd.Stage.CreateNew(str(asset));UsdGeom.SetStageMetersPerUnit(s,1);UsdGeom.SetStageUpAxis(s,'Z')
s.SetDefaultPrim(UsdGeom.Xform.Define(s,'/Conveyor').GetPrim())
def mat(name,color,metal=0):
 m=UsdShade.Material.Define(s,'/Conveyor/Looks/'+name);sh=UsdShade.Shader.Define(s,str(m.GetPath())+'/Surface');sh.CreateIdAttr('UsdPreviewSurface')
 sh.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color));sh.CreateInput('metallic',Sdf.ValueTypeNames.Float).Set(metal);sh.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(.4)
 m.CreateSurfaceOutput().ConnectToSource(sh.CreateOutput('surface',Sdf.ValueTypeNames.Token));return m
steel=mat('Roller',(.48,.52,.57),.8);blue=mat('Frame',(.055,.15,.26),.5);dark=mat('Transfer',(.045,.045,.05));yellow=mat('Guide',(.9,.55,.06),.3)
def cube(path,pos,size,material):
 o=UsdGeom.Cube.Define(s,'/Conveyor/'+path);o.CreateSizeAttr(1);o.AddTranslateOp().Set(Gf.Vec3d(*pos));o.AddScaleOp().Set(Gf.Vec3f(*size));UsdShade.MaterialBindingAPI.Apply(o.GetPrim()).Bind(material)
for i in range(24):
 o=UsdGeom.Cylinder.Define(s,f'/Conveyor/Main/Roller_{i:02}');o.CreateAxisAttr('Y');o.CreateRadiusAttr(.03);o.CreateHeightAttr(.9);o.AddTranslateOp().Set(Gf.Vec3d(-1.15+i*.1,0,.67));UsdShade.MaterialBindingAPI.Apply(o.GetPrim()).Bind(steel)
# Opening at the inspection station allows lateral transfer without crossing a rail.
cube('Main/FrameSouth',(0,-.49,.62),(2.4,.08,.12),blue)
for label,x in [('West',-.86),('East',.86)]:
 cube('Main/FrameNorth'+label,(x,.49,.62),(.68,.08,.12),blue)
 cube('Main/GuideNorth'+label,(x,.46,.745),(.68,.025,.06),yellow)
cube('Main/GuideSouth',(0,-.46,.745),(2.4,.025,.06),yellow)
for x in [-1.,1.]:
 for y in [-.49,.49]:cube('Main/Leg_'+str(x).replace('-','n').replace('.','_')+'_'+str(y).replace('-','n').replace('.','_'),(x,y,.29),(.08,.08,.58),blue)
for i in range(11):
 o=UsdGeom.Cylinder.Define(s,f'/Conveyor/Buffer/Roller_{i:02}');o.CreateAxisAttr('X');o.CreateRadiusAttr(.03);o.CreateHeightAttr(.9);o.AddTranslateOp().Set(Gf.Vec3d(0,.6+i*.1,.67));UsdShade.MaterialBindingAPI.Apply(o.GetPrim()).Bind(steel)
for label,x in [('Left',-.49),('Right',.49)]:
 cube('Buffer/Frame'+label,(x,1.1,.62),(.08,1.16,.12),blue)
 cube('Buffer/Guide'+label,(x,1.1,.745),(.025,1.16,.06),yellow)
 for suffix,y in [('Near',.68),('Far',1.5)]:cube('Buffer/Leg'+label+suffix,(x,y,.29),(.08,.08,.58),blue)
cube('Buffer/EndStop',(0,1.68,.75),(.9,.04,.08),yellow)
# Lowered transfer strips are only a schematic lift-transfer mechanism, not driven belts.
for i,x in enumerate([-.3,0,.3]):cube(f'Transfer/LoweredStrip_{i}',(x,.76,.645),(.045,1.58,.035),dark)
s.GetDefaultPrim().SetCustomDataByKey('scope','Static layout only; no vision, motion, collision or mass. Transfer strips shown lowered.')
s.GetRootLayer().Save()
folder=ROOT/'external_assets/engines/caterham_duratec/usd'
scene=Usd.Stage.CreateNew(str(folder/'inlet_conveyor_preview.usda'));UsdGeom.SetStageMetersPerUnit(scene,1);UsdGeom.SetStageUpAxis(scene,'Z');scene.SetDefaultPrim(UsdGeom.Xform.Define(scene,'/World').GetPrim())
UsdGeom.Xform.Define(scene,'/World/Conveyor').GetPrim().GetReferences().AddReference(str(asset))
assembly=UsdGeom.Xform.Define(scene,'/World/InspectionLoad');assembly.GetPrim().GetReferences().AddReference(str(folder/'engine_supported_preview.usda'));assembly.AddTranslateOp().Set(Gf.Vec3d(0,0,.7))
for child in ['Light','PreviewCamera']:scene.OverridePrim('/World/InspectionLoad/'+child).SetActive(False)
light=UsdLux.DomeLight.Define(scene,'/World/Light');light.CreateIntensityAttr(900)
cam=UsdGeom.Camera.Define(scene,'/World/PreviewCamera');cam.CreateClippingRangeAttr(Gf.Vec2f(.01,100));cam.CreateFocalLengthAttr(35);cam.AddTransformOp().Set(Gf.Matrix4d().SetLookAt(Gf.Vec3d(3.4,-3.8,3),Gf.Vec3d(0,.45,.65),Gf.Vec3d(0,0,1)).GetInverse())
scene.GetRootLayer().Save()
assert sum(p.IsA(UsdGeom.Cylinder) for p in s.Traverse())==35
box=UsdGeom.BBoxCache(Usd.TimeCode.Default(),['default']).ComputeWorldBound(scene.GetPrimAtPath('/World/InspectionLoad/InlinePallet')).ComputeAlignedRange()
assert abs(box.GetMin()[2]-.7)<1e-6
print('PASS: 24 main rollers, 11 buffer rollers; pallet bottom at roller top Z=0.700m')
print(folder/'inlet_conveyor_preview.usda')
