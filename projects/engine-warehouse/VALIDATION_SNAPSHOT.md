# Engine Warehouse — recorded validation results

This report summarizes saved runs; generating it does not run Isaac Sim.
Each case is a recorded trial, not a statistical success probability.
Errors below are post-action seating position errors, not perception errors.
Kinematic clamp only; no force/contact or real-machine validation.

## warehouse-case-validation.json

Source modified (UTC): 2026-10-26T07:41:44.739199+00:00
SHA-256: `c1bde43d52e7abab1ca16018bd0e445c736d61d5625f90b2ecc0cd81f7766fe1`

Complete recorded cases: **17/17**.

| Case | Complete + 3 seating checks | E1 seating error (mm) | Observations |
|---|---|---:|---:|
| engine_normal | PASS | 1.210 | 1 |
| engine_shift | PASS | 0.182 | 1 |
| engine_high | PASS | 0.838 | 1 |
| engine_roll | PASS | 0.918 | 1 |
| engine_pitch | PASS | 0.188 | 1 |
| engine_combined | PASS | 0.594 | 1 |
| engine_combined_occluded | PASS | 0.594 | 3 |
| normal | PASS | 0.572 | 1 |
| stop_x | PASS | 0.262 | 1 |
| lateral_y | PASS | 0.907 | 1 |
| yaw | PASS | 0.338 | 1 |
| occluded | PASS | 0.436 | 3 |
| x_y | PASS | 0.807 | 1 |
| x_yaw | PASS | 0.466 | 1 |
| y_yaw | PASS | 0.238 | 1 |
| x_y_yaw | PASS | 0.295 | 1 |
| combined_occluded | PASS | 0.572 | 3 |

Maximum E1 seating error among complete cases: **1.210 mm**.

These sources are separate test batches; overlapping cases are not merged into a larger success rate.

## correction-ui-validation.json

Source modified (UTC): 2026-10-26T13:19:51.591978+00:00
SHA-256: `2cb611297aeb15dc81d579c9dbd9fc6151287de609bd61c13c3e8fae418443b8`

Complete recorded cases: **3/3**.

| Case | Complete + 3 seating checks | E1 seating error (mm) | Observations |
|---|---|---:|---:|
| engine_combined | PASS | 0.594 | 1 |
| normal | PASS | 0.427 | 1 |
| occluded | PASS | 0.405 | 3 |

Maximum E1 seating error among complete cases: **0.594 mm**.

These sources are separate test batches; overlapping cases are not merged into a larger success rate.
