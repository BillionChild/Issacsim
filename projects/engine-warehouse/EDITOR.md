# Work inside the existing Isaac Sim editor

The extension does not create or close SimulationApp. Your regular Isaac Sim window remains open across code edits and demo runs.

## Register in the current editor session

Open Isaac Sim's Script Editor. Open and run:

`C:/IssacsimProject/Issacsim/projects/engine-warehouse/load_in_editor.py`

Or paste and run:

```python
exec(compile(open(r"C:\IssacsimProject\Issacsim\projects\engine-warehouse\load_in_editor.py", encoding="utf-8").read(), "load_in_editor.py", "exec"))
```

An **Engine Warehouse** panel appears. **Load Project** uses the editor's unsaved-stage prompt before replacing the current stage. Save any work you want to retain.

Alternatively add `C:/IssacsimProject/Issacsim/exts` to the Extensions search paths in the editor, search **Engine Warehouse**, and enable it. The script registration above is for the current editor session; run it again after reopening the editor unless you configured a persistent extension search path/autoload.

## Normal workflow

### First-engine anomaly demonstration

The Monitor includes **ROBOT PROBLEM SOLVING | ENG-0001**: Observe ->
Estimate -> Correct / grip -> Verify seat. Blue indicates activity, orange
HOLD, green verified completion. RGB estimates are labeled separately from
the measured rack-seat error and maximum lift tilt. An accepted image alone
does not mean success; a recorded E1 seating check is required. Completed
observations and recaptures reset with the scenario. Mask clearing remains
operator-assisted. This panel always describes E1, independent of the
inventory-row selection. Toggle the extension OFF -> ON once for this UI
update. The existing image evidence window continues to show the RGB frame.

After loading the three-engine scenario and before Play, select a case in
**First engine anomaly**, then click **Apply case**. Available cases:
`normal`, X stop error (`stop_x`, 30 mm), Y offset (`lateral_y`, 15 mm),
`yaw` (2 degrees), `occluded`, and combinations (`x_y`, `x_yaw`, `y_yaw`,
`x_y_yaw`, `combined_occluded`). Stop / Reset is required to change cases.
The selected case persists across Reset; normal is the initial default.

The first engine/pallet acquires the offset smoothly near pickup. The wrist
RGB estimate drives the approach; the estimator never receives the chosen
case or injected pose. The engine remains at its actual pose until grasped.

For masked images the robot enters HOLD. **Retry observation** captures again
without clearing the fault. **Clear camera mask + retry** explicitly removes
the simulated sensor obstruction and captures a new image at the same
position. This is an operator/demo fault-clear action, not autonomous
physical obstruction removal. On a trusted estimate, Play continues the
corrected pickup and rack placement; after successful placement the vision
state becomes VERIFIED. Force-contact validation remains out of scope.

Warehouse inference uses `outputs/pickup-perception/warehouse-model.npz`,
trained by `train_warehouse_perception.py` from the current warehouse scene.
The separate pickup lab retains its own model. Generated weights are local
artifacts; a fresh checkout must train them. Changed lighting/assets/camera
require revalidation. Evidence and all retry observations are exported in
`outputs/warehouse-vision/` and `outputs/multi-engine-vision.json`.

Three-engine flow now overlaps independent conveyor work with the robot:
after outbound placement and return to standby, gate closure/departure no
longer blocks the next inbound. The monitor shows **CONVEYOR_DISPATCH** until
the loaded carrier reaches its buffer. Next infeed and repaired-engine
return also start after storage, during robot return. Shared loading-zone,
empty-carrier, gate and carrier-spacing conditions still gate movement.

For the three-engine scenario, use **Load three-engine scenario -> Play**.
The first engine now waits for an actual wrist RGB estimate before pickup;
an evidence window opens automatically. HOLD prevents pickup when inference
or calibration fails. Stop / Reset clears the measurement, so the next run
captures a fresh image. E2/E3 keep the existing replay behavior. After this
host update, toggle Engine Warehouse OFF -> ON once; no editor restart.

