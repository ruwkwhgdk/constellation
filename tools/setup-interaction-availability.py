"""Install per-object availability and the shared interaction input gate."""
import json,shutil
from pathlib import Path
import unreal as u
root=Path(u.Paths.project_dir()).resolve(); out=root/'Saved/InteractionAvailabilityReview'
(out/'backups').mkdir(parents=True,exist_ok=True)
base='/Game/Constellation/Gameplay/Interaction/'
paths = ['/Game/Constellation/Gameplay/Interaction/BP_Interactable_Base',
 '/Game/Constellation/Environments/School/Blueprints/BP_Grand_Piano',
 '/Game/Constellation/Environments/School/Blueprints/BP_School_Door',
 '/Game/Constellation/Environments/School/Blueprints/BP_School_Gate',
 '/Game/Constellation/Environments/School/Blueprints/BP_School_Girl_Statue',
 '/Game/Constellation/Environments/School/Blueprints/BP_School_Locker_Open',
 '/Game/Constellation/Gameplay/Interaction/BP_Interactable_CheckPosition',
 '/Game/Constellation/Gameplay/Interaction/Actors/BP_Book',
 '/Game/Constellation/Gameplay/Interaction/Actors/BP_Chest',
 '/Game/Constellation/Gameplay/Interaction/Actors/BP_Kiosk_Reset',
 '/Game/Constellation/Gameplay/Interaction/Actors/BP_Ladder',
 '/Game/Constellation/Gameplay/Interaction/Actors/BP_Star_Object',
 '/Game/Constellation/Gameplay/Interaction/Actors/BP_Star_Object_Sequence',
 '/Game/Constellation/Gameplay/Interaction/Actors/BP_Star_Object_Sequence_Combat',
 '/Game/Constellation/Gameplay/Interaction/Actors/BP_Star_Object_Sequence_Transform',
 '/Game/Constellation/Gameplay/Interaction/Actors/BP_Switch',
 '/Game/Constellation/Gameplay/Interaction/Actors/BP_Sword_Pickup',
 '/Game/Constellation/Environments/School/Blueprints/BP_School_Chair',
 '/Game/Constellation/Environments/School/Blueprints/BP_School_Desk',
 '/Game/Constellation/Gameplay/Interaction/Actors/BP_Holdable_TestBox']
sub=u.get_engine_subsystem(u.SubobjectDataSubsystem); fn=u.SubobjectDataBlueprintFunctionLibrary
def backup(path):
 source=root/('Content/'+path[6:]+'.uasset'); dest=out/'backups'/source.name
 if not dest.exists():shutil.copy2(source,dest)
for path in paths:
 backup(path); bp=u.load_asset(path)
 handles=sub.k2_gather_subobject_data_for_blueprint(bp)
 objects=[fn.get_object_for_blueprint(fn.get_data(h),bp) for h in handles]
 if not any(isinstance(x,u.InteractionAvailabilityComponent) for x in objects):
  handle,reason=sub.add_new_subobject(u.AddNewSubobjectParams(parent_handle=handles[0],new_class=u.InteractionAvailabilityComponent,blueprint_context=bp))
  assert fn.is_handle_valid(handle),str(reason)
  sub.rename_subobject(handle,'InteractionAvailability')
 u.BlueprintEditorLibrary.compile_blueprint(bp)
 assert u.EditorAssetLibrary.save_loaded_asset(bp,False)
path=base+'Components/Ac_Interact'
backup(path); bp=u.load_asset(path)
result=u.CarryEditorLibrary.install_interaction_availability_gate(bp)
assert result.startswith('OK:'),result
u.BlueprintEditorLibrary.compile_blueprint(bp)
assert u.EditorAssetLibrary.save_loaded_asset(bp,False)
(out/'installed.json').write_text(json.dumps({'actors':paths,'input':path,'result':result},indent=2),encoding='utf-8')
u.log('INTERACTION_AVAILABILITY_INSTALLED '+result)
