"""Read-only current gate and tutorial authoring inventory."""
import unreal as u,json
from pathlib import Path
out=Path(u.Paths.project_dir())/'Saved/GateUI20261019'
out.mkdir(parents=True,exist_ok=True)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
for name,path in {
 'gate':'/Game/Constellation/Environments/School/Blueprints/BP_School_Gate',
 'base':'/Game/Constellation/Gameplay/Interaction/BP_Interactable_Base',
 'widget':'/Game/Constellation/UI/Widgets/WBP_Tutorial',
}.items():
 bp=u.load_asset(path)
 (out/(name+'.txt')).write_text(u.ResourceRecoveryLibrary.export_blueprint_graphs(bp),encoding='utf-8')
(out/'level.txt').write_text(u.ResourceRecoveryLibrary.export_level_blueprint_graphs(world),encoding='utf-8')
rows=[]
for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
 if 'Gate' not in a.get_class().get_name():continue
 row=dict(name=a.get_name(),label=a.get_actor_label(),cls=a.get_class().get_name(),location=str(a.get_actor_location()))
 for key in ('InteractOnce','bIsInteracted','IsOpen','IsOpened','OpenAngle'):
  try:row[key]=str(a.get_editor_property(key))
  except Exception:pass
 rows.append(row)
(out/'gates.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
u.log('GATE_UI_AUDIT_COMPLETE')