1. **Load Project** once to load the U-layout and connect the controller.
2. Use the editor's native **Play**: FAIL -> rework wait. Click **Repair complete -> Reinspect** to continue to reinspection and robot storage.
3. Native **Pause** freezes the process; **Play** resumes it.
4. Native **Stop**, or panel **Stop / Reset**, resets the pallet, engine, robot and occupied-cell state. It does not close the scene.
5. Edit and save Python logic, then **Reload Code + Reset**. Play again in the same editor.
6. If motion source changed, use **Rebuild + Check Motion**. This runs preparation and geometry checks in a hidden helper process while the editor stays responsive, then reloads the controller. See `logs/editor-motion-build.log` for failures.

At cycle completion the timeline pauses, preserving the stored-engine result for inspection. Stop resets it.

Reload covers `fanuc_kinematics.py`, `u_loop_cycle.py`, `u_storage.py`, `u_storage_scene.py`, `build_u_storage_demo.py`, and `editor_runtime.py`. The old standalone `run_u_loop_demo.py` remains a fallback launcher; editing its UI does not change this extension. To modify extension host/UI code itself, toggle **Engine Warehouse** off and on in Extensions, without closing Isaac Sim.

## Limits and preservation

- Only one demo controller is attached; reload detaches the previous runtime and removes its anonymous USD sublayer. User-authored layers are not cleared.
- Playback changes live in a dedicated anonymous session sublayer. Do not use Save Flattened to overwrite the source scene while a demo is attached.
- Opening a different stage detaches the controller; it does not animate that stage.
- The timeline is used as a play/pause/stop control, not an animation scrubber. Scrubbing the time slider does not seek the state machine.
- Robot motion remains kinematic; inspection outcomes remain simulated. Rebuilding is not full physics or self-collision validation.
- Avoid running the standalone demo controller and this extension on the same stage.

## Verification

`test_editor_runtime.py` checks reset, repeated attach/detach, edit-target preservation and preservation of a separate user session layer. `test_editor_integration.py` runs a separate headless Kit instance to check native timeline controls, three reloads, the complete process, stage-change detachment and reopening—all within one process.

## Playback speed and measurements (2026-10-02)

- Toggle the Engine Warehouse extension off/on once to load the new UI; Isaac Sim can stay open. Load Project, then choose 1x / 2x / 4x and Play.
- Speed scales the kinematic model clock, not conveyor or robot design speeds. Default is 1x. PhysX time and timeline scrubbing are not the model clock.
- Model steps are at most 1/60 second; render frame deltas are no longer clipped to 0.1 seconds. Rendering may skip intermediate poses at higher playback speed.
- Export timing / performance CSV writes `outputs/editor-cycle-metrics.csv`; completion also exports automatically. Export before Stop/Reset to preserve a partial run. A new export overwrites the previous file.
- CSV contains modeled phase seconds, app-update FPS, maximum frame interval and runtime CPU time. Update FPS is a frame-interval proxy, not a GPU profiler. GPU/render time is not measured separately.
- WAIT_REWORK is operator waiting time and must be separated from machine cycle time; pause time is excluded. Default FAIL -> repair -> OK -> storage -> robot idle takes 109.25 model seconds excluding repair wait. At 4x, nominal playback is about 27.3 wall seconds plus operator wait. Phase boundaries have up to one 1/60-second step quantization.
- Existing trajectory, motion cache and conveyor speeds are unchanged. No physical robot-speed or cycle-time optimization is claimed.

Offline checks: 60/20/5 FPS input intervals produced equal modeled duration (109.2500 s). A 500-update infeed microbenchmark reduced USD writes from 7500 to 1000 and runtime CPU cost from 0.340 to 0.255 ms/update. This excludes Hydra/RTX rendering and does not establish the cause of the user's low viewport FPS.

## Token accounting

Run `tools/token_usage_report.py --session <local Codex rollout JSONL>` with Python. It reads usage metadata and request labels, and writes local `outputs/token-usage-by-turn.csv` and `outputs/token-usage-summary.json`. It does not send conversation contents externally. Native turn totals are used without adding the duplicate token-count events. Cached input is a subset of input; reasoning is a subset of output. Per-code-file, per-tool and coding-versus-testing token allocation is not provided by these records. The active turn's report is a snapshot, not its final usage or a monetary bill.

