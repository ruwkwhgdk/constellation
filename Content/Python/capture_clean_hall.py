"""Verify and render v005 without modifying/rebuilding any assets."""
import unreal as u,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir())
runpy.run_path(str(ROOT/'Content/Python/verify_clean_hall_shapes.py'))
script=(ROOT/'Content/Python/capture_hall_exposure.py').read_text()
script=script.replace('ArtSource/OvergrownHall/Scene/v001','ArtSource/OvergrownHall/TripoReplacement/v005').replace('/Game/Environment/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout','/Game/Environment/OvergrownHall/TripoFull/Maps/L_OvergrownHall_TripoFull').replace('unreal_exposure_fixed.png','unreal_clean.png')
exec(compile(script,'capture_clean_saved_hall','exec'),globals())
