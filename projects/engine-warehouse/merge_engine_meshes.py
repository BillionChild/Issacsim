"""Lossless material-group merge for this project's static converted engine only.
Offline pxr; no Kit startup. Original asset and active scene stay unchanged.
"""
import hashlib,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'.venv/asset-tools'))
lib=next(Path('C:/isaacsim/extscache').glob('omni.usd.libs-*'));sys.path.insert(0,str(lib));dll=os.add_dll_directory(str(lib/'bin'))
import numpy as np
from pxr import Usd,UsdGeom,UsdShade,Sdf,Vt,Gf
FOLDER=ROOT/'external_assets/engines/caterham_duratec/usd'

def merge():
    source=FOLDER/'engine.usdc';target=FOLDER/'engine_merged.usdc'
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    original=Usd.Stage.Open(str(source));groups={}
    allowed={'points','faceVertexCounts','faceVertexIndices','subdivisionScheme','doubleSided','normals','primvars:st','material:binding'}
    for p in original.Traverse():
        if not p.IsA(UsdGeom.Mesh):continue
        assert p.GetParent().GetPath()=='/Engine/Geometry', 'Only flat converted engine supported'
        assert set(x.GetName() for x in p.GetAuthoredProperties())<=allowed, 'Unexpected property; review before merging'
        assert not p.GetChildren() and not p.IsInstance(), 'Subsets/instances require a separate merge policy'
        assert all(not a.GetNumTimeSamples() for a in p.GetAttributes()), 'Animated geometry is not supported'
        assert UsdGeom.XformCache().GetLocalToWorldTransform(p)==Gf.Matrix4d(1), 'Unexpected transform'
        m=UsdGeom.Mesh(p);uv=UsdGeom.PrimvarsAPI(m).GetPrimvar('st');norm=m.GetNormalsAttr().Get()
        assert m.GetSubdivisionSchemeAttr().Get()=='none'
        assert norm is None or m.GetNormalsInterpolation()=='faceVarying'
        assert not uv or (uv.GetInterpolation()=='faceVarying' and not uv.IsIndexed())
        mat,_=UsdShade.MaterialBindingAPI(p).ComputeBoundMaterial()
        key=(str(mat.GetPath()),bool(uv),norm is not None,m.GetDoubleSidedAttr().Get(),str(m.GetOrientationAttr().Get()))
        groups.setdefault(key,[]).append(m)
    assert groups, 'No geometry found'
    original.GetRootLayer().Export(str(target));out=Usd.Stage.Open(str(target))
    for p in list(out.GetPrimAtPath('/Engine/Geometry').GetChildren()):out.RemovePrim(p.GetPath())
    mapping=[]
    for i,(key,meshes) in enumerate(groups.items()):
        path=f'/Engine/Geometry/Merged_{i:02d}'
        Sdf.CopySpec(original.GetRootLayer(),meshes[0].GetPath(),out.GetRootLayer(),path)
        merged=UsdGeom.Mesh(out.GetPrimAtPath(path));points=[];counts=[];indices=[];normals=[];uvs=[];offset=0;face_offset=0
        for m in meshes:
            pts=np.array(m.GetPointsAttr().Get());fc=np.array(m.GetFaceVertexCountsAttr().Get());ix=np.array(m.GetFaceVertexIndicesAttr().Get())
            assert np.all(fc==3) and np.all(ix>=0) and np.all(ix<len(pts))
            points.append(pts);counts.append(fc);indices.append(ix+offset)
            if key[2]:
                n=np.array(m.GetNormalsAttr().Get());assert len(n)==len(ix);normals.append(n)
            if key[1]:
                uv=np.array(UsdGeom.PrimvarsAPI(m).GetPrimvar('st').Get());assert len(uv)==len(ix);uvs.append(uv)
            mapping.append(dict(source=str(m.GetPath()),merged=path,point_start=offset,point_count=len(pts),face_start=face_offset,face_count=len(fc)))
            offset+=len(pts);face_offset+=len(fc)
        pts=np.concatenate(points)
        merged.GetPointsAttr().Set(Vt.Vec3fArray.FromNumpy(pts))
        merged.GetFaceVertexCountsAttr().Set(Vt.IntArray.FromNumpy(np.concatenate(counts).astype(np.int32)))
        merged.GetFaceVertexIndicesAttr().Set(Vt.IntArray.FromNumpy(np.concatenate(indices).astype(np.int32)))
        if key[2]:merged.GetNormalsAttr().Set(Vt.Vec3fArray.FromNumpy(np.concatenate(normals)))
        if key[1]:UsdGeom.PrimvarsAPI(merged).GetPrimvar('st').Set(Vt.Vec2fArray.FromNumpy(np.concatenate(uvs)))
        merged.CreateExtentAttr(Vt.Vec3fArray.FromNumpy(np.array([pts.min(axis=0),pts.max(axis=0)])))
    # Export a fresh crate: incremental saves can retain removed array blocks.
    packed=target.with_name('engine_merged_packed.usdc')
    out.GetRootLayer().Export(str(packed));out=None;merged=None
    os.replace(packed,target)
    reopened=Usd.Stage.Open(str(target))
    # Verify each original chunk, including face winding, exact normals and UVs.
    for row in mapping:
        a=UsdGeom.Mesh(original.GetPrimAtPath(row['source']));b=UsdGeom.Mesh(reopened.GetPrimAtPath(row['merged']))
        ps=row['point_start'];pe=ps+row['point_count'];fs=row['face_start'];fe=fs+row['face_count']
        assert np.array_equal(a.GetPointsAttr().Get(),np.array(b.GetPointsAttr().Get())[ps:pe])
        assert np.array_equal(a.GetFaceVertexCountsAttr().Get(),np.array(b.GetFaceVertexCountsAttr().Get())[fs:fe])
        assert np.array_equal(a.GetFaceVertexIndicesAttr().Get(),np.array(b.GetFaceVertexIndicesAttr().Get())[fs*3:fe*3]-ps)
        if a.GetNormalsAttr().Get() is not None:assert np.array_equal(a.GetNormalsAttr().Get(),np.array(b.GetNormalsAttr().Get())[fs*3:fe*3])
        uv=UsdGeom.PrimvarsAPI(a).GetPrimvar('st')
        if uv:assert np.array_equal(uv.Get(),np.array(UsdGeom.PrimvarsAPI(b).GetPrimvar('st').Get())[fs*3:fe*3])
        assert UsdShade.MaterialBindingAPI(a).ComputeBoundMaterial()[0].GetPath()==UsdShade.MaterialBindingAPI(b).ComputeBoundMaterial()[0].GetPath()
    for p in original.Traverse():
        if str(p.GetPath()).startswith('/Engine/Looks'):
            q=reopened.GetPrimAtPath(p.GetPath())
            for a in p.GetAttributes():
                assert a.Get()==q.GetAttribute(a.GetName()).Get()
                assert a.GetConnections()==q.GetAttribute(a.GetName()).GetConnections()
                if a.GetTypeName()==Sdf.ValueTypeNames.Asset and a.Get():assert q.GetAttribute(a.GetName()).Get().resolvedPath
    box=lambda s:UsdGeom.BBoxCache(Usd.TimeCode.Default(),['default','render']).ComputeWorldBound(s.GetDefaultPrim()).ComputeAlignedRange()
    assert box(original)==box(reopened)
    assert UsdGeom.GetStageMetersPerUnit(original)==UsdGeom.GetStageMetersPerUnit(reopened)
    assert UsdGeom.GetStageUpAxis(original)==UsdGeom.GetStageUpAxis(reopened)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
    preview_path=FOLDER/'engine_merged_preview.usda'
    preview=Usd.Stage.CreateInMemory()
    preview.GetRootLayer().subLayerPaths=[str(FOLDER/'engine_supported_preview.usda')]
    preview.OverridePrim('/World/Engine').GetReferences().SetReferences([Sdf.Reference(str(target))])
    preview.GetRootLayer().Export(str(preview_path))
    checked=Usd.Stage.Open(str(preview_path))
    assert sum(p.IsA(UsdGeom.Mesh) for p in Usd.PrimRange(checked.GetPrimAtPath('/World/Engine')))==len(groups)
    report=dict(source=str(source),candidate=str(target),source_sha256=digest,meshes_before=len(mapping),meshes_after=len(groups),triangles=sum(r['face_count'] for r in mapping),bytes_before=source.stat().st_size,bytes_after=target.stat().st_size,validation='Exact points, topology/winding, normals, UVs, material bindings/networks, textures, bounds, units and unchanged source passed',mapping=mapping)
    (ROOT/'outputs').mkdir(exist_ok=True)
    (ROOT/'outputs/engine-merge-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='mapping'},indent=2))

if __name__=='__main__':merge()
