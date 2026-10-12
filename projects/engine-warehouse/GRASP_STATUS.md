# Contact grasp status — 2026-10-12

Implemented in the separate Pickup anomaly lab, not warehouse playback.
Fresh wrist RGB inference -> sampled clearance -> approach -> close ->
fixture unlock -> lift -> two-second hold -> release -> restore scene.

Measured acceptance: lift >150 mm, hold drift <10 mm, release drop >100 mm.
Engine displacement comes from the transformed collision-envelope center,
not the asset's offset origin. Physics writes use a disposable session layer.
There is no engine-to-gripper joint or scripted engine transform following.

Isaac 6.1 editor-path integration check passed:

| Case | Lift | Hold drift | Release drop | Result |
| --- | ---: | ---: | ---: | --- |
| Normal / closed jaws | 175.45 mm | 0.0017 mm | 240.17 mm | Pass |
| Normal / open jaws | 0 mm | 0 mm | 0 mm | Correctly rejected |
| Combined X/Y/yaw / closed jaws | 172.81 mm | 0.0088 mm | 233.90 mm | Pass |

Masked observation caused HOLD without robot or payload motion. After every
trial, robot/payload transforms were restored and the contact layer removed.
Existing pregrasp geometry/rejection unit checks: 2 passed. These are local
simulation results; values can vary slightly between rendered observations.

Scope: convex engine collider, normalized 1 kg body, kinematic jaws, initial
world fixture lock released before lift. This does not validate real engine
load, grip force, pin-hole seating, unseen conditions or production safety.
The camera position/lens are unchanged; its approved bracket is raised to
clear the contact approach. Reproduction and button instructions: EDITOR.md.

Next independent project stage: connect verified pickup to warehouse recovery
and add re-observation/retry policy. No automatic retry or rack placement is
claimed by this contact test.
