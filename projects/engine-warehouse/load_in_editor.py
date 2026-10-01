"""Run once in Isaac Sim's Script Editor. Does not launch/close SimulationApp."""
from pathlib import Path
import omni.kit.app

ROOT=Path('C:/IssacsimProject/Issacsim')
manager=omni.kit.app.get_app().get_extension_manager()
manager.add_path(str(ROOT/'exts'))
manager.set_extension_enabled_immediate('engine.warehouse',True)
from engine_warehouse_editor import get_instance
if get_instance() is not None:get_instance().window.visible=True
print('Engine Warehouse extension enabled. Click Load Project in its window.')
