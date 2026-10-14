"""Actual Kit widget/state checks; no robot motion or new scene assets."""
from isaacsim import SimulationApp
app=SimulationApp({'headless':True})
import asyncio
from pathlib import Path
import omni.kit.app

async def test():
    manager=omni.kit.app.get_app().get_extension_manager()
    manager.add_path(str(Path(__file__).resolve().parents[2]/'exts'))
    manager.set_extension_enabled_immediate('engine.warehouse',True)
    from engine_warehouse_editor import get_instance
    from engine_warehouse_editor.dashboard import recovery_snapshot
    ext=get_instance();ext.multi=True;await ext.load_async()
    assert ext.runtime,ext.info.text
    m=ext.runtime.model;panel=ext.dashboard
    def show():
        panel.update(ext.runtime,force=True)
        return recovery_snapshot(m)
    assert show()['steps']==['WAIT']*4
    m.vision_state='OBSERVE'
    assert show()['steps'][0]=='ACTIVE'
    m.vision_result={'pose':[2.,-1.,.1],'accepted':False}
    m.observations=[m.vision_result];m.vision_state='HOLD';m.fault='HOLD: dark image'
    assert show()['tone']=='hold' and 'dark image' in panel.recovery_title.text
    assert 'rejected; not used' in panel.recovery_estimate.text
    m.vision_result=None;m.fault=None;m.vision_state='OBSERVE'
    assert show()['estimate']=='Image estimate: --'
    m.vision_result={'pose':[2.,-1.,.1],'accepted':True}
    m.observations.append(m.vision_result);m.vision_state='ACCEPTED'
    assert show()['steps']==['DONE','DONE','ACTIVE','WAIT']
    assert 'not yet verified' in panel.recovery_title.text
    assert 'Recaptures: 1' in panel.recovery_attempts.text
    m.fault='Clamp alignment failed'
    assert show()['steps'][2]=='HOLD'
    m.fault=None
    m.vision_state='VERIFIED'
    # State alone is insufficient: an actual E1 check must exist.
    assert show()['tone']!='success'
    m.pickup_checks=[dict(engine='E1',seat_error_m=.0015,max_tilt_deg=.02)]
    assert show()['tone']=='success' and '1.50 mm' in panel.recovery_outcome.text
    m.fault='Later engine fault'
    assert show()['tone']=='hold'
    ext.runtime.reset()
    assert show()['steps']==['WAIT']*4
    assert 'VERIFIED' not in panel.recovery_outcome.text
    assert 'Recaptures: 0' in panel.recovery_attempts.text
    panel.update(None,force=True)
    assert panel.recovery_estimate.text==''
    print('RECOVERY MONITOR PASS: waiting, observe, hold, retry, accepted, verified, fault, reset, detach',flush=True)

task=asyncio.ensure_future(test())
try:
    while not task.done():app.update()
    task.result()
except BaseException:
    import traceback
    traceback.print_exc();print('RECOVERY MONITOR FAILED',flush=True)
finally:app.close()
