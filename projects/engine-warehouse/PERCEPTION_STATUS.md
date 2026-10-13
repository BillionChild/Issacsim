# Wrist image pose estimation — 2026-10-11

## Warehouse connection — 2026-10-13

The wrist camera is now virtual: CameraBracket, CameraOuterDrop and
CameraHousing are no longer generated, and existing mount geometry is
deactivated when attaching to an older scene. The Camera prim, calibrated
transform, lens and gripper geometry remain unchanged. This deliberately
omits real camera mounting/package clearance from the demonstration.

The three-engine editor scenario now requires a fresh wrist RGB estimate for
E1 before inbound. OBSERVE freezes the logical scheduler at pickup. Accepted
pixel-only inference drives an IK approach, jaw closure, level lift and a
return to the existing rack route. E2/E3 retain their existing replay paths.
Rejected images, changed camera calibration, missing model or planner errors
cause HOLD with no pickup. Reset invalidates any in-flight observation.

Enable the updated extension once (OFF -> ON), then **Load three-engine
scenario -> Play**. The **Warehouse vision | first engine** window shows the
captured RGB and estimated outline. Subsequent logic edits use Reload Code +
Reset. Local outputs: `outputs/warehouse-vision/` PNG/JSON evidence and
`outputs/multi-engine-vision.json`; event CSV includes OBSERVE, ESTIMATED and
CORRECTION_READY before clamp lock and storage verification.

Validation: 11 offline tests cover compound estimate-driven pickup, level
rejoin, rejected observations, reset invalidation and existing replay.
`test_warehouse_vision.py` exercises actual RGB and the extension Play path,
then completes all three engines. A normal-scene run estimated roughly
(-0.7 mm, +0.1 mm, -0.07 degrees). This is a fixed-scene check, not a
generalization benchmark. Full multi-engine anomaly presets are the next step.

The grip is still an ideal kinematic pin/clamp. There is no contact-force or
swept-volume proof for the complete corrected route. Camera capture/planning
wall time is excluded from logical process time; current timing is not a
measured production cycle including vision latency. Earlier sections below
describe the separate lab milestones.

Implemented: fixed-scene learned RGB ridge regression, nominal/estimated pallet
outline evidence window, missing-image HOLD, camera-pose mismatch rejection.
Input is wrist RGB only; estimator imports no USD or case generator.
This is direct pose regression, not the initially proposed keypoint network.
It provides a small reproducible learned baseline before a larger detector.

125 grid training views; 24 separate random validation poses (seed 42).
Held-out MAE: X 1.065 mm, Y 0.259 mm, yaw 0.135 deg.
Held-out maximum: X 3.562 mm, Y 0.611 mm, yaw 0.368 deg.
These describe one fixed simulation configuration, not real deployment accuracy.
The separate 10-preset editor test passed (<8 mm / 1 degree for visible
cases, both mask cases rejected); changed wrist pose was also rejected.
The displayed image-distance and darkness gates are heuristics, not confidence probabilities.

Remaining: lighting/appearance variation, stronger pose estimation, limited
re-observation, IK/collision checked correction and post-action verification.
No automatic correction or physical grasp claim is made in this stage.

Artifacts (local, ignored): outputs/pickup-perception/model.npz,
evaluation.json, combined-estimate.png. Reproduction script:
train_pickup_perception.py; integration: test_pickup_perception_editor.py.

## Stage 3: image-guided pregrasp approach
Implemented Run vision-guided approach: fresh inference -> bounded IK ->
161-pose sampled environment clearance -> open-jaw pregrasp -> FK tracking
check -> reversed return. Stops 350 mm above contact due to unvalidated
gripper/camera geometry for final grasp. This is approach correction only.
Offline tests: rejection of invalid/held estimates and normal/combined geometry
passed. Isaac integration: occlusion caused no joint change; combined RGB
estimate drove approach, returned to original pose, and allowed re-inference.
Tracking is against estimated target; independent true-pose/physical grasp
verification and full recovery remain outstanding.
