import runpy,unreal as u
from pathlib import Path
runpy.run_path(str(Path(u.Paths.project_dir())/'Content/Python/refine_hall_reference.py'),init_globals={'STAGE':2})
