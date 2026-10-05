# Outbound implementation — 2026-10-05

Connected to Engine Warehouse through Request outbound. User approved an opening crossbar while retaining existing support pads. Source carrier dimensions/pads are unchanged; runtime session-layer overrides animate SideRail0 vertically down 0.70 m as a conceptual sliding crossbar.

Sequence: completed inbound/occupied cell -> explicit request -> gate opens (2 s) -> cell retrieval -> elevated east route -> preseat -> jaws relieve 35 mm per side -> final 40 mm descent -> release -> open jaws -> robot returns to pickup standby -> gate closes (2 s) -> carrier and engine travel +Y 2.8 m at 0.4 m/s -> stop. Carrier departure waits until robot return and closed gate. Duplicate/early/empty-cell requests are rejected; Stop resets gate, carrier, payload and occupancy.

The opening gate is a kinematic concept with no actuator/hinge/locking hardware. Engine attachment during partial jaw relief is also kinematic; mechanical load retention is not validated. This remains a single-engine demo, not multi-order warehouse scheduling. Departure ends at a conveyor buffer; forklift/truck loading is not implemented.

Measured model duration: approximately 77.08 s outbound (about 66 s robot + gate/transport). Inbound duration remains 109.25 s excluding operator repair wait. Playback speed changes wall waiting time only.

Verification: baked complete sequence includes gate travel and carrier departure. 386 samples at 0.2 s intervals detected no robot/environment or payload/rack/carrier overlaps. FK/USD agreement passed; carried midpoint vertical-axis error ~0.000011 and grip interpolation error ~0.000010 m. Runtime tests verify ordered transitions, permission gates, closed-gate departure, final engine/carrier alignment and complete reset. This is sampled external geometry, not full swept-volume, robot self-collision, mechanical gate design or physical grasp validation.

Usage: toggle Engine Warehouse extension off/on once for new UI; run load_in_editor.py if needed; Load Project; Play and complete repair/reinspection; after inbound pauses, click Request outbound. Existing speed buttons and CSV export apply to both stages. The generated motion cache is already rebuilt locally. Rebuild + Check Motion now rebuilds/checks both inbound and outbound.

Headless Kit integration passed: native Play/Pause/Stop, three reloads, inbound plus outbound, reset and stage-change/reload. No traceback or warehouse reload error in the final integration log. In-editor visual review remains pending.
