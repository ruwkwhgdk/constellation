"""Mark only the starting gate as a one-shot interaction; preserve the current map."""
import unreal as u,json,shutil
from pathlib import Path
out=Path(u.Paths.project_dir())/'Saved/GateUI20261019'
out.mkdir(parents=True,exist_ok=True)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_name()=='AbandonedSchool'
assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world(), 'Stop PIE before authoring'
gates=[a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
       if a.get_name()=='BP_School_Gate_C_3' and a.get_class().get_name()=='BP_School_Gate_C']
assert len(gates)==1
gate=gates[0]
assert gate.get_actor_location()==u.Vector(-850,0,1000)
source=Path(u.Paths.project_dir())/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
backup=out/'AbandonedSchool-before-gate-fix.umap'
if not backup.exists():shutil.copy2(source,backup)
before=gate.get_editor_property('InteractOnce')
gate.set_editor_property('InteractOnce',True)
state=gate.get_component_by_class(u.InteractionAvailabilityComponent)
assert state and state.get_editor_property('respect_interact_once')
assert not gate.get_editor_property('bIsInteracted'), 'Never save a played/open gate state'
assert u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
(out/'gate-fix.json').write_text(json.dumps(dict(actor=gate.get_path_name(),previous_interact_once=before,interact_once=True),indent=2),encoding='utf-8')
u.log('START_GATE_AVAILABILITY_SAVED')
