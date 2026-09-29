import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name('export_blockout_unreal.py')),init_globals={'DETAIL_MODE':True})
