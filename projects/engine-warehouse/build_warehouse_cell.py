"""Static direct-engine storage cell: conveyor, FANUC 210L, jig and padded rack."""
import os,sys
from pathlib import Path
p=next(Path('C:/isaacsim/extscache').glob('omni.usd.libs-*'));sys.path.insert(0,str(p));dll=os.add_dll_directory(str(p/'bin'))
from pxr import Usd,UsdGeom,UsdShade,UsdLux,Sdf,Gf
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];folder=ROOT/'external_assets/engines/caterham_duratec/usd'
s=Usd.Stage.CreateNew(str(folder/'warehouse_cell_preview.usda'));UsdGeom.SetStageMetersPerUnit(s,1);UsdGeom.SetStageUpAxis(s,'Z');s.SetDefaultPrim(UsdGeom.Xform.Define(s,'/World').GetPrim())
def ref(path,file,xyz=(0,0,0)):
 o=UsdGeom.Xform.Define(s,path);o.GetPrim().GetReferences().AddReference(str(file));o.AddTranslateOp().Set(Gf.Vec3d(*xyz));return o
ref('/World/Line',folder/'inlet_conveyor_preview.usda')
for name in ['Light','PreviewCamera']:s.OverridePrim('/World/Line/'+name).SetActive(False)
load=UsdGeom.Xformable(s.GetPrimAtPath('/World/Line/InspectionLoad'))
next(op for op in load.GetOrderedXformOps() if op.GetOpType()==UsdGeom.XformOp.TypeTranslate).Set(Gf.Vec3d(1.8,0,.7))
# Approved 300 mm move away from the conveyor for the cell approach workspace.
ref('/World/FANUC_210L',ROOT/'external_assets/robots/fanuc_r2000ic_210l/robot.usdc',(2.1,2.2,0)).AddRotateZOp().Set(-90)
# Empty-hand idle pose: turn away from conveyor and retract the shoulder.
UsdGeom.Xformable(s.GetPrimAtPath('/World/FANUC_210L/Base/J1')).AddRotateZOp().Set(180)
UsdGeom.Xformable(s.GetPrimAtPath('/World/FANUC_210L/Base/J1/J2')).AddRotateYOp().Set(-20)
UsdGeom.Xformable(s.GetPrimAtPath('/World/FANUC_210L/Base/J1/J2/J3')).AddRotateYOp().Set(35)
ref('/World/FANUC_210L/Base/J1/J2/J3/J4/J5/J6/EngineJig',HERE/'assets/engine_jig.usda',(.24,0,0))
def mat(name,color,metal=0):
 m=UsdShade.Material.Define(s,'/World/Looks/'+name);sh=UsdShade.Shader.Define(s,str(m.GetPath())+'/Surface');sh.CreateIdAttr('UsdPreviewSurface');sh.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color));sh.CreateInput('metallic',Sdf.ValueTypeNames.Float).Set(metal);sh.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(.4);m.CreateSurfaceOutput().ConnectToSource(sh.CreateOutput('surface',Sdf.ValueTypeNames.Token));return m
blue=mat('Frame',(.055,.15,.26),.5);steel=mat('Steel',(.48,.52,.57),.8);orange=mat('RackBeam',(.95,.3,.04),.3);yellow=mat('Guide',(.9,.55,.06),.3)
def box(path,pos,size,material):
 o=UsdGeom.Cube.Define(s,'/World/'+path);o.CreateSizeAttr(1);o.AddTranslateOp().Set(Gf.Vec3d(*pos));o.AddScaleOp().Set(Gf.Vec3f(*size));UsdShade.MaterialBindingAPI.Apply(o.GetPrim()).Bind(material)
for i in range(12):
 o=UsdGeom.Cylinder.Define(s,f'/World/Extension/Roller_{i}');o.CreateAxisAttr('Y');o.CreateRadiusAttr(.03);o.CreateHeightAttr(.9);o.AddTranslateOp().Set(Gf.Vec3d(1.25+i*.1,0,.67));UsdShade.MaterialBindingAPI.Apply(o.GetPrim()).Bind(steel)
for j,y in enumerate([-.49,.49]):
 box(f'Extension/Frame_{j}',(1.8,y,.62),(1.2,.08,.12),blue);box(f'Extension/Guide_{j}',(1.8,y,.745),(1.2,.025,.06),yellow)
 box(f'Extension/Leg_{j}',(2.25,y,.29),(.08,.08,.58),blue)
# Rack opens toward -X; two columns along Y, two levels along Z.
for i,x in enumerate([3.7,4.8]):
 for j,y in enumerate([.6,1.8,3.]):box(f'Rack/Post_{i}_{j}',(x,y,1.35),(.08,.08,2.7),blue)
for level,z in enumerate([.65,1.65]):
 for col,y in enumerate([1.2,2.4]):
  for side,yy in enumerate([y-.54,y+.54]):box(f'Rack/Beam_{level}_{col}_{side}',(4.25,yy,z-.055),(1.1,.08,.11),orange)
  box(f'Rack/Cell_{level}_{col}',(4.25,y,z-.015),(1.02,1.02,.03),steel)
  ref(f'/World/Rack/Cradle_{level}_{col}',HERE/'assets/engine_cell_cradle.usda',(4.25,y,z))
# Direct engine storage supersedes external-pallet transfer; no transfer table.
light=UsdLux.DomeLight.Define(s,'/World/Light');light.CreateIntensityAttr(900)
cam=UsdGeom.Camera.Define(s,'/World/PreviewCamera');cam.CreateClippingRangeAttr(Gf.Vec2f(.01,100));cam.CreateFocalLengthAttr(35);cam.AddTransformOp().Set(Gf.Matrix4d().SetLookAt(Gf.Vec3d(9,-9,7),Gf.Vec3d(1.8,1.5,1.),Gf.Vec3d(0,0,1)).GetInverse())
s.GetRootLayer().Save()
assert sum(p.IsA(UsdGeom.Cylinder) for p in s.Traverse() if '/Extension/' in str(p.GetPath()))==12
assert all(s.GetPrimAtPath(f'/World/Rack/Cell_{i}_{j}') for i in range(2) for j in range(2))
assert s.GetPrimAtPath('/World/FANUC_210L/Base/J1/J2/J3/J4/J5/J6')
print('PASS: 36 main rollers, 4 rack cells, 7 robot links composed')
print(folder/'warehouse_cell_preview.usda')
