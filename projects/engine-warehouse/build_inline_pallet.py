"""Build the approved 800 x 800 x 20 mm, R50 inline pallet visual."""
import math
import os
from pathlib import Path
import sys

usd_lib = next(Path("C:/isaacsim/extscache").glob("omni.usd.libs-*"))
sys.path.insert(0, str(usd_lib))
dll_handle = os.add_dll_directory(str(usd_lib / "bin"))
from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade

output = Path(__file__).resolve().parent / "assets/inline_pallet.usda"
output.parent.mkdir(parents=True, exist_ok=True)
stage = Usd.Stage.CreateNew(str(output))
UsdGeom.SetStageMetersPerUnit(stage, 1.0)
UsdGeom.SetStageUpAxis(stage, "Z")
root = UsdGeom.Xform.Define(stage, "/InlinePallet")
stage.SetDefaultPrim(root.GetPrim())
root.GetPrim().SetCustomDataByKey("design", "800x800x20 mm; corner R50; visual only")

# Counterclockwise perimeter, 16 segments per quarter-circle.
ring = []
for cx, cy, start in [(0.35, 0.35, 0), (-0.35, 0.35, 90),
                      (-0.35, -0.35, 180), (0.35, -0.35, 270)]:
    for step in range(17):
        angle = math.radians(start + step * 90 / 16)
        ring.append((cx + 0.05 * math.cos(angle), cy + 0.05 * math.sin(angle)))
n = len(ring)
points = [(x, y, z) for z in (0.0, 0.02) for x, y in ring]
# Triangle fans on each cap and quad sides; outward-facing winding.
points.extend([(0, 0, 0), (0, 0, 0.02)])
faces = []
for i in range(n):
    j = (i + 1) % n
    faces.extend([(2*n, j, i), (2*n+1, n+i, n+j), (i, j, n+j, n+i)])
mesh = UsdGeom.Mesh.Define(stage, "/InlinePallet/Plate")
mesh.CreatePointsAttr(points)
mesh.CreateFaceVertexCountsAttr([len(f) for f in faces])
mesh.CreateFaceVertexIndicesAttr([i for f in faces for i in f])
mesh.CreateSubdivisionSchemeAttr("none")
mesh.CreateExtentAttr([Gf.Vec3f(-0.4, -0.4, 0), Gf.Vec3f(0.4, 0.4, 0.02)])
material = UsdShade.Material.Define(stage, "/InlinePallet/Metal")
shader = UsdShade.Shader.Define(stage, "/InlinePallet/Metal/Surface")
shader.CreateIdAttr("UsdPreviewSurface")
shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0.45, 0.48, 0.52))
shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(1.0)
shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.35)
material.CreateSurfaceOutput().ConnectToSource(shader.CreateOutput("surface", Sdf.ValueTypeNames.Token))
UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(material)
stage.GetRootLayer().Save()
print(output)
