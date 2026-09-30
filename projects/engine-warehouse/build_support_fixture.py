"""Build the approved visual-only three-pin fixture and engine preview."""
import os, sys, math, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'.venv/asset-tools'))
p=next(Path('C:/isaacsim/extscache').glob('omni.usd.libs-*'))
sys.path.insert(0,str(p)); dll=os.add_dll_directory(str(p/'bin'))
import numpy as np
from pxr import Usd,UsdGeom,UsdShade,UsdLux,Sdf,Gf
HERE=Path(__file__).resolve().parent
folder=ROOT/'external_assets/engines/caterham_duratec/usd'
engine_stage=Usd.Stage.Open(str(folder/'engine.usdc'))
b=UsdGeom.BBoxCache(Usd.TimeCode.Default(),['default','render']).ComputeWorldBound(engine_stage.GetDefaultPrim()).ComputeAlignedRange()
center=b.GetMidpoint(); offset=np.array([-center[0],-center[1],.15-b.GetMin()[2]])
tri=[]
for prim in engine_stage.Traverse():
 if prim.IsA(UsdGeom.Mesh):
  m=UsdGeom.Mesh(prim);v=np.array(m.GetPointsAttr().Get())+offset
  tri.append(v[np.array(m.GetFaceVertexIndicesAttr().Get()).reshape(-1,3)])
tri=np.concatenate(tri)
def surface_z(x,y):
 a=tri[:,0];u=tri[:,1]-a;v=tri[:,2]-a
 den=u[:,0]*v[:,1]-u[:,1]*v[:,0]
 valid=abs(den)>1e-12;safe=np.where(valid,den,1)
 px=x-a[:,0];py=y-a[:,1]
 s=(px*v[:,1]-py*v[:,0])/safe;t=(u[:,0]*py-u[:,1]*px)/safe
 hit=valid&(s>=0)&(t>=0)&(s+t<=1)
 assert hit.any(),(x,y)
 return float((a[:,2]+s*u[:,2]+t*v[:,2])[hit].min())
fixture=Usd.Stage.CreateNew(str(HERE/'assets/three_pin_fixture.usda'))
UsdGeom.SetStageMetersPerUnit(fixture,1);UsdGeom.SetStageUpAxis(fixture,'Z')
fixture.SetDefaultPrim(UsdGeom.Xform.Define(fixture,'/Fixture').GetPrim())
for group in ['Columns','Receivers']:UsdGeom.Xform.Define(fixture,'/Fixture/'+group)
def material(name,color):
 mat=UsdShade.Material.Define(fixture,'/Fixture/'+name)
 sh=UsdShade.Shader.Define(fixture,'/Fixture/'+name+'/Surface');sh.CreateIdAttr('UsdPreviewSurface')
 sh.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color))
 sh.CreateInput('metallic',Sdf.ValueTypeNames.Float).Set(.7)
 sh.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(.3)
 mat.CreateSurfaceOutput().ConnectToSource(sh.CreateOutput('surface',Sdf.ValueTypeNames.Token));return mat
steel=material('Steel',(.35,.4,.46));adapter=material('Adapter',(.36,.22,.08))
def revolve(path,x,y,profile,mat):
 n=64;points=[];rings=[]
 for r,z in profile:
  if r==0:
   rings.append([len(points)]*n);points.append((x,y,z))
  else:
   rings.append(list(range(len(points),len(points)+n)))
   points.extend((x+r*math.cos(i*2*math.pi/n),y+r*math.sin(i*2*math.pi/n),z) for i in range(n))
 faces=[]
 for k in range(len(profile)):
  q=(k+1)%len(profile)
  for i in range(n):
   j=(i+1)%n;face=list(dict.fromkeys([rings[k][i],rings[k][j],rings[q][j],rings[q][i]]))
   if len(face)>=3:faces.append(face)
 mesh=UsdGeom.Mesh.Define(fixture,path);mesh.CreatePointsAttr(points)
 mesh.CreateFaceVertexCountsAttr([len(f) for f in faces]);mesh.CreateFaceVertexIndicesAttr([i for f in faces for i in f]);mesh.CreateSubdivisionSchemeAttr('none')
 UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(mat)
report=[]
for name,x,y in [('A',-.22,.1),('B',-.22,-.1),('C',.18,0)]:
 # Solid axis, stepped shoulder and a 5 mm taper at the pin tip.
 revolve('/Fixture/Columns/'+name,x,y,[(0,.02),(.025,.02),(.025,.12),(.008,.12),(.008,.135),(.004,.14),(0,.14)],steel)
 # Blind hole: radius 9mm, mouth at .120, ceiling .145; no solid overlaps the pin.
 z=surface_z(x,y);top=z+.003
 revolve('/Fixture/Receivers/'+name,x,y,[(.009,.12),(.032,.12),(.032,top),(0,top),(0,.145),(.009,.145)],adapter)
 report.append(dict(name=name,x_m=x,y_m=y,engine_surface_z_m=z,adapter_top_z_m=top))
fixture.GetRootLayer().Save()
stage=Usd.Stage.CreateNew(str(folder/'engine_supported_preview.usda'))
UsdGeom.SetStageMetersPerUnit(stage,1);UsdGeom.SetStageUpAxis(stage,'Z')
stage.SetDefaultPrim(UsdGeom.Xform.Define(stage,'/World').GetPrim())
def reference(path,file,prim=None):
 obj=UsdGeom.Xform.Define(stage,path)
 if prim:obj.GetPrim().GetReferences().AddReference(str(file),prim)
 else:obj.GetPrim().GetReferences().AddReference(str(file))
 return obj
reference('/World/InlinePallet',HERE/'assets/inline_pallet.usda')
reference('/World/Fixture',HERE/'assets/three_pin_fixture.usda')
reference('/World/Engine',folder/'engine.usdc').AddTranslateOp().Set(Gf.Vec3d(*offset))
light=UsdLux.DomeLight.Define(stage,'/World/Light');light.CreateIntensityAttr(900)
cam=UsdGeom.Camera.Define(stage,'/World/PreviewCamera');cam.CreateClippingRangeAttr(Gf.Vec2f(.01,100));cam.CreateFocalLengthAttr(40)
cam.AddTransformOp().Set(Gf.Matrix4d().SetLookAt(Gf.Vec3d(1.2,-1.5,.9),Gf.Vec3d(0,0,.27),Gf.Vec3d(0,0,1)).GetInverse())
stage.GetRootLayer().Save()
(folder/'support-report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2));print('SCENE:',folder/'engine_supported_preview.usda')
