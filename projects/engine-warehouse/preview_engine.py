"""Open the converted engine in a persistent Isaac Sim preview window."""
from pathlib import Path
import argparse
from isaacsim import SimulationApp

parser = argparse.ArgumentParser()
parser.add_argument("--pallet", action="store_true", help="Show the approved inline pallet")
parser.add_argument("--stage", help="Open an already generated USD preview")
args, _ = parser.parse_known_args()
app = SimulationApp({"headless": False, "hide_ui": False})
import omni.usd
from omni.kit.viewport.utility import get_active_viewport
from pxr import Gf, Usd, UsdGeom, UsdLux

if args.stage:
    if not omni.usd.get_context().open_stage(str(Path(args.stage).resolve())):
        app.close()
        raise RuntimeError("Could not open preview stage")
    get_active_viewport().camera_path = "/World/PreviewCamera"
    print("CUSTOM PREVIEW READY", flush=True)
    while app.is_running():
        app.update()
    app.close()
    raise SystemExit(0)

folder = Path(__file__).resolve().parents[2] / "external_assets/engines/caterham_duratec/usd"
context = omni.usd.get_context()
context.new_stage()
stage = context.get_stage()
UsdGeom.SetStageMetersPerUnit(stage, 1.0)
UsdGeom.SetStageUpAxis(stage, "Z")
world = UsdGeom.Xform.Define(stage, "/World")
stage.SetDefaultPrim(world.GetPrim())
engine = UsdGeom.Xform.Define(stage, "/World/Engine")
engine.GetPrim().GetReferences().AddReference(str(folder / "engine.usdc"))
bounds = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ["default", "render"]).ComputeWorldBound(engine.GetPrim()).ComputeAlignedRange()
# Center only the preview instance; retain the source asset's coordinates and size.
center = bounds.GetMidpoint()
engine.AddTranslateOp().Set(Gf.Vec3d(-center[0], -center[1], -bounds.GetMin()[2] + (0.02 if args.pallet else 0)))
if args.pallet:
    pallet = UsdGeom.Xform.Define(stage, "/World/InlinePallet")
    pallet.GetPrim().GetReferences().AddReference(str(Path(__file__).resolve().parent / "assets/inline_pallet.usda"))
light = UsdLux.DomeLight.Define(stage, "/World/PreviewLight")
light.CreateIntensityAttr(1000)
camera = UsdGeom.Camera.Define(stage, "/World/PreviewCamera")
camera.CreateClippingRangeAttr(Gf.Vec2f(0.01, 100))
camera.CreateFocalLengthAttr(45)
view = Gf.Matrix4d().SetLookAt(Gf.Vec3d(1.0, -1.25, 0.9), Gf.Vec3d(0, 0, 0.25), Gf.Vec3d(0, 0, 1))
camera.AddTransformOp().Set(view.GetInverse())
stage.GetRootLayer().Export(str(folder / ("engine_pallet_preview.usda" if args.pallet else "engine_preview.usda")))
get_active_viewport().camera_path = camera.GetPath()
print("ENGINE PREVIEW READY", flush=True)
while app.is_running():
    app.update()
app.close()
