# Outbound candidate status — 2026-10-05

Not connected to the editor runtime. Existing inbound workflow preserved.
User requested retaining existing carrier support pads; their dimensions/positions are unchanged.

Candidate: cell retrieval -> elevated east route -> carrier placement -> pickup standby. Built with build_u_outbound_demo.py; about 66 seconds, FK/USD agreement passed. Fingers open 35 mm per side at preseat before final 40 mm descent. This retains a kinematic attachment and does not prove mechanical grip stability.

Unchanged carrier: sampled geometry fails against robot-side top rail SideRail0 during wrist descent/withdrawal. Angled descent probes at yaw 330/390/300/420 also intersect carrier parts; 270/450 high poses failed IK. Do not use this candidate in production playback.

Concrete alternative for approval: keep support pads unchanged; make robot-side SideRail0 an opening/removable crossbar, open before robot enters and restore only after full robot clearance. Its open parking position, actuator motion and interlocks still need design/validation. A temporary test with only that rail deactivated passed 331 external-geometry samples (0.2 s intervals), no detected robot/environment or payload overlaps. Rail was restored after the probe. This is clearance evidence for an open aperture, not validation of a gate mechanism, self-collisions, physical grip or full swept-volume safety.

Pending user choice: approve opening crossbar or provide another preferred frame/gripper arrangement. Then implement gate clearance, outbound request gating, occupancy transfer, carrier departure only after robot-clear, reset and editor controls.