## Windows HTTP port startup failure
If startup reports WinError 10013 while binding 0.0.0.0:8011, inspect Windows TCP excluded port ranges before changing the application or clearing caches. On 2026-10-02 the range 7964-8063 included 8011; a direct bind failed while port 18011 succeeded.
Run projects/engine-warehouse/start_editor.ps1 to start the regular editor with HTTP port 18011 and random port fallback disabled. The script also passes --ext-folder for this repository's exts directory and --enable engine.warehouse on every launch, so extension registration does not depend on saving the USD stage or the previous session. This leaves the installation and Windows exclusions unchanged. If Windows later reserves this port too, check another free port. External HTTP clients must use the selected port. The original launcher still uses its original settings.


## Pickup-ready standby (2026-10-02)
Robot waits with open jaws at flange (0.43, -2.2, 2.35) m, level tool yaw 180 degrees. Existing OK/READY_PICKUP permission still gates descent. It returns to the same hover after storage instead of folding. Speeds and placement are unchanged.
Robot motion: 95.136 s -> about 54.5 s (43% reduction). Full FAIL/repair/OK model cycle excluding manual wait: 109.250 s. This is not a globally optimal path or a validated real robot cycle. The single-cell demo still stops after one engine; continuous multi-engine scheduling is separate.
To apply in the open editor: Stop, Reload Code + Reset, Play. Load Project also refreshes the saved static layout. Delivered motion cache is already rebuilt.
Verification: 273 motion geometry samples and 1097 standby/load U-loop samples passed; 3 storage and 3 runtime tests passed. Limits: no continuous swept-volume, self-collision or real grip physics validation; visual playback remains unverified.


## Engine outbound
See OUTBOUND_STATUS.md for the verified sequence and limitations. Toggle the extension off/on once to get **Request outbound**. After inbound completes, click it to open the sliding crossbar, retrieve and place the engine, return the robot, close the crossbar, and convey the loaded carrier north. Support pads are unchanged. Stop resets the full scene. Each stage pauses on completion; export CSV after outbound for both stages. A new inbound run requires Reset; multi-order scheduling is not implemented.


## Three-engine automatic replay
Toggle Engine Warehouse off/on once, then **Load three-engine scenario -> Play**. The replay automatically performs E1 OK storage, E2 repair diversion, E3 OK storage, E2 repaired reinspection with E1 outbound priority, E2 storage, then E3/E2 outbound. Four transport carriers feed from the east; loaded carriers accumulate north. Empty inline pallets leave via the approved 2 m west recovery segment. Original Load Project remains the one-engine mode. See MULTI_ENGINE_PLAN.md for timing, boundaries and outputs. Three-engine replay takes about 491 model seconds (about 123 wall seconds at 4x under sufficient frame throughput).

## Warehouse monitor

Toggle Engine Warehouse off/on once after this UI update. The dockable
`Engine Warehouse Monitor` window opens with the extension; reopen it using
`Open warehouse monitor`. Load three-engine scenario, then Play.

The read-only monitor shows demo serials ENG-0001..0003, engine states and
vision results, a front-view 2x2 rack map, selected-engine entry/storage
times, and the seven latest events. Click an engine or occupied cell for
details. A is right lower, B is right upper; the two left cells are unused.
Times are simulation seconds: SCENE_ENTRY starts intake, STORED finishes
intake, including repair delays. Playback speed does not change these times.
Stop/Reset clears the history through the existing model reset. Single-engine
mode explicitly shows that the three-engine scenario must be loaded.
The monitor polls at most four times per wall-clock second and does not
modify the scene or scheduler. UI labels use English for Kit font portability.

### Manual outbound orders

