"""Replace only support pads; preserve original jig frame and rack geometry."""
import os,sys
from pathlib import Path
lib=next(Path('C:/isaacsim/extscache').glob('omni.usd.libs-*'))
sys.path.insert(0,str(lib));dll=os.add_dll_directory(str(lib/'bin'))
from pxr import Usd
from pxr import UsdGeom,UsdShade,Gf
from support_contact import ROOT,SITES,engine_triangles,underside,np
import json

tri=engine_triangles();path=ROOT/'projects/engine-warehouse/assets/engine_jig.usda'
stage=Usd.Stage.Open(str(path));report=[]
for side,cx,cy,hx,hy in SITES:
    root='/EngineJig/'+side
    stage.RemovePrim(root+'/SupportPad')
    for name in ('SupportBridge','SupportRiser','SupportStem'):stage.RemovePrim(root+'/'+name)
    # Tool-local conversion: engine center = (.43,0,-.65), Rz(180).
    xs=np.linspace(cx-hx,cx+hx,17);ys=np.linspace(cy-hy,cy+hy,11)
    upper=np.array([[.43-x,-y,underside(tri,x,y)-.65] for y in ys for x in xs])
    lower=upper.copy();lower[:,2]-=.008
    def mesh(name,top,bottom,material):
        obj=UsdGeom.Mesh.Define(stage,root+'/'+name);n=len(top);points=np.r_[top,bottom];faces=[]
        for j in range(len(ys)-1):
            for i in range(len(xs)-1):
                k=j*len(xs)+i;faces.extend([[k,k+1,k+len(xs)+1],[k,k+len(xs)+1,k+len(xs)]])
                faces.extend([[n+k,n+k+len(xs)+1,n+k+1],[n+k,n+k+len(xs),n+k+len(xs)+1]])
        edge=list(range(len(xs)))+[j*len(xs)+len(xs)-1 for j in range(1,len(ys))]+list(range(n-2,n-len(xs)-1,-1))+[j*len(xs) for j in range(len(ys)-2,0,-1)]
        for a,b in zip(edge,edge[1:]+edge[:1]):faces.extend([[a,n+a,n+b],[a,n+b,b]])
        obj.CreatePointsAttr([Gf.Vec3f(*p) for p in points]);obj.CreateFaceVertexCountsAttr([3]*len(faces));obj.CreateFaceVertexIndicesAttr(np.asarray(faces).ravel().tolist());obj.CreateSubdivisionSchemeAttr('none')
        UsdShade.MaterialBindingAPI.Apply(obj.GetPrim()).Bind(UsdShade.Material(stage.GetPrimAtPath('/EngineJig/Looks/'+material)))
    mesh('SupportPad',upper,lower,'Rubber')
    bottom=lower.copy();bottom[:,2]=-.48 if side=='Right' else -.515
    assert np.all(lower[:,2]>bottom[:,2])
    mesh('SupportRiser',lower,bottom,'Metal')
    # Right bridge is raised above the rack pad; an outer stem joins the original finger.
    y0=-cy;outer=.215 if y0>0 else -.215
    cube=UsdGeom.Cube.Define(stage,root+'/SupportBridge');cube.CreateSizeAttr(1.)
    cube.AddTranslateOp().Set(Gf.Vec3d(.43-cx,(y0+outer)/2,-.49 if side=='Right' else -.535))
    cube.AddScaleOp().Set(Gf.Vec3f(.04,abs(outer-y0)+2*hy,.02 if side=='Right' else .04))
    UsdShade.MaterialBindingAPI.Apply(cube.GetPrim()).Bind(UsdShade.Material(stage.GetPrimAtPath('/EngineJig/Looks/Metal')))
    if side=='Right':
        stem=UsdGeom.Cube.Define(stage,root+'/SupportStem');stem.CreateSizeAttr(1.)
        stem.AddTranslateOp().Set(Gf.Vec3d(.43-cx,outer,-.4975));stem.AddScaleOp().Set(Gf.Vec3f(.04,.02,.035))
        UsdShade.MaterialBindingAPI.Apply(stem.GetPrim()).Bind(UsdShade.Material(stage.GetPrimAtPath('/EngineJig/Looks/Metal')))
    report.append(dict(side=side,center_engine_m=[cx,cy],contact_samples=len(upper),height_range_m=[float(upper[:,2].min()+.65),float(upper[:,2].max()+.65)]))
stage.GetRootLayer().Save()
(ROOT/'outputs/support-shoes.json').write_text(json.dumps(report,indent=2))
print('SUPPORT SHOES BUILT',report)
