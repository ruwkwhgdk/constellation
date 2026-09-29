import runpy
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
runpy.run_path(str(BASE/'Scripts/preview_overgrown_flock.py'),init_globals={'FLOCK_OUT':BASE/'Scene/v001/Flock','HALL_BLEND':BASE/'Scene/v001/overgrown_hall_layout.blend'})
