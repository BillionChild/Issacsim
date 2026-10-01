# U-shaped warehouse cell — approved topology, provisional geometry

2026-10-01. +Y is 12 o'clock; +X is 3 o'clock. This replaces the proposed straight-line layout for future work, not its historical demo files.

## Approved flow
- Robot central; rack at 12 o'clock with openings facing the robot.
- Inline roller infeed at 9 o'clock travels north -> south and turns east at the vision corner.
- Vision is at the L corner. An OK pallet moves to the 6 o'clock pickup station and stops for robot pickup.
- A FAIL pallet passes the pickup station WITHOUT robot pickup, turns down into the rework loop, and stops at the worker station.
- Worker repair completion permits return to the SAME vision corner. It is not an automatic OK signal; another inspection is mandatory.
- Reinspection OK -> pickup station. Another FAIL -> rework again.
- Fresh infeed and returning pallets must be mutually interlocked at the shared vision corner. Pickup permission requires that pallet's current OK result and station occupancy confirmation.
- Outbound conveyor at 3 o'clock travels south -> north. It is physically separate from the inspection/rework loop.

## Pallets
- Inline: existing 800mm pin fixture pallet.
- Outbound: custom open-top box-frame carrier, shock-absorbing support pads, no locating pins, fork channels for transport together with the engine on a wing-body truck.
- Preview carrier dimensions 1100 x 1100 x 950mm are PROVISIONAL and require visual review. No stacking, securing latch, restraint, verified fork compatibility or truck loading design is implied.

## Preview coordinates (metres, provisional spacing)
| Item | Position / route |
|---|---|
| Robot base | (0,0,0), folded static review pose |
| Rack center | (0,3,0); four existing padded cells |
| Infeed | X=-2.5, Y=3.4 -> -2.2 |
| Vision | (-2.5,-2.2), camera overhead |
| Pickup | (0,-2.2) |
| FAIL loop | (2.5,-2.2) -> (2.5,-3.6) -> (-2.5,-3.6) -> vision |
| Worker station | lower return leg around (0,-3.6), worker side south |
| Outbound | X=2.5, Y=-1 -> 3.4 |
| Roller top | Z=0.7 |

## Files and scope
- `build_u_layout.py`: generates the separate local `warehouse_u_layout_preview.usda` and own `assets/outbound_frame_pallet.usda`.
- `verify_u_layout.py`: static placement, pallet type and robot external AABB checks.
- Default `PreviewCamera` is top-down; `PerspectiveCamera` is the oblique view.
- Corner decks are schematic 90-degree transfer locations; driven roller/chain/lift details are not modeled yet.
- This is a STATIC review scene: no camera inference, conveyor interlocks, moving pallets or robot paths implemented for this layout.
- Do not play the older `warehouse_cycle_preview.usdc` as if it uses this layout. That historical demo uses different coordinates.
