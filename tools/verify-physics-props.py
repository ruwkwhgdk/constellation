"""Reload and verify physics table migration, including preserved designer data."""
import json
from pathlib import Path
import unreal as u
root=Path(u.Paths.project_dir()).resolve()
out=root/'Saved/PhysicsPropsReview'; out.mkdir(parents=True,exist_ok=True)
folder='/Game/Constellation/Gameplay/Interaction/Data/'
table=u.load_asset(folder+'DT_PhysicsProps')
items=u.load_asset(folder+'DT_HoldableItems')
assert table and items
assert u.DataTableFunctionLibrary.export_data_table_to_json_file(table,str(out/'physics-after.json'))
assert u.DataTableFunctionLibrary.export_data_table_to_json_file(items,str(out/'items-after.json'))
rows=json.loads((out/'physics-after.json').read_text(encoding='utf-8-sig'))
itemrows=json.loads((out/'items-after.json').read_text(encoding='utf-8-sig'))
assert all('WeightKg' not in r for r in itemrows)
assert {r['Name'] for r in rows}=={'SchoolChair','SchoolDesk','TestBox'}
before=out/'items-before.json'
if before.exists():
 expected=json.loads(before.read_text(encoding='utf-8-sig'))
 for r in expected: r.pop('WeightKg',None)
 assert expected==itemrows,'Existing hold/throw/offset settings changed'
baseline=json.loads((root/'ArtSource/Gameplay/PhysicsProps/initial-rows.json').read_text(encoding='utf-8-sig'))
for row in rows:
 old=next(x for x in baseline if x['Name']==row['Name'])
 for key,value in old.items():
  assert abs(row[key]-value)<.0001 if isinstance(value,float) else row[key]==value,(key,row)
sub=u.get_engine_subsystem(u.SubobjectDataSubsystem); fn=u.SubobjectDataBlueprintFunctionLibrary
paths={'SchoolChair':'/Game/Constellation/Environments/School/Blueprints/BP_School_Chair','SchoolDesk':'/Game/Constellation/Environments/School/Blueprints/BP_School_Desk','TestBox':'/Game/Constellation/Gameplay/Interaction/Actors/BP_Holdable_TestBox'}
for name,path in paths.items():
 bp=u.load_asset(path)
 objects=[fn.get_object_for_blueprint(fn.get_data(h),bp) for h in sub.k2_gather_subobject_data_for_blueprint(bp)]
 components=[x for x in objects if isinstance(x,u.PhysicsPropComponent)]
 assert len(components)==1
 row=components[0].get_editor_property('physics_row')
 assert row.data_table==table and str(row.row_name)==name
(out/'verified.json').write_text(json.dumps({'saved_rows':rows,'preserved_holdable_settings':True,'blueprint_links':paths},indent=2),encoding='utf-8')
u.log('PHYSICS_PROPS_RELOAD_VERIFIED')
