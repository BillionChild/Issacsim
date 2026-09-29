"""Convert the selected SketchUp Collada to a static USD visual asset.
Run with C:/isaacsim/kit/python/python.exe. Requires pycollada in .venv/asset-tools.
SketchUp edge lines are omitted; triangles, normals and UVs are preserved.
"""
from pathlib import Path
import json
import os
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '.venv/asset-tools'))
usd_lib = next(Path('C:/isaacsim/extscache').glob('omni.usd.libs-*'))
sys.path.insert(0, str(usd_lib))
dll_handle = os.add_dll_directory(str(usd_lib / 'bin'))
import collada
import numpy as np
from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade, Vt

folder = ROOT / 'external_assets/engines/caterham_duratec'
source = folder / 'source/model.dae'
output = folder / 'usd/engine.usdc'
output.parent.mkdir(exist_ok=True)
model = collada.Collada(str(source))
assert model.assetInfo.upaxis == 'Z_UP'
unit = model.assetInfo.unitmeter
assert unit and unit > 0
stage = Usd.Stage.CreateNew(str(output))
UsdGeom.SetStageMetersPerUnit(stage, 1.0)
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
root = UsdGeom.Xform.Define(stage, '/Engine')
stage.SetDefaultPrim(root.GetPrim())
materials = {}
textures = []
for material in model.materials:
    path = '/Engine/Looks/' + material.id
    mat = UsdShade.Material.Define(stage, path)
    shader = UsdShade.Shader.Define(stage, path + '/Surface')
    shader.CreateIdAttr('UsdPreviewSurface')
    shader.CreateInput('roughness', Sdf.ValueTypeNames.Float).Set(0.5)
    diffuse = material.effect.diffuse
    if isinstance(diffuse, collada.material.Map):
        texture_path = source.parent / diffuse.sampler.surface.image.path
        destination = output.parent / 'textures' / texture_path.name
        destination.parent.mkdir(exist_ok=True)
        shutil.copy2(texture_path, destination)
        textures.append(destination.name)
        tex = UsdShade.Shader.Define(stage, path + '/Texture')
        tex.CreateIdAttr('UsdUVTexture')
        tex.CreateInput('file', Sdf.ValueTypeNames.Asset).Set(Sdf.AssetPath('textures/' + destination.name))
        tex.CreateInput('sourceColorSpace', Sdf.ValueTypeNames.Token).Set('sRGB')
        tex.CreateInput('wrapS', Sdf.ValueTypeNames.Token).Set('repeat')
        tex.CreateInput('wrapT', Sdf.ValueTypeNames.Token).Set('repeat')
        reader = UsdShade.Shader.Define(stage, path + '/UV')
        reader.CreateIdAttr('UsdPrimvarReader_float2')
        reader.CreateInput('varname', Sdf.ValueTypeNames.Token).Set('st')
        tex.CreateInput('st', Sdf.ValueTypeNames.Float2).ConnectToSource(reader.CreateOutput('result', Sdf.ValueTypeNames.Float2))
        shader.CreateInput('diffuseColor', Sdf.ValueTypeNames.Color3f).ConnectToSource(tex.CreateOutput('rgb', Sdf.ValueTypeNames.Float3))
    else:
        color = diffuse or material.effect.transparent or (0.5, 0.5, 0.5, 1)
        # Collada color values are retained; material lighting is approximated.
        shader.CreateInput('diffuseColor', Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color[:3]))
    mat.CreateSurfaceOutput().ConnectToSource(shader.CreateOutput('surface', Sdf.ValueTypeNames.Token))
    materials[material.id] = mat

all_points = []
triangles = 0
mesh_count = 0
skipped_lines = 0
for geometry in model.scene.objects('geometry'):
    for primitive in geometry.primitives():
        if isinstance(primitive, collada.lineset.BoundLineSet):
            skipped_lines += 1
            continue
        if not isinstance(primitive, collada.triangleset.BoundTriangleSet):
            raise TypeError(type(primitive))
        points = np.asarray(primitive.vertex * unit, dtype=np.float32)
        indices = primitive.vertex_index.copy()
        # A reflected instance needs the triangle winding reversed.
        reflected = np.linalg.det(geometry.matrix[:3, :3]) < 0
        if reflected:
            indices = indices[:, ::-1]
        mesh = UsdGeom.Mesh.Define(stage, f'/Engine/Geometry/Mesh_{mesh_count:04d}')
        mesh.CreatePointsAttr(Vt.Vec3fArray.FromNumpy(points))
        mesh.CreateFaceVertexCountsAttr([3] * len(indices))
        mesh.CreateFaceVertexIndicesAttr(indices.reshape(-1).tolist())
        mesh.CreateSubdivisionSchemeAttr('none')
        mesh.CreateDoubleSidedAttr(True)
        if primitive.original.normal is not None:
            normal_indices = primitive.normal_index[:, ::-1] if reflected else primitive.normal_index
            normals = primitive.original.normal[normal_indices].reshape(-1, 3)
            normals = normals @ np.linalg.inv(geometry.matrix[:3, :3])
            lengths = np.linalg.norm(normals, axis=1, keepdims=True)
            normals = normals / np.maximum(lengths, 1e-12)
            mesh.CreateNormalsAttr(Vt.Vec3fArray.FromNumpy(normals.astype(np.float32)))
            mesh.SetNormalsInterpolation('faceVarying')
        if primitive.texcoordset:
            uv_indices = primitive.texcoord_indexset[0]
            if reflected:
                uv_indices = uv_indices[:, ::-1]
            uv = primitive.texcoordset[0][uv_indices].reshape(-1, 2).astype(np.float32)
            UsdGeom.PrimvarsAPI(mesh).CreatePrimvar('st', Sdf.ValueTypeNames.TexCoord2fArray, 'faceVarying').Set(Vt.Vec2fArray.FromNumpy(uv))
        if primitive.material:
            UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(materials[primitive.material.id])
        all_points.append(points)
        triangles += len(indices)
        mesh_count += 1
stage.GetRootLayer().Save()
points = np.concatenate(all_points)
assert np.isfinite(points).all()
bounds = [points.min(axis=0).tolist(), points.max(axis=0).tolist()]
reopened = Usd.Stage.Open(str(output))
box = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ['default', 'render']).ComputeWorldBound(reopened.GetDefaultPrim()).ComputeAlignedRange()
assert np.allclose(bounds, [list(box.GetMin()), list(box.GetMax())], atol=1e-6)
report = dict(source=str(source), output=str(output), source_meters_per_unit=unit,
              meters_per_unit=1, up_axis='Z', meshes=mesh_count, triangles=triangles,
              skipped_edge_line_sets=skipped_lines, textures=textures, bounds_m=bounds,
              size_m=(points.max(axis=0)-points.min(axis=0)).tolist())
(folder / 'usd/conversion-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
