"""Register the existing statue in the event placement tool; keep original cinematic content."""
import unreal as u
from pathlib import Path
import shutil, json
root=Path(u.Paths.project_dir()).resolve()
level='/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool'
map_file=root/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
backup=root/'Saved/SceneEventAuthoring/Backup/AbandonedSchool.umap'
backup.parent.mkdir(parents=True,exist_ok=True)
if not backup.exists(): shutil.copy2(map_file,backup)
assert u.EditorLoadingAndSavingUtils.load_map(level)
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
cls=u.EditorAssetLibrary.load_blueprint_class('/Game/SceneDirector/Statue/BP_StatueDirector')
statues=[a for a in actors.get_all_level_actors() if a.get_class()==cls]
assert len(statues)==1,'Expected maintained statue instance'
statue=statues[0]
existing=[a for a in actors.get_all_level_actors() if isinstance(a,u.SceneEventBinding) and a.get_editor_property('source')==statue]
assert len(existing)<=1,'Duplicate statue binding'
if not existing:
    binding=actors.spawn_actor_from_class(u.SceneEventBinding,statue.get_actor_location())
    binding.set_actor_label('연출_석상_상호작용')
    binding.set_editor_property('trigger',u.SceneEventTrigger.INTERACTION)
    binding.set_editor_property('source',statue)
    binding.set_editor_property('director',u.load_asset('/Game/SceneDirector/Statue/DA_StatueInteraction'))
    binding.set_editor_property('origin',u.SceneEventOrigin.SOURCE)
    binding.set_editor_property('repeat',u.SceneEventRepeat.EVERY_TIME)
    assert u.EditorLoadingAndSavingUtils.save_dirty_packages(True,False)
else: binding=existing[0]
(root/'Saved/SceneEventAuthoring/installation.json').write_text(json.dumps({'level':level,'binding':binding.get_path_name(),'event_id':str(binding.get_editor_property('event_id'))},ensure_ascii=False,indent=2),encoding='utf-8')
u.log('SCENE_EVENT_AUTHORING_INSTALLED '+binding.get_path_name())
