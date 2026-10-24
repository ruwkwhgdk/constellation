"""Set real carry action durations; preserve all existing resources and designer values."""
import json, shutil
from pathlib import Path
import unreal as u
root=Path(u.Paths.project_dir()).resolve()
out=root/'Saved/CarryResponsive20261024/Settings'
out.mkdir(parents=True,exist_ok=True)
path='/Game/Constellation/Gameplay/Interaction/Data/DT_CarrySettings'
table=u.load_asset(path)
assert table
backup=out/'DT_CarrySettings.uasset'
assert not backup.exists(), 'Use a new output folder for a new migration run'
shutil.copy2(root/'Content/Constellation/Gameplay/Interaction/Data/DT_CarrySettings.uasset',backup)
assert u.DataTableFunctionLibrary.export_data_table_to_json_file(table,str(out/'before.json'))
rows=json.loads((out/'before.json').read_text(encoding='utf-8-sig'))
row=next(r for r in rows if r['Name']=='Default')
for key in ('PickupActionSeconds','PlaceActionSeconds','ThrowActionSeconds'): row[key]=.75
assert u.DataTableFunctionLibrary.fill_data_table_from_json_string(table,json.dumps(rows,ensure_ascii=False))
assert u.EditorAssetLibrary.save_loaded_asset(table,False)
assert u.DataTableFunctionLibrary.export_data_table_to_json_file(table,str(out/'after.json'))
u.log('CARRY_ACTION_TIMING_SAVED')
