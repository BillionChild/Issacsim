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
    ext.request_outbound();assert r.outbound.state=='OPENING'
    for _ in range(300):
        r.tick(.5)
        if r.finished:break
    assert r.outbound.state=='DONE' and not r.storage.cell_occupied
    assert r.outbound.carrier_y==2.8 and r.outbound.gate_open==0.
    ext.reset()
    assert r.outbound.state=='WAITING' and r.outbound.carrier_y==0.
    assert r.cycle.state=='IDLE' and not r.storage.cell_occupied
    # Changing stages detaches the old controller and does not touch the new scene.
    await omni.usd.get_context().new_stage_async()
    for _ in range(3):await kit.next_update_async()
    assert ext.runtime is None
    await ext.load_async();assert ext.runtime
    ext.multi=True;await ext.load_async();assert ext.runtime,ext.info.text
    mr=ext.runtime;assert mr.is_multi
    ext.dashboard.update(mr,force=True)
    assert 'ENG-0001' in ext.dashboard.rows['E1'].text
    assert '0.0s' in ext.dashboard.detail.text
    timeline.play()
    for _ in range(8):await kit.next_update_async()
    timeline.pause();paused=mr.sim_seconds
    for _ in range(3):await kit.next_update_async()
    assert mr.sim_seconds==paused
    mr.tick(1200);assert mr.finished and mr.model.shipped==['E1','E3','E2']
    ext.dashboard.update(mr,force=True)
    assert 'Shipped 3' in ext.dashboard.summary.text
    assert 'SHIPPED' in ext.dashboard.rows['E2'].text
    ext.dashboard.select('E2')
    assert 'ENG-0002' in ext.dashboard.detail.text
    ext.reset();assert mr.sim_seconds==0 and not mr.finished
    ext.dashboard.update(mr,force=True)
    assert 'PENDING' in ext.dashboard.rows['E2'].text
    assert 'Stored: --' in ext.dashboard.detail.text
    ext.dashboard.mode(True)
    assert mr.model.manual
    mr.tick(210)
    ext.dashboard.select('E3')
    assert ext.dashboard.order_button.enabled
    ext.dashboard.request()
    assert mr.model.requests==['E3']
    ext.dashboard.request()
    assert mr.model.requests==['E3']
    ext.dashboard.select('E1');ext.dashboard.request()
    mr.tick(230)
    ext.dashboard.select('E2');ext.dashboard.request()
    mr.tick(300)
    assert mr.model.shipped==['E3','E1','E2'],mr.model.summary
    ext.dashboard.update(mr,force=True)
    assert 'Shipped 3' in ext.dashboard.summary.text
    ext.reset()
    assert mr.model.manual and mr.model.requests==[]
    ext.reload_code();assert ext.runtime.is_multi
    print('EDITOR INTEGRATION PASS: native Play/Pause/Stop, 3 reloads, storage/outbound and three-engine cycles, stage change, reload without editor restart',flush=True)
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