After toggling the extension off/on for this update, load the three-engine
scenario. Before Play (or after Stop / Reset), select `Manual outbound` in
the monitor. Select a stored engine or occupied cell, then press
`Request selected engine outbound`. Press Play to process orders if paused.
Requests are FIFO; duplicates and engines not stored in a cell are rejected.
An active robot job finishes before the next outbound job starts. If both
scheduled cells are occupied, E2 waits until a requested shipment frees one.
E2 can use either A or B. Loaded carriers stop by shipment order, preserving
1.3 m spacing even when engines are requested in a different order.
The monitor shows OUTBOUND_QUEUED / OUTBOUND_MOVING / SHIPPED.
Reset clears orders and events but retains the chosen mode; Reload Code
creates a fresh runtime in Auto demo mode. Mode changes during playback
are disabled. Inspection/repair remain scripted in both modes.

## Pickup anomaly lab (stage 1)

Toggle the extension off/on, then Open pickup anomaly lab -> Load pickup test
scene. Select normal, stop_x, lateral_y, yaw, occluded, or a combined preset.
Capture RGB + depth writes outputs/pickup-captures/<timestamp>-<case>/.
Observation contains rgb.png, depth_m.npy and camera.json; ground_truth.json
is evaluation-only. Masked depth is NaN. Occlusion here is an observation
mask, not a physical obstacle; it appears only in exported images.

The referenced preview keeps original assets unchanged. Robot is hidden and
no motion controller is attached. X=30 mm, Y=15 mm and yaw=2 degrees are
small experimental inputs, not certified correction ranges. Engine/pallet/
fixture share one transform. Select normal to reset. The top-down 512x512
RGB-D camera uses a 24 mm focal length. This stage provides sensor capture;
learned perception, confidence scoring, corrected trajectories and recovery
are subsequent stages and are not implemented by this panel.

## Robot Camera (wrist view)

After extension off/on, load the three-engine scene or pickup anomaly lab,
then Open Robot Camera. Keep the main viewport on the overall process and
place the Robot Camera window beside it. The camera is rigidly parented to
EngineJig; it follows joint motion, without tracking or teleporting its aim.
A 12 mm wide-angle lens and a side bracket aim toward the engine/pallet.
The lab robot is stationary; normal vs x_y_yaw can be compared from the same
camera pose. Observation masks still apply to exported top-camera images
only, not the live wrist viewport. Bracket geometry is conceptual and has
not undergone full-cycle clearance verification. Close the extra viewport
when not needed to reduce rendering cost.

Portfolio presentation requirement: show overall process and robot view
together, with INJECT -> OBSERVE -> ESTIMATE -> CORRECT -> VERIFY. Display
actual measured errors and decision reasons once perception is connected.
Never present injected ground truth as a detection, or scripted attachment
as verified physical grasp. Current implementation ends at OBSERVE.

## Wrist RGB perception (stage 2)

Open pickup anomaly lab -> Load pickup test scene -> select case ->
Estimate from wrist RGB. The evidence window shows nominal pallet outline
in green and learned pose estimate in orange, plus X/Y in mm and yaw in
degrees. Results are estimates; robot correction is not yet executed.
Selecting another case hides stale evidence. Missing/dark regions and changed
wrist calibration produce HOLD. These are conservative demo gates, not
calibrated probability or a general out-of-distribution detector.

The current model is NumPy ridge RGB regression trained on 125 real rendered
views, with 24 held-out random poses. It estimates the rigid engine/pallet
assembly, assuming the engine remains correctly seated on its pins. It is
not a pretrained foundation model or keypoint detector. Training is limited
to fixed geometry, camera, lighting and +/-40 mm X, +/-25 mm Y, +/-3 deg yaw.
No real-world or unseen-lighting generalization is claimed.

Reproduce with Isaac Python: projects/engine-warehouse/train_pickup_perception.py.
Local model and evaluation report are outputs/pickup-perception/model.npz and
evaluation.json; model files are ignored by Git. Runtime predict(rgb) has no
USD, case name or truth inputs. The separate training harness uses truth for
labels and evaluation only. Mask injection affects captured wrist RGB,
not the raw live Robot Camera viewport.

## Vision-guided pregrasp correction (stage 3)

