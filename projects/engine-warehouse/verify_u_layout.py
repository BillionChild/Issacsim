"""Static arrangement checks; no robot-motion or transport-load claim."""
from build_u_layout import Usd, UsdGeom, OUTPUT

s = Usd.Stage.Open(str(OUTPUT))
cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ['default','render'])
def bounds(path):
    return cache.ComputeWorldBound(s.GetPrimAtPath(path)).ComputeAlignedRange()

robot, rack = bounds('/World/Robot'), bounds('/World/Rack')
assert rack.GetMin()[1] > 2.3
assert abs(rack.GetMidpoint()[0]) < .1
assert bounds('/World/Conveyors/InlineInfeed').GetMax()[0] < -1.9
assert bounds('/World/Conveyors/Outbound').GetMin()[0] > 1.8
assert bounds('/World/Conveyors/InspectionToPickup').GetMax()[1] < -1.6
assert bounds('/World/Conveyors/ReworkReturn').GetMax()[1] < -3.
assert abs(bounds('/World/InlineLoad/InlinePallet').GetMin()[2]-.7) < 1e-6
assert abs(bounds('/World/OutboundCarrier').GetMin()[2]-.7) < 1e-6
assert not any('Pin' in p.GetName() for p in Usd.PrimRange(s.GetPrimAtPath('/World/OutboundCarrier')))
assert s.GetPrimAtPath('/World/OutboundCarrier/Pad0')
assert s.GetPrimAtPath('/World/OutboundCarrier/Pad1')
assert bounds('/World/Vision/Camera').GetMin()[2] > bounds('/World/InlineLoad').GetMax()[2]

robot_shapes=[]; others=[]
for p in s.Traverse():
    path=str(p.GetPath())
    if path.startswith(('/World/Flow/','/World/Zones/')): continue
    if p.IsA(UsdGeom.Mesh) or p.IsA(UsdGeom.Cube) or p.IsA(UsdGeom.Cylinder):
        (robot_shapes if path.startswith('/World/Robot/') else others).append((path,cache.ComputeWorldBound(p).ComputeAlignedRange()))
hits=[]
for a,ab in robot_shapes:
    for b,bb in others:
        if all(min(ab.GetMax()[i],bb.GetMax()[i])-max(ab.GetMin()[i],bb.GetMin()[i]) > .001 for i in range(3)):
            hits.append((a,b))
assert not hits, hits[:5]
print('PASS: U topology, vision above corner, two separate pallet types, roller-level alignment, static robot external AABB clearance.')
