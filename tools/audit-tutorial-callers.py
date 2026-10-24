"""Read-only inventory of authored tutorial callers and level triggers."""
import unreal as u
import json
from pathlib import Path
out=Path(u.Paths.project_dir())/'Saved/TutorialAudit20261023'
out.mkdir(parents=True,exist_ok=True)
paths=['/Game/Constellation/UI/Blueprints/BP_HUD','/Game/Constellation/UI/Widgets/WBP_Tutorial','/Game/Constellation/Gameplay/Interaction/Actors/BP_Star_Object','/Game/Constellation/Gameplay/Interaction/Actors/BP_Sword_Pickup','/Game/Constellation/Gameplay/Interaction/Actors/BP_Star_Object_Sequence_Transform']
for path in paths:
    bp=u.load_asset(path)
    if bp:(out/(path.rsplit('/',1)[-1]+'.txt')).write_text(u.ResourceRecoveryLibrary.export_blueprint_graphs(bp),encoding='utf-8')
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
(out/'level.txt').write_text(u.ResourceRecoveryLibrary.export_level_blueprint_graphs(world),encoding='utf-8')
rows=[]
for actor in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
    if any(s in actor.get_class().get_name() for s in ['Trigger','Star_Object','Sword','Tutorial']):
        rows.append(dict(name=actor.get_name(),label=actor.get_actor_label(),cls=actor.get_class().get_name(),location=str(actor.get_actor_location())))
(out/'actors.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
u.log('TUTORIAL_CALLERS_AUDITED')
