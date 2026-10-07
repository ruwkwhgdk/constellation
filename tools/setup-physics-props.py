"""Migrate preserved prop physics into a shared table; preserve existing designer rows."""
import json
from pathlib import Path
import unreal as u
root=Path(u.Paths.project_dir()).resolve()
out=root/'Saved/PhysicsPropsReview'
folder='/Game/Constellation/Gameplay/Interaction/Data'
path=folder+'/DT_PhysicsProps'
table=u.load_asset(path) if u.EditorAssetLibrary.does_asset_exist(path) else None
if table is None:
 factory=u.DataTableFactory()
 factory.set_editor_property('struct',u.load_object(None,'/Script/Constellation.PhysicsPropRow'))
 table=u.AssetToolsHelpers.get_asset_tools().create_asset('DT_PhysicsProps',folder,u.DataTable,factory)
 assert table
 assert u.DataTableFunctionLibrary.fill_data_table_from_json_file(table,str(root/'ArtSource/Gameplay/PhysicsProps/initial-rows.json'))
assert u.EditorAssetLibrary.save_loaded_asset(table,False)
items=u.load_asset(folder+'/DT_HoldableItems')
assert u.EditorAssetLibrary.save_loaded_asset(items,False)
paths={'SchoolChair':'/Game/Constellation/Environments/School/Blueprints/BP_School_Chair','SchoolDesk':'/Game/Constellation/Environments/School/Blueprints/BP_School_Desk','TestBox':'/Game/Constellation/Gameplay/Interaction/Actors/BP_Holdable_TestBox'}
sub=u.get_engine_subsystem(u.SubobjectDataSubsystem); fn=u.SubobjectDataBlueprintFunctionLibrary
for name,path in paths.items():
 bp=u.load_asset(path)
 handles=sub.k2_gather_subobject_data_for_blueprint(bp)
 objects=[fn.get_object_for_blueprint(fn.get_data(h),bp) for h in handles]
 component=next((x for x in objects if isinstance(x,u.PhysicsPropComponent)),None)
 if component is None:
  handle,reason=sub.add_new_subobject(u.AddNewSubobjectParams(parent_handle=handles[0],new_class=u.PhysicsPropComponent,blueprint_context=bp))
  assert fn.is_handle_valid(handle),str(reason)
  sub.rename_subobject(handle,'PhysicsProps')
  component=fn.get_object_for_blueprint(fn.get_data(handle),bp)
 row=u.DataTableRowHandle()
 row.data_table=table; row.row_name=name
 component.set_editor_property('physics_row',row)
 u.BlueprintEditorLibrary.compile_blueprint(bp)
 assert u.EditorAssetLibrary.save_loaded_asset(bp,False)
u.log('PHYSICS_PROPS_MIGRATION_SAVED')
