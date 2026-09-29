import runpy
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
runpy.run_path(str(BASE/'Scripts/export_blockout_unreal.py'),init_globals={'SOURCE_DIR':BASE/'Scene/v001','SOURCE_BLEND':'overgrown_hall_layout.blend','MATCH_CAMERA_HANDEDNESS':True})
