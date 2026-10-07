"""Apply tested heroine contact forces without changing furniture or the map."""
import shutil
from pathlib import Path
import unreal as u

root=Path(u.Paths.project_dir()).resolve()
out=root/'Saved/CarryReview/FirstContact'
out.mkdir(parents=True,exist_ok=True)
source=root/'Content/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine.uasset'
backup=out/'BP_Player_Heroine-before.uasset'
if not backup.exists(): shutil.copy2(source,backup)
bp=u.load_asset('/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine')
sub=u.get_engine_subsystem(u.SubobjectDataSubsystem)
fn=u.SubobjectDataBlueprintFunctionLibrary
objects=[fn.get_object(fn.get_data(h)) for h in sub.k2_gather_subobject_data_for_blueprint(bp)]
movement=next(c for c in objects if isinstance(c,u.CharacterMovementComponent))
movement.set_editor_property('initial_push_force_factor',360.)
movement.set_editor_property('push_force_factor',6000.)
u.BlueprintEditorLibrary.compile_blueprint(bp)
assert u.EditorAssetLibrary.save_loaded_asset(bp,False)
u.log('FURNITURE_CONTACT_SAVED initial=360 continuous=6000')
