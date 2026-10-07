"""Create action strings once and connect the heroine; preserve later designer edits."""
import unreal as u
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve()
path='/Game/Constellation/Gameplay/Interaction/Data/ST_InteractionActions'
result=u.CarryEditorLibrary.create_interaction_strings(str(root/'ArtSource/Gameplay/Interaction/initial-action-strings.csv'))
assert result.startswith('OK:'),result
table=u.load_asset(path)
assert table and u.EditorAssetLibrary.save_loaded_asset(table,False)
hero=u.load_asset('/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine')
sub=u.get_engine_subsystem(u.SubobjectDataSubsystem)
fn=u.SubobjectDataBlueprintFunctionLibrary
components=[fn.get_object_for_blueprint(fn.get_data(h),hero) for h in sub.k2_gather_subobject_data_for_blueprint(hero)]
prompt=next(c for c in components if isinstance(c,u.InteractionPromptComponent))
prompt.set_editor_property('action_strings',table)
u.BlueprintEditorLibrary.compile_blueprint(hero)
assert u.EditorAssetLibrary.save_loaded_asset(hero,False)
u.log('INTERACTION_ACTION_STRINGS_SAVED '+result)
