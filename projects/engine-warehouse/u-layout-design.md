# U-shaped warehouse cell — approved topology, provisional geometry

For development inside an existing Isaac Sim window, see **EDITOR.md**. The editor extension supports native Play/Pause/Stop, Reload Code and motion rebuild; the standalone launch commands below remain fallback options.

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
- Saved USD remains a STATIC review scene. The session-only loop demo below adds one-pallet transport; no camera inference, physical conveyor drive or new robot paths.
- Do not play the older `warehouse_cycle_preview.usdc` as if it uses this layout. That historical demo uses different coordinates.

## Single-pallet loop demonstration

`u_loop_cycle.py` implements the approved route at 0.4m/s, with a 2-second simulated inspection. The default result sequence is FAIL then OK. Missing scripted results fail closed; tests also cover a second FAIL followed by another repair/reinspection.

- `Start infeed`: depart from the north end of the inline conveyor.
- `Pause / Resume`: freeze/resume transport and inspection dwell.
- `Repair complete -> REINSPECT`: enabled only at the worker stop, while unpaused. Clears the old result to PENDING and releases return travel; never grants OK itself.
- `Reset to inlet`: resets the position, inspection sequence and pickup permission.
- `Top view` / `Perspective`: change review camera.
- Pickup permission is true only at the pickup station after an OK result; FAIL crosses that station with permission false. The robot remains static.
- Only one pallet exists in this demo. Multi-pallet merging, spacing and traffic arbitration are not implemented.
- Corner direction changes use kinematic translations without rotating the square pallet; no powered transfer mechanism is claimed.

Run in PowerShell:
```powershell
& C:/isaacsim/python.bat C:/IssacsimProject/Issacsim/projects/engine-warehouse/run_u_loop_demo.py
```
`--autoplay` starts infeed automatically, then still waits for manual repair completion. `--test` visibly exercises the repair gate with one automated test input, verifies final USD position/robot inactivity, and resets to normal manual controls without closing the window.

Offline checks: `C:/isaacsim/kit/python/python.exe projects/engine-warehouse/test_u_loop_cycle.py`.

## OK-triggered robot storage

`--store` connects the loop to a single-engine transfer into the lower rack cell at world (0.6,3.0). Robot base and U layout are unchanged. The original folded pose is both the wait and finish pose.

- Start requires current inspection OK, READY_PICKUP state and pallet position (0,-2.2,0.7).
- A one-shot transfer latch prevents repeated pickup from the still-high loop signal. The cell is reserved while moving and marked occupied at release.
- Close jaws -> attach the engine and its mock receiver blocks -> lift -> pass above the outbound carrier -> align at the rack front -> lower -> insert -> seat -> release -> open -> withdraw -> idle.
- The inline pallet and its support columns remain at pickup. Outbound transport is not animated by this step.
- Carried engine stays level; yaw may rotate. Attachment is a kinematic relationship, not simulated gripping forces or verified pin engagement.
- `Reset to inlet` resets the entire single-engine demonstration, including the occupied-cell state.

Prepare once after changing motion source:
```powershell
& C:/isaacsim/kit/python/python.exe C:/IssacsimProject/Issacsim/projects/engine-warehouse/build_u_storage_demo.py
& C:/isaacsim/kit/python/python.exe C:/IssacsimProject/Issacsim/projects/engine-warehouse/check_u_storage.py
& C:/isaacsim/python.bat C:/IssacsimProject/Issacsim/projects/engine-warehouse/run_u_loop_demo.py --store
```
Motion is cached locally in `outputs/u_storage_motion.npz`; source fingerprints prevent reuse after motion-code changes. Layout or asset changes require rebuilding and rechecking as well. `--store --test` performs the visible integration check, then resets to manual controls and keeps the window open.

Verification for this path: 476 time samples at 0.2s intervals, no detected robot/environment or payload/rack/carrier intersections; robot triangle/cube checks follow bounding-box checks. Midpoint carried-axis error <0.000010 and grip-position interpolation error <0.000011m. USD link transforms agree with FK. These are sampled external checks, not proof of continuous collision freedom, robot self-collision, engine/jig contact, real vision or load dynamics. Nominal robot-only sequence is about 95 seconds; this is a deliberately slow demonstration, not a production cycle-time estimate.
