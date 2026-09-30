from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u,runpy,json
from pathlib import Path
root=Path(u.Paths.project_dir());out=root/'ArtSource/OvergrownHall/TripoReplacement/v002'
level=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert level.load_level('/Game/Constellation/Worlds/OvergrownHall/Maps/L_OvergrownHall_TripoFull')
for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
    if a.get_actor_label().startswith('OH_FULL_14_'):
        a.set_actor_rotation(u.Rotator(pitch=0,yaw=180,roll=0),False)
assert level.save_current_level()
placements=load_current_json((out/'placements.json').read_text())
for r in placements:
    if r['id']=='14':r['yaw']=180
(out/'placements.json').write_text(json.dumps(placements,indent=2))
runpy.run_path(str(root/'Content/Python/capture_tripo_full_hall.py'))
