# Engine pose correction (2026-10-21)

## Process rule

- Assembly defects or missing parts produce inspection FAIL and enter repair.
- A misplaced/tilted engine is a pose error, not a part-quality failure.
  Observe the engine, correct the grip, lift in its current orientation,
  level in free space, and seat in the normal rack pose.
- Unusable observations or an unreachable/out-of-range correction HOLD at
  pickup. They do not route the engine to part repair.

## Separate engine and pallet

Existing presets retain their pallet-plus-engine RGB demonstration.
New `engine_*` presets keep the pallet fixed and independently displace the
engine and its receiver fixtures. XYZ is in millimetres; roll/pitch/yaw uses
XYZ Euler angles relative to the normal seated engine frame.

| Preset | XYZ mm | Roll / pitch / yaw deg |
|---|---|---|
| engine_normal | 0, 0, 0 | 0, 0, 0 |
| engine_shift | 30, 15, 0 | 0, 0, 2 |
| engine_high | 0, 0, 20 | 0, 0, 0 |
| engine_roll | 0, 0, 15 | 2, 0, 0 |
| engine_pitch | 0, 0, 15 | 0, -2, 0 |
| engine_combined | 20, -12, 20 | 1.5, -1, 2 |
| engine_combined_occluded | same combined pose | image mask also applied |

## Perception and control

The original RGB regressor was trained with engine and pallet moving
together. It is not used to infer these new independent six-axis engine poses.
The same virtual wrist camera supplies RGB and depth. A fixed calibrated
workspace crop keeps upper-engine depth surfaces and excludes the low pallet.
Trimmed rigid ICP registers the nominal engine depth reference to the current
observed points. Inference does not read the live engine's USD transform or
the injected case coordinates. Camera calibration is checked before capture.

This new path is **geometric RGB-D registration**, not a newly trained AI
model. It assumes a known engine, fixed viewpoint and isolated workspace;
it is not semantic recognition of arbitrary engines. RGB masking rejects
the observation before registration; retry requires a new sensor capture.

The estimated engine transform maps the known engine-to-tool grip transform
to a six-axis IK target. The robot approaches with open jaws, closes, lifts
without immediately flattening the engine, then levels above the conveyor
and rejoins the existing rack path. Actual engine pose is retained at clamp
capture, so estimation error remains visible in the final seating check.
Existing 5 mm seat-position and 0.25 degree final attitude checks remain.
The temporary lift tilt bound is the actual captured tilt plus 0.25 degrees;
it permits intentional tilted pickup without disabling final level checking.

Nominal correction limits: +/-40, +/-25, +/-30 mm XYZ and +/-3 degrees per
rotation axis. These are rejection bounds, not proof that every pose in that
continuous volume has been validated. Pins/supports/grip remain ideal
kinematic geometry; no force, pin-insertion or continuous collision proof.

## Reproduction

Use the Isaac Python launcher for `calibrate_engine_depth.py`. It captures a
normal reference and tests six independent poses before promoting
`outputs/engine-depth/reference.npz`. Results and reference are local ignored
artifacts. Recalibrate after asset, lens or scene appearance changes; the
current guard checks camera transform, not every asset modification.

Rebuild `build_multi_motion.py` after kinematics source changes. Toggle the
extension OFF -> ON, load the three-engine demo, select `engine_combined`,
Apply case and Play. Monitor shows XYZ plus roll/pitch/yaw and marks the
method as depth. E2 remains the simulated part-quality FAIL/rework example;
E1 pose cases never enter repair. E2/E3 keep nominal replay paths.

Offline checks: `test_engine_pose.py` plus existing guided/multi tests.
Actual sensor/controller integration: `test_warehouse_cases_editor.py`.

## Validation snapshot (2026-10-21)

- Offline suite: 22 tests passed (engine pose, guided inbound, cases, cycle, runtime).
- Actual Isaac Sim sensor/controller integration: all 17 cases finished, including
  seven independent engine cases and ten existing pallet cases.
- Engine-case E1 final seat position error: maximum 1.21 mm, below 5 mm gate.
- Six calibration poses passed the 3 mm / 0.2 degree calibration acceptance gates.
- Evidence: local logs/engine-pose-unit.log, logs/engine-pose-editor-final.log,
  outputs/warehouse-case-validation.json and outputs/engine-depth/calibration-check.json.
- These results establish the tested kinematic/sensor scenarios, not contact-force
  validation or exhaustive coverage of the correction envelope.

Camera recovery (2026-10-26): each pickup observation restores the wrist camera's
configured local transform and lens before rendering. Viewport navigation must
not become a new sensor calibration. The world-transform guard remains active.
If a run is already on HOLD, use Clear camera mask + retry after reloading code.
Regression: 5 offline tests and actual engine_roll / engine_combined runs with
intentionally altered camera transform/lens passed (logs/camera-restore-editor.log).

Known visual limitation: the ideal clamp does not check engine-to-pad surface
contact. A local vertical-ray sample over the current pad footprints found no
engine surface above one footprint; the other had a minimum sampled gap around
4.5 mm. These are geometry diagnostics, not contact-force results. Engine pose
and final seating tests alone do not establish a credible support contact.
Pad contact geometry revision is pending user approval.
