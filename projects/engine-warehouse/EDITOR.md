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
Run projects/engine-warehouse/start_editor.ps1 to start the regular editor with HTTP port 18011 and random port fallback disabled. This leaves the installation and Windows exclusions unchanged. If Windows later reserves this port too, check another free port. External HTTP clients must use the selected port. The original launcher still uses its original settings.


## Pickup-ready standby (2026-10-02)
Robot waits with open jaws at flange (0.43, -2.2, 2.35) m, level tool yaw 180 degrees. Existing OK/READY_PICKUP permission still gates descent. It returns to the same hover after storage instead of folding. Speeds and placement are unchanged.
Robot motion: 95.136 s -> about 54.5 s (43% reduction). Full FAIL/repair/OK model cycle excluding manual wait: 109.250 s. This is not a globally optimal path or a validated real robot cycle. The single-cell demo still stops after one engine; continuous multi-engine scheduling is separate.
To apply in the open editor: Stop, Reload Code + Reset, Play. Load Project also refreshes the saved static layout. Delivered motion cache is already rebuilt.
Verification: 273 motion geometry samples and 1097 standby/load U-loop samples passed; 3 storage and 3 runtime tests passed. Limits: no continuous swept-volume, self-collision or real grip physics validation; visual playback remains unverified.


## Engine outbound
See OUTBOUND_STATUS.md for the verified sequence and limitations. Toggle the extension off/on once to get **Request outbound**. After inbound completes, click it to open the sliding crossbar, retrieve and place the engine, return the robot, close the crossbar, and convey the loaded carrier north. Support pads are unchanged. Stop resets the full scene. Each stage pauses on completion; export CSV after outbound for both stages. A new inbound run requires Reset; multi-order scheduling is not implemented.


## Three-engine automatic replay
Toggle Engine Warehouse off/on once, then **Load three-engine scenario -> Play**. The replay automatically performs E1 OK storage, E2 repair diversion, E3 OK storage, E2 repaired reinspection with E1 outbound priority, E2 storage, then E3/E2 outbound. Four transport carriers feed from the east; loaded carriers accumulate north. Empty inline pallets leave via the approved 2 m west recovery segment. Original Load Project remains the one-engine mode. See MULTI_ENGINE_PLAN.md for timing, boundaries and outputs. Three-engine replay takes about 491 model seconds (about 123 wall seconds at 4x under sufficient frame throughput).
