# Three-engine inbound/outbound scenario

## User-requested order
E1 first-pass OK -> cell A. E2 FAIL -> manual-repair buffer. E3 first-pass OK -> cell B. After E3 storage, scripted repair completes; E2 returns through the same vision station and passes. When E2 travels toward pickup or is ready there, request E1 outbound as soon as the robot is free. After E1 is placed on its carrier and the robot returns clear, admit E2 to cell A while E1's conveyor departure continues. Finally ship E3 then E2.

Use unique engine IDs and distinct pallet instances. Keep repaired E2 visible while E3 moves; never relabel one visible engine as another. Store cell occupancy by engine ID. One robot job at a time, cell/pickup/carrier reservations, departure only after robot-clear and gate-closed. No teleporting load between pallet/cell/carrier.

## Approved carrier buffer layout
Existing loading position (2.5,0,0.7), northbound discharge preserved. Approved empty-carrier feed from east along y=0, about 5 m; 1.10 m carriers at 1.30 m pitch. Four total: one at loading and three queued east. Loaded-carrier northbound buffer extends to about y=6 with controlled accumulation. The east-feed/north-discharge option was selected.

## Implementation sequence
1. Confirm carrier-feed geometry. Inspect cell A/B positions, derive second-cell trajectory with the existing FK/IK and verify sampled external clearance; do not translate robot joint trajectories blindly.
2. Add deterministic scheduler independent of USD. Track each engine's inspection, repair, transport, cell and shipment ownership. Advance all active conveyor/repair states concurrently with the robot. E2 may wait at pickup while E1 is shipped.
3. Add separate engine/inline-pallet and four carrier scene instances. Keep original detailed engine source and established inbound/outbound demos. Queue carriers with spacing/zone reservations; do not slide through occupied loading/discharge zones.
4. Connect Start three-engine scenario, pause, reset and per-engine event/cycle logs to the existing editor panel. Existing one-engine controls should remain usable.
5. Validate exact event ordering, exclusive robot use, unique engine ownership, cell reservations, no pickup of NG engines, carrier starvation/accumulation, partial-run reset, render-rate independence and route geometry. One targeted headless editor integration, then user visual review.

## Defaults and limits
A/B are the existing right lower/upper cells (.6,3,.66)/( .6,3,1.66). Upper routes passed sampled geometry with lower A occupied; left lower was not reachable with the tested approach. Repair completion is scripted after E3 storage in this replay, not a real inspection or human-work-duration model. Final shipment order E1,E3,E2. Empty inline pallet clearing and loaded outbound accumulation require explicit transport states, not disappearing geometry. Truck/forklift loading, mechanical gate hardware and physical grasp/load validation remain out of scope.


## Implementation checkpoint
Separate multi-engine scheduler, USD instances/runtime, east carrier feed/north buffer builder and editor mode implemented locally. All four genuine IK routes are cached; B geometry checks passed with lower A occupied. Original serial replay model time ~491.33 s, shipments E1,E3,E2. Existing single-engine mode retained.

## Parallel flow update — 2026-10-13

- Robot ownership ends at the completed return motion. Gate closure and loaded-carrier departure continue in independent dispatch jobs. OUTBOUND_DONE still means actual arrival at the outbound buffer, not merely robot release.
- E2 infeed starts once E1 is stored, during E1 robot return. Scripted E2 repair completion starts once E3 is stored, during E3 return. These do not change repair duration realism; this remains a scripted demo.
- E2 inbound no longer waits for E1 shipment completion. E2 outbound can begin before E3 finishes departing once the robot and an empty carrier at the loading position are available.
- Departure waits for robot clearance and closed gate. Empty carriers wait for 1.3 m discharge clearance; moving loaded carriers retain 1.3 m spacing. Destination slots are reserved on order start, so concurrent departures cannot select the same slot.
- Existing cached paths and speeds: 491.33 -> 437.42 model seconds (53.92 s / 10.97% reduction). E2 inbound starts at 230.85 s while E1 dispatch ends at 246.35 s. This comparison excludes camera capture/planning wall time and uses the nominal replay routes.
- `test_multi_cycle.py` includes slow-conveyor spacing, unique destinations, concurrent robot release, and reset checks. `check_parallel_flow.py` samples the new robot/other-load interactions at 0.2 s; this is not continuous collision or physical validation. Local reports: `outputs/parallel-flow-timing.json`, `outputs/parallel-flow-geometry.json`.

Empty inline pallet recovery approved on 2026-10-06 and added: existing loop -> left-end 2 m conveyor -> modeled upstream boundary at x=-4.5,y=-3.6. Empty pallets remain visible while returning, wait behind occupied pallets, then exit the modeled scene with an EMPTY_PALLET_EXIT event. No forklift handling is simulated beyond that boundary.

Usage: toggle Engine Warehouse off/on once for the new UI, then Load three-engine scenario -> Play (optional 4x). Repair/reinspection and outbound orders in this replay are scripted automatically. Pause freezes the scenario; Stop resets all engines, queues, cells and carriers. Load Project retains the original one-engine demo. Completion exports outputs/multi-engine-events.csv and multi-engine-performance.json.

End state: E1/C1 at north buffer y5.4, E3/C2 at y4.1, E2/C3 at y2.8; C4 empty at loading position. Cells empty; all three inline pallets exited via the recovery boundary. Four motion caches are generated by build_multi_motion.py. On code updates Rebuild + Check Motion in multi mode also regenerates/checks these routes.
