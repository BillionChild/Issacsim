"""Visual-only custom engine jig and rubber-pad rack cradle. Units: metres."""
import os,sys
from pathlib import Path
p=next(Path('C:/isaacsim/extscache').glob('omni.usd.libs-*'));sys.path.insert(0,str(p));dll=os.add_dll_directory(str(p/'bin'))
from pxr import Usd,UsdGeom,UsdShade,UsdLux,Sdf,Gf
HERE=Path(__file__).resolve().parent

def new_stage(filename,root):
 s=Usd.Stage.CreateNew(str(HERE/'assets'/filename));UsdGeom.SetStageMetersPerUnit(s,1);UsdGeom.SetStageUpAxis(s,'Z');s.SetDefaultPrim(UsdGeom.Xform.Define(s,root).GetPrim());return s

def material(s,root,name,color,metal=0):
 m=UsdShade.Material.Define(s,root+'/Looks/'+name);sh=UsdShade.Shader.Define(s,str(m.GetPath())+'/Surface');sh.CreateIdAttr('UsdPreviewSurface');sh.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color));sh.CreateInput('metallic',Sdf.ValueTypeNames.Float).Set(metal);sh.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(.65 if metal==0 else .35);m.CreateSurfaceOutput().ConnectToSource(sh.CreateOutput('surface',Sdf.ValueTypeNames.Token));return m

def box(s,path,pos,size,mat):
 o=UsdGeom.Cube.Define(s,path);o.CreateSizeAttr(1);o.AddTranslateOp().Set(Gf.Vec3d(*pos));o.AddScaleOp().Set(Gf.Vec3f(*size));UsdShade.MaterialBindingAPI.Apply(o.GetPrim()).Bind(mat)

def cylinder(s,path,pos,radius,length,axis,mat):
 o=UsdGeom.Cylinder.Define(s,path);o.CreateAxisAttr(axis);o.CreateRadiusAttr(radius);o.CreateHeightAttr(length);o.AddTranslateOp().Set(Gf.Vec3d(*pos));UsdShade.MaterialBindingAPI.Apply(o.GetPrim()).Bind(mat)

s=new_stage('engine_jig.usda','/EngineJig')
metal=material(s,'/EngineJig','Metal',(.28,.34,.42),.7);rubber=material(s,'/EngineJig','Rubber',(.025,.03,.035));pin=material(s,'/EngineJig','Locator',(.9,.58,.08),.65)
# Local origin is the wrist flange; +X approaches engine, +Z stays upright.
cylinder(s,'/EngineJig/WristAdapter',(.025,0,0),.115,.05,'X',metal)
box(s,'/EngineJig/Backbone',(.08,0,-.21),(.06,.12,.46),metal)
box(s,'/EngineJig/TopCrossbar',(.1,0,0),(.08,.90,.08),metal)
for name,sign in [('Left',1),('Right',-1)]:
 root='/EngineJig/'+name
 UsdGeom.Xform.Define(s,root).AddTranslateOp().Set(Gf.Vec3d(0,sign*.12,0))
 box(s,root+'/TopArm',(.39,sign*.255,0),(.66,.08,.08),metal)
 box(s,root+'/SideArm',(.43,sign*.255,-.27),(.12,.08,.54),metal)
 box(s,root+'/LowerFinger',(.43,sign*.215,-.535),(.30,.12,.04),metal)
 box(s,root+'/SupportPad',(.43,sign*.195,-.5075),(.24,.08,.015),rubber)
box(s,'/EngineJig/LocatorPlate',(.105,0,-.28),(.035,.34,.18),metal)
for name,y in [('A',-.12),('B',.12)]:
 cylinder(s,'/EngineJig/LocatorPin'+name,(.145,y,-.28),.008,.045,'X',pin)
s.GetDefaultPrim().SetCustomDataByKey('scope','Custom concept, not a FANUC catalogue gripper. Placeholder locator positions, default open pose, 120mm travel per jaw; no verified engine hole fit.')
s.GetRootLayer().Save()

c=new_stage('engine_cell_cradle.usda','/Cradle')
steel=material(c,'/Cradle','Steel',(.20,.27,.34),.6);pad=material(c,'/Cradle','Rubber',(.025,.03,.035))
# Narrow central support rails leave side lanes for the gripper fingers.
for name,y in [('Left',.085),('Right',-.085)]:
 box(c,'/Cradle/'+name+'/Pedestal',(0,y,.055),(.50,.08,.11),steel)
 box(c,'/Cradle/'+name+'/RubberPad',(0,y,.12),(.46,.09,.02),pad)
c.GetDefaultPrim().SetCustomDataByKey('scope','Generic rubber-pad visual cradle, not a verified sump contact contour. Finger lanes remain clear in nominal aligned layout.')
c.GetRootLayer().Save()
# Detail preview displays the two components separately for design review.
root=HERE.parents[1];out=root/'external_assets/engines/caterham_duratec/usd/jig_detail_preview.usda'
v=Usd.Stage.CreateNew(str(out));UsdGeom.SetStageMetersPerUnit(v,1);UsdGeom.SetStageUpAxis(v,'Z');v.SetDefaultPrim(UsdGeom.Xform.Define(v,'/World').GetPrim())
g=UsdGeom.Xform.Define(v,'/World/Gripper');g.GetPrim().GetReferences().AddReference(str(HERE/'assets/engine_jig.usda'));g.AddTranslateOp().Set(Gf.Vec3d(-.43,-.60,.8))
r=UsdGeom.Xform.Define(v,'/World/Cradle');r.GetPrim().GetReferences().AddReference(str(HERE/'assets/engine_cell_cradle.usda'));r.AddTranslateOp().Set(Gf.Vec3d(0,.65,0))
light=UsdLux.DomeLight.Define(v,'/World/Light');light.CreateIntensityAttr(1000)
cam=UsdGeom.Camera.Define(v,'/World/PreviewCamera');cam.CreateFocalLengthAttr(40);cam.CreateClippingRangeAttr(Gf.Vec2f(.01,100));cam.AddTransformOp().Set(Gf.Matrix4d().SetLookAt(Gf.Vec3d(2.4,-2.8,2.),Gf.Vec3d(0,0,.35),Gf.Vec3d(0,0,1)).GetInverse());v.GetRootLayer().Save()
print('Built engine_jig.usda, engine_cell_cradle.usda, detail preview')
