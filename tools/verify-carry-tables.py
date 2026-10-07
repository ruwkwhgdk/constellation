"""Reload persisted rows, messages, and blueprint links without modifying assets."""
import json
from pathlib import Path
import unreal as u
out=Path(u.Paths.project_dir()).resolve()/'Saved/CarryReview/DataTables'
base='/Game/Constellation/Gameplay/Interaction/Data/'
common=u.load_asset(base+'DT_CarrySettings')
items=u.load_asset(base+'DT_HoldableItems')
strings=u.load_asset(base+'ST_CarryMessages')
assert common and items and strings
assert u.DataTableFunctionLibrary.export_data_table_to_json_file(common,str(out/'settings.json'))
assert u.DataTableFunctionLibrary.export_data_table_to_json_file(items,str(out/'items.json'))
settings=json.loads((out/'settings.json').read_text(encoding='utf-8-sig'))
props=json.loads((out/'items.json').read_text(encoding='utf-8-sig'))
assert len(settings)==1 and settings[0]['Name']=='Default'
assert settings[0]['PickupPlayRate']==2 and settings[0]['PlacePlayRate']==2
assert settings[0]['CharacterWeightKg']==50 and settings[0]['LiftWeightRatio']>0
assert len(props)==3 and {r['Name'] for r in props}=={'SchoolChair','SchoolDesk','TestBox'}
assert all('WeightKg' not in r for r in props)

sub=u.get_engine_subsystem(u.SubobjectDataSubsystem)
fn=u.SubobjectDataBlueprintFunctionLibrary
checks=[]
for path,typ,prop,key in (
 ('/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine',u.CarryComponent,'settings_row','Default'),
 ('/Game/Constellation/Environments/School/Blueprints/BP_School_Chair',u.HoldableComponent,'item_row','SchoolChair'),
 ('/Game/Constellation/Environments/School/Blueprints/BP_School_Desk',u.HoldableComponent,'item_row','SchoolDesk'),
 ('/Game/Constellation/Gameplay/Interaction/Actors/BP_Holdable_TestBox',u.HoldableComponent,'item_row','TestBox')):
 bp=u.load_asset(path)
 c=next(fn.get_object(fn.get_data(h)) for h in sub.k2_gather_subobject_data_for_blueprint(bp) if isinstance(fn.get_object(fn.get_data(h)),typ))
 row=c.get_editor_property(prop)
 assert row.data_table and str(row.row_name)==key
 checks.append({'blueprint':path,'row':str(row.row_name),'table':row.data_table.get_path_name()})
(out/'reload.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
u.log('CARRY_TABLE_RELOAD_VERIFIED '+json.dumps(checks))
