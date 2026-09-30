import unreal as u,runpy,math
from pathlib import Path
root=Path(u.Paths.project_dir()); folder=root/'ArtSource/OvergrownHall/Scene/v001'
runpy.run_path(str(root/'Content/Python/import_overgrown_hall_blockout.py'),init_globals={'SOURCE_DIR':folder,'DESTINATION':'/Game/Constellation/Environments/OvergrownHall/Scene','MAP_NAME':'L_OvergrownHall_Layout'})
A=u.get_editor_subsystem(u.EditorActorSubsystem)
cam=next(a for a in A.get_all_level_actors() if a.get_actor_label()=='OH_ReferenceCamera')
cam.set_actor_rotation(u.Rotator(pitch=math.degrees(math.atan2(2.45,15)),yaw=90,roll=0),False)
assert u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
runpy.run_path(str(root/'Content/Python/build_overgrown_flock.py'),init_globals={'FLOCK_DEST':'/Game/Constellation/Environments/OvergrownHall/Scene','FLOCK_MAP':'L_OvergrownHall_Layout','FLOCK_OUT':folder/'Flock'})
runpy.run_path(str(root/'Content/Python/polish_hall_reference.py'))
