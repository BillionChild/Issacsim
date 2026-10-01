"""Approved U cell topology; schematic roller transfers and transport carrier.

Coordinates: +Y=12 o'clock, +X=3 o'clock. Static layout review only.
Detailed spacings and carrier dimensions are provisional, not production specs.
"""
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
lib = next(Path('C:/isaacsim/extscache').glob('omni.usd.libs-*'))
sys.path.insert(0, str(lib))
_dll = os.add_dll_directory(str(lib/'bin'))
from pxr import Usd, UsdGeom, UsdShade, UsdLux, Sdf, Gf

FOLDER = ROOT/'external_assets/engines/caterham_duratec/usd'
OUTPUT = FOLDER/'warehouse_u_layout_preview.usda'


def stage(path, root):
    s = Usd.Stage.CreateNew(str(path))
    s.SetDefaultPrim(UsdGeom.Xform.Define(s, root).GetPrim())
    UsdGeom.SetStageMetersPerUnit(s, 1.)
    UsdGeom.SetStageUpAxis(s, 'Z')
    return s


def material(s, name, color, metal=0.):
    path = str(s.GetDefaultPrim().GetPath())+'/Looks/'+name
    m = UsdShade.Material.Define(s, path)
    shader = UsdShade.Shader.Define(s, path+'/Surface')
    shader.CreateIdAttr('UsdPreviewSurface')
    shader.CreateInput('diffuseColor', Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color))
    shader.CreateInput('metallic', Sdf.ValueTypeNames.Float).Set(metal)
    shader.CreateInput('roughness', Sdf.ValueTypeNames.Float).Set(.45)
    m.CreateSurfaceOutput().ConnectToSource(shader.CreateOutput('surface', Sdf.ValueTypeNames.Token))
    return m


def box(s, path, xyz, size, mat):
    o = UsdGeom.Cube.Define(s, path)
    o.CreateSizeAttr(1.)
    o.AddTranslateOp().Set(Gf.Vec3d(*xyz))
    o.AddScaleOp().Set(Gf.Vec3f(*size))
    UsdShade.MaterialBindingAPI.Apply(o.GetPrim()).Bind(mat)
    return o


def reference(s, path, asset, xyz=(0,0,0), prim=None):
    o = UsdGeom.Xform.Define(s, path)
    if prim:
        o.GetPrim().GetReferences().AddReference(str(asset), prim)
    else:
        o.GetPrim().GetReferences().AddReference(str(asset))
    o.AddTranslateOp().Set(Gf.Vec3d(*xyz))
    return o


def carrier():
    """Open-top box frame with three runners, fork channels and rubber supports."""
    out = HERE/'assets/outbound_frame_pallet.usda'
    s = stage(out, '/Carrier')
    steel = material(s, 'Frame', (.20,.29,.36), .7)
    rubber = material(s, 'SupportPads', (.035,.035,.04))
    for i, x in enumerate((-.49,0,.49)):
        box(s, f'/Carrier/Runner{i}', (x,0,.045), (.12,1.10,.09), steel)
    box(s, '/Carrier/Deck', (0,0,.135), (1.10,1.10,.05), steel)
    for i, x in enumerate((-.53,.53)):
        for j, y in enumerate((-.53,.53)):
            box(s, f'/Carrier/Post{i}{j}', (x,y,.545), (.04,.04,.81), steel)
        box(s, f'/Carrier/SideRail{i}', (x,0,.93), (.04,1.10,.04), steel)
    for j, y in enumerate((-.53,.53)):
        box(s, f'/Carrier/EndRail{j}', (0,y,.93), (1.10,.04,.04), steel)
    for i, y in enumerate((-.12,.12)):
        box(s, f'/Carrier/Pad{i}', (0,y,.215), (.50,.12,.11), rubber)
    s.GetDefaultPrim().SetCustomDataByKey('scope', 'Concept only: 1.10m square, 0.95m high; open top, no pins, two support pads, fork entry from +/-Y. Restraints and forklift/truck compatibility not designed.')
    s.GetRootLayer().Save()
    return out