In the pickup lab, select a case and press Run vision-guided approach. Each
run captures fresh wrist RGB, rejects HOLD observations, solves joint angles
from the estimate, checks all 161 sampled poses on a private stage including
the camera/bracket, animates alignment and descent, verifies FK tracking,
then reverses the same path to the observation pose. No timeline Play needed.

The endpoint is 350 mm above the existing contact pose. Fingers stay open
and the engine/pallet never moves. This demonstrates corrected approach,
not grasp or completed warehouse recovery. Verify means joints reached the
image-derived target; it does not mean independent visual confirmation of
true engine alignment. The original fixed-pose image model is not valid at
the descended wrist pose. Re-estimation is available after returning.

Geometry checks use sampled robot/environment bounds and triangle/cube
checks; no self-collision, continuous swept volume, dynamic obstacles or
physical contact validation is claimed. Scene/object edits during movement
stop the sequence. If interrupted, reload the test scene before retrying.
Reports: outputs/pickup-corrections/*.json. UI phases: PLAN, CHECK, CORRECT,
VERIFY, RETURN, PREGRASP VERIFIED. Rejected observations cause no motion.

## Fixture-assisted level pickup (stage 4)

In Pickup anomaly lab, load the test scene, select a case, then press
**Verify level pickup (clamp / lift / reseat)**. A fresh wrist RGB estimate
drives the full approach. Rejected or masked observations produce HOLD.
The robot closes its jaws, commands a 200 mm lift, holds for two simulated
seconds, lowers to its original seat, then opens the jaws. An ideal fixed
joint models the engaged locating pins and clamp. It captures the engine's
existing relative pose at closure, without snapping it into alignment.
Success requires lift >190 mm, hold drift <3 mm, maximum orientation change
<0.25 degrees, horizontal drift <3 mm and reseat error <5 mm. Orientation
and drift are sampled throughout closure, lift, hold and lowering, not just
after the engine has already settled tilted. Afterward the temporary test layer is
removed and the observation pose is restored. No editor restart or Play
is needed. Reports: outputs/pickup-grasps/*.json.

This is a separate contact experiment, not a conversion of warehouse
playback to physical control. The engine uses a convex collision envelope
and a normalized 1 kg test mass; jaws follow kinematic trajectories. The
production locating fixture is abstracted as an initial world lock. It
hands over to the gripper fixed joint before lift, and takes over again
after reseating before jaw opening. This is ideal fixture-assisted motion,
not evidence of friction-only grasp success. Pin-hole seating, real engine mass, actuator force,
structural capacity and real-world grasp reliability are not validated.
The negative control leaves jaws open, never engages the gripper joint,
and leaves the engine on its pallet. It must fail the lift criterion.
The previous deliberate drop test has been replaced by reseating.

If the new button is missing, reopen the lab after reloading its Python
module in Script Editor:

```python
import importlib, grasp_contact, pickup_capture_editor
importlib.reload(grasp_contact)
importlib.reload(pickup_capture_editor).show()
```

Integration check (Isaac Python):
projects/engine-warehouse/test_grasp_editor.py. Covers masked HOLD, normal
closed grasp, open-jaw negative control, combined X/Y/yaw offsets, and
payload/robot restoration after each trial.

## Warehouse inbound: ideal level clamp

Engine Warehouse -> Load three-engine scenario -> Play. For a scene already
loaded in this mode, Reload Code + Reset also loads the new inbound logic.
The existing multi-engine playback remains kinematic. On jaw closure it
captures the engine-to-tool relative pose, carries the engine with that ideal
pin/clamp constraint (level roll/pitch; planned Z rotation allowed), checks
the rack seat before releasing, and only then records STORED. This does not
add live RGB perception to the main warehouse or prove physical pin contact.

Tilt >0.25 degrees, premature opening, or rack-seat error >5 mm / >0.25 degrees
produces HOLD before handover. Reset is required to resume after fixing a
failed route. The status text includes the last inbound clamp state.
Export timing / performance CSV also writes multi-engine-pickup-checks.json
under outputs, with per-engine tilt and seating error. Events include
PIN_CLAMP_LOCKED, LEVEL_PICKUP_VERIFIED, PIN_CLAMP_RELEASED and PICKUP_HOLD.
