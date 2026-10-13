"""Real warehouse RGB domain check and first-engine guided inbound integration."""
from isaacsim import SimulationApp
app=SimulationApp({'headless':True})
import asyncio
from pathlib import Path
import omni.usd
import omni.kit.app
import omni.timeline
from multi_runtime import MultiRuntime

async def test():
    root=Path(__file__).resolve().parents[2]
    await omni.usd.get_context().open_stage_async(str(root/'external_assets/engines/caterham_duratec/usd/warehouse_multi_layout.usda'))
    manager=omni.kit.app.get_app().get_extension_manager()
    manager.add_path(str(root/'exts'));manager.set_extension_enabled_immediate('engine.warehouse',True)
    from engine_warehouse_editor import get_instance
    ext=get_instance();ext.reload_code();r=ext.runtime
    assert r is not None,ext.info.text
    r.tick(1200)
    assert r.model.vision_state=='OBSERVE' and r.model.active is None
    before=r.sim_seconds;r.tick(10);assert r.sim_seconds==before
    timeline=omni.timeline.get_timeline_interface();timeline.play()
    for _ in range(1000):
        await omni.kit.app.get_app().next_update_async()
        if r.model.vision_state!='OBSERVE' and not ext.busy:break
    timeline.pause()
    print('WAREHOUSE VISION RESULT',r.model.vision_result,r.model.fault,flush=True)
    assert r.model.vision_state=='ACCEPTED',r.model.fault
    r.tick(1200)
    assert r.finished,(r.model.phase,r.model.fault)
    assert r.model.shipped==['E1','E3','E2']
    assert len(r.model.pickup_checks)==3
    r.export_metrics();ext.detach();manager.set_extension_enabled_immediate('engine.warehouse',False)
    print('WAREHOUSE VISION PASS',flush=True)

task=asyncio.ensure_future(test())
try:
    while not task.done():app.update()
    task.result()
except BaseException:
    import traceback
    traceback.print_exc();print('WAREHOUSE VISION FAILED',flush=True)
finally:app.close()
