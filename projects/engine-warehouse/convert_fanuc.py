"""Convert official FANUC R-2000iC/210L visual meshes into a static link hierarchy."""
import os,sys,json,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.venv/asset-tools'))
p=next(Path('C:/isaacsim/extscache').glob('omni.usd.libs-*'));sys.path.insert(0,str(p));dll=os.add_dll_directory(str(p/'bin'))
import collada,numpy as np
from pxr import Usd,UsdGeom,UsdShade,Sdf,Gf,Vt
folder=ROOT/'external_assets/robots/fanuc_r2000ic_210l'
s=Usd.Stage.CreateNew(str(folder/'robot.usdc'));UsdGeom.SetStageMetersPerUnit(s,1);UsdGeom.SetStageUpAxis(s,'Z');s.SetDefaultPrim(UsdGeom.Xform.Define(s,'/Robot').GetPrim())
xml=ET.parse(folder/'robot.xacro');joints={j.attrib['name'].replace('${prefix}',''):j for j in xml.iter('joint')}
path='/Robot/Base';triangles=0
for i,name in enumerate(['base','j1','j2','j3','j4','j5','j6']):
 if i:path+=f'/J{i}'
 xf=UsdGeom.Xform.Define(s,path)
 if i:
  j=joints[f'J{i}'];xyz=[float(v) for v in j.find('origin').attrib['xyz'].split()]
  assert j.find('origin').attrib['rpy']=='0 0 0'
  xf.AddTranslateOp().Set(Gf.Vec3d(*xyz));xf.GetPrim().SetCustomDataByKey('jointAxis',j.find('axis').attrib['xyz'])
 m=collada.Collada(str(folder/(name+'.dae')));assert m.assetInfo.unitmeter==1 and m.assetInfo.upaxis=='Z_UP'
 k=0
 for geo in m.scene.objects('geometry'):
  for prim in geo.primitives():
   assert isinstance(prim,collada.triangleset.BoundTriangleSet)
   mesh=UsdGeom.Mesh.Define(s,path+f'/Mesh_{k}')
   mesh.CreatePointsAttr(Vt.Vec3fArray.FromNumpy(np.asarray(prim.vertex,dtype=np.float32)))
   indices=prim.vertex_index;mesh.CreateFaceVertexCountsAttr([3]*len(indices));mesh.CreateFaceVertexIndicesAttr(indices.reshape(-1).tolist());mesh.CreateSubdivisionSchemeAttr('none')
   if prim.original.normal is not None:
    normals=prim.original.normal[prim.normal_index].reshape(-1,3)@np.linalg.inv(geo.matrix[:3,:3]);normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12)
    mesh.CreateNormalsAttr(Vt.Vec3fArray.FromNumpy(normals.astype(np.float32)));mesh.SetNormalsInterpolation('faceVarying')
   color=prim.material.effect.diffuse if prim.material else (.5,.5,.5,1)
   assert isinstance(color,tuple)
   mat=UsdShade.Material.Define(s,path+f'/Material_{k}');sh=UsdShade.Shader.Define(s,str(mat.GetPath())+'/Surface');sh.CreateIdAttr('UsdPreviewSurface');sh.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color[:3]));sh.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(.38);mat.CreateSurfaceOutput().ConnectToSource(sh.CreateOutput('surface',Sdf.ValueTypeNames.Token));UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(mat)
   triangles+=len(indices);k+=1
s.GetDefaultPrim().SetCustomDataByKey('scope','Static visual links at URDF zero pose; no articulation, masses or drives.')
s.GetRootLayer().Save();assert len(list(s.GetPrimAtPath('/Robot/Base').GetChildren()))>0
print('Converted 7 links, triangles:',triangles)
