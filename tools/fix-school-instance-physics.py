"""Repair legacy per-instance physics overrides in the maintained school map."""
import json
import shutil
from pathlib import Path
import unreal as u

root=Path(u.Paths.project_dir()).resolve()
out=root/'Saved/CarryReview/StartupAndTilt'
(out/'backups').mkdir(parents=True,exist_ok=True)
map_path='/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool'
assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level(map_path)
disk=root/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
backup=out/'backups/AbandonedSchool.umap'
if not backup.exists():
    shutil.copy2(disk,backup)
editor=u.get_editor_subsystem(u.EditorActorSubsystem)
rows=[]
for a in editor.get_all_level_actors():
    if a.get_class().get_name() not in ('BP_School_Chair_C','BP_School_Desk_C'):
        continue
    mesh=a.get_component_by_class(u.StaticMeshComponent)
    hold=a.get_component_by_class(u.HoldableComponent)
    body=mesh.get_editor_property('body_instance')
    if body.get_editor_property('simulate_physics') and mesh.mobility==u.ComponentMobility.MOVABLE:
        continue
    rows.append({'actor':a.get_name(),'label':a.get_actor_label(), 'before_physics':body.get_editor_property('simulate_physics'),'before_mobility':str(mesh.mobility)})
    mesh.set_mobility(u.ComponentMobility.MOVABLE)
    mesh.set_enable_gravity(True)
    mesh.set_mass_override_in_kg('',hold.get_weight_kg(),True)
    mesh.set_simulate_physics(True)
if rows:
    assert u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
(out/'instance-fixes.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
u.log('SCHOOL_INSTANCE_PHYSICS_FIXED '+json.dumps(rows))
