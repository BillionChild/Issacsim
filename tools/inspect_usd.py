"""Concise, read-only USD inventory. Never prints geometry arrays."""
import argparse,json,os,sys
from pathlib import Path

def inspect(path,root='/'):
    from pxr import Usd,UsdGeom,UsdShade,UsdPhysics
    stage=Usd.Stage.Open(str(path))
    if not stage:raise ValueError('Cannot open stage')
    prim=stage.GetPrimAtPath(root)
    if not prim:raise ValueError('Missing subtree: '+root)
    counts=dict(prims=0,meshes=0,points=0,faces=0,triangles_estimate=0,rigid_bodies=0,colliders=0,articulations=0,joints=0)
    materials={};largest=[]
    for p in Usd.PrimRange(prim):
        counts['prims']+=1
        for key,api in [('rigid_bodies',UsdPhysics.RigidBodyAPI),('colliders',UsdPhysics.CollisionAPI),('articulations',UsdPhysics.ArticulationRootAPI)]:
            counts[key]+=int(p.HasAPI(api))
        counts['joints']+=int(p.IsA(UsdPhysics.Joint))
        if not p.IsA(UsdGeom.Mesh):continue
        m=UsdGeom.Mesh(p);faces=m.GetFaceVertexCountsAttr().Get()
        faces=[] if faces is None else faces
        points=m.GetPointsAttr().Get();n=sum(max(0,int(v)-2) for v in faces)
        counts['meshes']+=1;counts['points']+=len(points) if points is not None else 0
        counts['faces']+=len(faces);counts['triangles_estimate']+=n
        material,_=UsdShade.MaterialBindingAPI(p).ComputeBoundMaterial()
        key=str(material.GetPath()) if material else '(unbound)';materials[key]=materials.get(key,0)+1
        largest.append((n,str(p.GetPath())))
    cache=UsdGeom.BBoxCache(Usd.TimeCode.Default(),['default','render','proxy'])
    bounds=cache.ComputeWorldBound(prim).ComputeAlignedRange()
    return dict(file=str(path),bytes=path.stat().st_size,root=root,**counts,
                meters_per_unit=UsdGeom.GetStageMetersPerUnit(stage),up_axis=str(UsdGeom.GetStageUpAxis(stage)),
                world_size_stage_units=list(bounds.GetSize()),material_groups=len(materials),
                top_material_groups=sorted(materials.items(),key=lambda x:x[1],reverse=True)[:5],
                largest_meshes=sorted(largest,reverse=True)[:5],
                note='Default-time active composed prims; instance proxies excluded. Triangle estimate ignores holes. Not a render benchmark or reference validator.')

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('file',type=Path);a.add_argument('--root',default='/');a.add_argument('--out',type=Path);args=a.parse_args()
    try:import pxr
    except ImportError:
        lib=next(Path('C:/isaacsim/extscache').glob('omni.usd.libs-*'));sys.path.insert(0,str(lib));dll=os.add_dll_directory(str(lib/'bin'))
    result=inspect(args.file.resolve(),args.root);text=json.dumps(result,indent=2)
    if args.out:args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(text,encoding='utf-8')
    print(text)
