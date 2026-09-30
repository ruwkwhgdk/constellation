import unreal as u,runpy,json
from pathlib import Path
root=Path(u.Paths.project_dir()); folder=root/'ArtSource/OvergrownHall/Scene/v001'
assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level('/Game/Constellation/Environments/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout')
actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
pp=next(a for a in actors if a.get_actor_label()=='OH_Exposure')
apply=runpy.run_path(str(root/'Content/Python/hall_exposure_settings.py'))['apply_hall_exposure']
result=apply(pp)
assert u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
(folder/'exposure_fix.json').write_text(json.dumps(result,indent=2))
u.log('HALL_EXPOSURE_FIXED '+json.dumps(result))