def build():
    carrier_path = carrier()
    s = stage(OUTPUT, '/World')
    steel = material(s, 'Steel', (.48,.52,.57), .8)
    blue = material(s, 'Frame', (.055,.15,.26), .5)
    yellow = material(s, 'Guide', (.95,.6,.04), .3)
    green = material(s, 'OK', (.06,.55,.25))
    orange = material(s, 'Rework', (.95,.24,.035))
    dark = material(s, 'Camera', (.04,.045,.06))

    def rollers(name, axis, center, length, width=.9):
        base = '/World/Conveyors/'+name
        along = 0 if axis == 'X' else 1
        across = 1-along
        n = max(1, round(length/.1))
        for i in range(n):
            xyz = [center[0],center[1],.67]
            xyz[along] += -length/2+(i+.5)*length/n
            o = UsdGeom.Cylinder.Define(s, base+f'/Roller{i:02}')
            o.CreateAxisAttr('Y' if axis=='X' else 'X')
            o.CreateRadiusAttr(.03); o.CreateHeightAttr(width)
            o.AddTranslateOp().Set(Gf.Vec3d(*xyz))
            UsdShade.MaterialBindingAPI.Apply(o.GetPrim()).Bind(steel)
        for sign in (-1,1):
            xyz = [center[0],center[1],.62]
            xyz[across] += sign*(width/2+.04)
            size = [.08,.08,.12]; size[along] = length
            box(s, base+f'/Frame{sign+1}', xyz, size, blue)
            xyz[2] = .745; size[2] = .05; size[across] = .025
            box(s, base+f'/Guide{sign+1}', xyz, size, yellow)
            for end in (-1,1):
                leg = xyz.copy(); leg[along] += end*max(0,length/2-.12);leg[2]=.29
                box(s, base+f'/Leg{sign+1}{end+1}', leg, (.08,.08,.58), blue)

    rollers('InlineInfeed', 'Y', (-2.5,.85), 5.1)
    rollers('InspectionToPickup', 'X', (0,-2.2), 4.)
    rollers('FailReturnEast', 'Y', (2.5,-2.9), .4)
    rollers('ReworkReturn', 'X', (0,-3.6), 4.)
    rollers('ReinspectWest', 'Y', (-2.5,-2.9), .4)
    rollers('Outbound', 'Y', (2.5,1.2), 4.4, 1.2)
    # Transfer decks are topology placeholders, not a claimed roller-drive mechanism.
    for name,x,y in [('VisionCorner',-2.5,-2.2),('FailTurn',2.5,-2.2),('ReturnEast',2.5,-3.6),('ReturnWest',-2.5,-3.6)]:
        box(s, '/World/Transfers/'+name+'/Body', (x,y,.65), (1.,1.,.1), blue)
        box(s, '/World/Transfers/'+name+'/Deck', (x,y,.695), (.96,.96,.01), steel)
    # Reuse the actual approved robot and rack assets, with new layout transforms.
    reference(s, '/World/Robot', ROOT/'external_assets/robots/fanuc_r2000ic_210l/robot.usdc').AddRotateZOp().Set(-90)
    path = '/World/Robot/Base'
    for index, (axis, value) in enumerate(zip('ZYYXYX',(180,-60,79,0,125,0)),1):
        path += f'/J{index}'
        getattr(UsdGeom.Xformable(s.GetPrimAtPath(path)), 'AddRotate'+axis+'Op')().Set(value)
    reference(s, path+'/EngineJig', HERE/'assets/engine_jig.usda', (.24,0,0))
    reference(s, '/World/Rack', FOLDER/'warehouse_cell_preview.usda', (1.8,-1.25,0), '/World/Rack').AddRotateZOp().Set(90)
    # Referenced rack materials live outside the referenced subtree; rebind locally.
    for prim in Usd.PrimRange(s.GetPrimAtPath('/World/Rack')):
        if prim.IsA(UsdGeom.Cube) and '/Cradle_' not in str(prim.GetPath()):
            UsdShade.MaterialBindingAPI.Apply(prim).Bind(orange if 'Beam_' in prim.GetName() else steel if 'Cell_' in prim.GetName() else blue)
    reference(s, '/World/InlineLoad', FOLDER/'engine_supported_preview.usda', (-2.5,-2.2,.7))
    for name in ('Light','PreviewCamera'):
        s.OverridePrim('/World/InlineLoad/'+name).SetActive(False)
    reference(s, '/World/OutboundCarrier', carrier_path, (2.5,0,.7))
    # Vision hardware at the corner, with support outside the transfer envelope.
    box(s, '/World/Vision/Post', (-3.22,-2.2,.9), (.07,.07,1.8), blue)
    box(s, '/World/Vision/Arm', (-2.85,-2.2,1.76), (.81,.06,.06), blue)
    box(s, '/World/Vision/Camera', (-2.5,-2.2,1.69), (.14,.12,.10), dark)
    box(s, '/World/Vision/Light', (-2.5,-2.2,1.63), (.26,.22,.025), yellow)
    # Ground markings stay out of the load path; no physical stop geometry yet.
    box(s, '/World/Zones/Pickup', (0,-2.2,.006), (1.05,1.15,.012), green)
    box(s, '/World/Zones/Worker', (0,-4.55,.006), (1.4,.8,.012), orange)
    box(s, '/World/Rework/Table', (.9,-4.5,.78), (.7,.45,.06), blue)
    for x in (.6,1.2):
        box(s, '/World/Rework/Leg'+str(int(x*10)), (x,-4.5,.38), (.06,.4,.76), blue)

    def arrow(name, x, y, angle, color):
        root = UsdGeom.Xform.Define(s,'/World/Flow/'+name)
        root.AddTranslateOp().Set(Gf.Vec3d(x,y,.018));root.AddRotateZOp().Set(angle)
        o=UsdGeom.Mesh.Define(s,str(root.GetPath())+'/Arrow')
        o.CreatePointsAttr([(-.25,-.055,0),(.08,-.055,0),(.08,-.14,0),(.28,0,0),(.08,.14,0),(.08,.055,0),(-.25,.055,0)])
        o.CreateFaceVertexCountsAttr([7]);o.CreateFaceVertexIndicesAttr(list(range(7)));o.CreateSubdivisionSchemeAttr('none');o.CreateDoubleSidedAttr(True)
        UsdShade.MaterialBindingAPI.Apply(o.GetPrim()).Bind(color)
    for values in [('Infeed',-3.25,.8,-90,green),('ToPickup',-1.1,-1.48,0,green),('FailPass',1.35,-1.48,0,orange),('LoopDown',3.24,-2.85,-90,orange),('Return',0,-4.25,180,orange),('Reinspect',-3.25,-3.2,90,orange),('Outbound',3.4,1.2,90,green)]:
        arrow(*values)
    light = UsdLux.DomeLight.Define(s,'/World/Light');light.CreateIntensityAttr(900)
    for name, eye, target, up in [('PerspectiveCamera',(9,-12,10),(0,-.6,.6),(0,0,1)),('PreviewCamera',(0,-.6,17),(0,-.6,0),(0,1,0))]:
        c=UsdGeom.Camera.Define(s,'/World/'+name);c.CreateClippingRangeAttr(Gf.Vec2f(.01,100));c.CreateFocalLengthAttr(35)
        c.AddTransformOp().Set(Gf.Matrix4d().SetLookAt(Gf.Vec3d(*eye),Gf.Vec3d(*target),Gf.Vec3d(*up)).GetInverse())
    s.GetDefaultPrim().SetCustomDataByKey('scope','STATIC proposed spacing. Approved topology: vision corner -> OK pickup / FAIL bypass -> manual rework -> same vision corner. New-feed and recirculation require merge interlock. Old robot trajectory must not be used here.')
    s.GetRootLayer().Save()
    print(OUTPUT)
    return s


if __name__=='__main__':
    build()
