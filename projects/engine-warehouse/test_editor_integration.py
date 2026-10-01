"""One-process, headless Kit test; never touches the user's open editor."""
from pathlib import Path
from isaacsim import SimulationApp
app=SimulationApp({'headless':True,'hide_ui':True})
import asyncio
import omni.kit.app
import omni.timeline
import omni.usd

ROOT=Path(__file__).resolve().parents[2]
manager=omni.kit.app.get_app().get_extension_manager()
manager.add_path(str(ROOT/'exts'));manager.set_extension_enabled_immediate('engine.warehouse',True)
from engine_warehouse_editor import get_instance
async def test():
    ext=get_instance();assert ext is not None
    await ext.load_async();assert ext.runtime,ext.info.text
    kit=omni.kit.app.get_app();timeline=omni.timeline.get_timeline_interface()
    timeline.play()
    for _ in range(12):await kit.next_update_async()
    assert ext.runtime.cycle.state=='INFEED'
    timeline.pause()
    for _ in range(2):await kit.next_update_async()
    frozen=ext.runtime.cycle.position
    for _ in range(8):await kit.next_update_async()
    assert ext.runtime.cycle.position==frozen
    timeline.stop()
    for _ in range(3):await kit.next_update_async()
    assert ext.runtime.cycle.state=='IDLE'
    for _ in range(3):
        ext.reload_code();assert ext.runtime,ext.info.text
        layers=list(ext.runtime.stage.GetSessionLayer().subLayerPaths)
        assert sum('warehouse-runtime' in p for p in layers)==1,layers
    r=ext.runtime
    r.tick(1000);assert r.cycle.state=='WAIT_REWORK' and r.storage.state=='WAITING'
    assert r.repair()
    for _ in range(600):
        r.tick(.5)
        if r.storage.state=='DONE':break
    assert r.storage.state=='DONE' and r.storage.cell_occupied
    ext.reset()
    assert r.cycle.state=='IDLE' and not r.storage.cell_occupied
    # Changing stages detaches the old controller and does not touch the new scene.
    await omni.usd.get_context().new_stage_async()
    for _ in range(3):await kit.next_update_async()
    assert ext.runtime is None
    await ext.load_async();assert ext.runtime
    print('EDITOR INTEGRATION PASS: native Play/Pause/Stop, 3 reloads, storage cycle, stage change, reload without editor restart',flush=True)
    ext.info.text='Verified. Click Play; repair input is manual. Stop resets; Reload applies code.'

task=asyncio.ensure_future(test())
reported=False
try:
    while app.is_running():
        app.update()
        if task.done() and not reported:
            reported=True
            task.result()
            break
finally:app.close()
