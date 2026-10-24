"""Place only the pickup toast area, preserving the freshly loaded school map."""
import json, shutil
from pathlib import Path
import unreal as u

root=Path(u.Paths.project_dir())
out=root/'Saved/PickupTutorial'
out.mkdir(parents=True,exist_ok=True)
map_path='/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool'
assert 'PickupTutorial/Authoring' in u.Paths.project_saved_dir()
world=u.EditorLoadingAndSavingUtils.load_map(map_path)
assert world
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
existing=[a for a in actors.get_all_level_actors() if isinstance(a,u.PickupTutorialTrigger)]
assert len(existing)<=1, 'Multiple pickup areas; inspect before modifying'
source=root/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
backup=out/'AbandonedSchool-before-pickup.umap'
if not backup.exists():shutil.copy2(source,backup)
trigger=existing[0] if existing else actors.spawn_actor_from_class(u.PickupTutorialTrigger,u.Vector(2320,0,130))
assert trigger
trigger.set_actor_label('Tutorial_PickUp_StartRoom')
trigger.set_folder_path('Tutorials')
trigger.set_actor_location(u.Vector(2320,0,130),False,True)
trigger.set_editor_property('area_extent',u.Vector(200,650,160))
trigger.area.set_box_extent(u.Vector(200,650,160))
assert u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
assert u.EditorLoadingAndSavingUtils.load_map(map_path)
saved=[a for a in actors.get_all_level_actors() if isinstance(a,u.PickupTutorialTrigger)]
assert len(saved)==1
trigger=saved[0]
assert trigger.get_actor_location()==u.Vector(2320,0,130)
assert trigger.get_editor_property('area_extent')==u.Vector(200,650,160)
assert not trigger.get_editor_property('has_shown')
for start in (a for a in actors.get_all_level_actors() if isinstance(a,u.PlayerStart)):
    p=start.get_actor_location()-trigger.get_actor_location()
    assert abs(p.x)>200 or abs(p.y)>650 or abs(p.z)>160, 'Player start must be outside the pickup area'
(out/'placement.json').write_text(json.dumps(dict(map=map_path,actor=trigger.get_path_name(),location=[2320,0,130],extent=[200,650,160],message='[F]를 눌러 물건을 들 수 있습니다.',hold_seconds=8,repeat='Once per level visit'),ensure_ascii=False,indent=2),encoding='utf-8')
u.log('PICKUP_TUTORIAL_SAVED')
