"""All preset cases through actual warehouse RGB, UI selection and recovery."""
from isaacsim import SimulationApp
app=SimulationApp({'headless':True})
import asyncio,json
from pathlib import Path
import omni.usd,omni.kit.app,omni.timeline

async def test():
    root=Path(__file__).resolve().parents[2]
    manager=omni.kit.app.get_app().get_extension_manager()
    manager.add_path(str(root/'exts'));manager.set_extension_enabled_immediate('engine.warehouse',True)
    from engine_warehouse_editor import get_instance
    from warehouse_cases import CASES,ENGINE_CASES
    ext=get_instance();ext.multi=True;await ext.load_async()
    assert ext.runtime,ext.info.text
    kit=omni.kit.app.get_app();timeline=omni.timeline.get_timeline_interface()
    reports=[]
    for name in list(ENGINE_CASES)+[n for n in CASES if n not in ENGINE_CASES]:
        truth=CASES[name]
        ext.reset()
        for _ in range(2):await kit.next_update_async()
        ext.case_combo.model.get_item_value_model().set_value(ext.case_names.index(name));ext.apply_case()
        r=ext.runtime;m=r.model;r.tick(100)
        assert m.vision_state=='OBSERVE' and m.active is None
        before=(m.engines['E1']['position'],m.engines['E1']['yaw'],m.engines['E1']['roll'],m.engines['E1']['pitch'],m.time)
        await ext.observe_first_engine();timeline.pause()
        assert before==(m.engines['E1']['position'],m.engines['E1']['yaw'],m.engines['E1']['roll'],m.engines['E1']['pitch'],m.time)
        if name in ENGINE_CASES:
            assert m.engines['E1']['pallet_position']==(0.,-2.2,.7)
            assert m.engines['E1']['cycle'].result=='OK'
        if truth[3]:
            assert m.vision_state=='HOLD' and m.active is None,(name,m.fault)
            for clear in (False,True):
                ext.retry_vision(clear)
                for _ in range(1000):
                    await kit.next_update_async()
                    if m.vision_state!='OBSERVE' and not ext.busy:break
                timeline.pause()
                assert m.vision_state==('ACCEPTED' if clear else 'HOLD'),(name,clear,m.fault)
            assert [v['accepted'] for v in m.observations]==[False,False,True]
        row=dict(case=name,estimate=m.vision_result,observations=len(m.observations),accepted=m.vision_state=='ACCEPTED')
        if row['accepted']:r.tick(1200)
        row.update(finished=r.finished,fault=m.fault,checks=m.pickup_checks)
        assert not any(e['engine']=='E1' and e['event']=='WAIT_REWORK' for e in m.events)
        assert any(e['engine']=='E2' and e['event']=='WAIT_REWORK' for e in m.events) if r.finished else True
        print('WAREHOUSE CASE',name,row['accepted'],row['finished'],row['fault'],flush=True)
        reports.append(row)
    (root/'outputs/warehouse-case-validation.json').write_text(json.dumps(reports,indent=2))
    assert all(v['accepted'] and v['finished'] and len(v['checks'])==3 for v in reports),[(v['case'],v['fault']) for v in reports if not v['finished']]
    print('WAREHOUSE CASES PASS',len(reports),flush=True)

task=asyncio.ensure_future(test())
try:
    while not task.done():app.update()
    task.result()
except BaseException:
    import traceback
    traceback.print_exc();print('WAREHOUSE CASES FAILED',flush=True)
finally:app.close()
