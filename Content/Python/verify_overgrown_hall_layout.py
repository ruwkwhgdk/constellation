import unreal as u,runpy
from pathlib import Path
root=Path(u.Paths.project_dir()); folder=root/'ArtSource/OvergrownHall/Scene/v001'
runpy.run_path(str(root/'Content/Python/verify_overgrown_hall_blockout.py'),init_globals={'SOURCE_DIR':folder,'MAP_PATH':'/Game/Environment/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout'})
actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
cam=actors['OH_ReferenceCamera']; bench=actors['OH_SM_OH_Blockout_14']; center,_=bench.get_actor_bounds(False)
assert (center-cam.get_actor_location()).dot(cam.get_actor_right_vector())<0
assert actors['OH_ReferenceFog'].get_component_by_class(u.ExponentialHeightFogComponent).get_editor_property('enable_volumetric_fog')
settings=actors['OH_Exposure'].get_editor_property('settings')
assert settings.auto_exposure_min_brightness==1024 and settings.auto_exposure_bias==0
runpy.run_path(str(root/'Content/Python/verify_overgrown_flock.py'),init_globals={'FLOCK_DEST':'/Game/Environment/OvergrownHall/Scene','FLOCK_MAP':'L_OvergrownHall_Layout','FLOCK_OUT':folder/'Flock'})
