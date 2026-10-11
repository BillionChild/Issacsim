# Wrist image pose estimation — 2026-10-11

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
