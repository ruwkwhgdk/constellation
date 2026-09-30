"""Fresh saved-state checks and an actual render, without rebuilding assets."""
import unreal as u,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir())
runpy.run_path(str(ROOT/'Content/Python/verify_hall_growth_water.py'))
script=(ROOT/'Content/Python/capture_hall_exposure.py').read_text().replace('ArtSource/OvergrownHall/Scene/v001','ArtSource/OvergrownHall/TripoReplacement/v006').replace('/Game/Constellation/Environments/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout','/Game/Constellation/Worlds/OvergrownHall/Maps/L_OvergrownHall_TripoFull').replace('unreal_exposure_fixed.png','unreal_growth_water.png')
script=script.replace('pp=next',"u.EditorLevelLibrary.set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation())\nu.EditorLevelLibrary.pilot_level_actor(cam)\npp=next")
script=script.replace("'r.ScreenPercentage 100'","'ShowFlag.ReflectionEnvironment 1'")
exec(compile(script,'capture_saved_growth_water','exec'),globals())
