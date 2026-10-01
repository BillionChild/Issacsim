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
