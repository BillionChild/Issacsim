# Fixture-assisted level pickup — 2026-10-12

Implemented in the separate Pickup anomaly lab, not warehouse playback.
Fresh wrist RGB inference -> sampled clearance -> approach -> close ->
ideal clamp lock -> pallet unlock -> lift -> two-second hold -> lower ->
pallet lock -> clamp unlock -> jaw opening -> restore scene.

Measured acceptance: lift >190 mm, hold drift <3 mm, maximum orientation
change <0.25 degrees, horizontal drift <3 mm, reseat error <5 mm.
Engine displacement comes from the transformed collision-envelope center,
not the asset's offset origin. Physics writes use a disposable session layer.
An engine-to-gripper fixed joint abstracts fully engaged locating pins and
clamps. It captures the measured relative pose at closure without snapping.
It is an ideal fixture constraint, not friction-only grasp verification.
The previous criteria omitted tilt during lifting and could accept an engine
that settled tilted. Those earlier success claims are superseded by this gate.

Isaac 6.1 editor-path integration check passed:

| Case | Lift | Max rotation change | Reseat error | Result |
| --- | ---: | ---: | ---: | --- |
| Normal / closed jaws | 200.02 mm | 0.000 degrees | 0.46 mm | Pass |
| Normal / open jaws | 0 mm | 0 degrees | 0 mm | Correctly rejected; no clamp lock |
| Combined X/Y/yaw / closed jaws | 200.02 mm | 0.000 degrees | 0.46 mm | Pass |

Masked observation caused HOLD without robot or payload motion. After every
trial, robot/payload transforms were restored and the contact layer removed.
Both closed runs: horizontal drift <0.06 mm; hold drift <0.56 mm.
Pose-metric regression checks: 2 passed, including a transient 3-degree tilt
followed by stable hold/reseat that must still fail. These are local
simulation results; values can vary slightly between rendered observations.

Scope: convex engine collider, normalized 1 kg body, kinematic jaws, ideal
pin/clamp joint and pallet fixture handover. This does not validate real engine
load, grip force, pin-hole seating, unseen conditions or production safety.
The camera position/lens are unchanged; its approved bracket is raised to
clear the contact approach. Reproduction and button instructions: EDITOR.md.

Next independent project stage: connect verified pickup to warehouse recovery
and add re-observation/retry policy. No automatic retry or rack placement is
claimed by this contact test.
