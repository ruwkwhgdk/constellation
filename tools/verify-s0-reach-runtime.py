import runpy
from pathlib import Path
root=Path(__file__).parent
runpy.run_path(str(root/'verify-s0-reach-asset.py'))
runpy.run_path(str(root/'verify-s0-cinematic-polish.py'))
