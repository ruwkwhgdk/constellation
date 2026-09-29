"""Apply the v012 shallow-water pass to the maintained map."""
import runpy,unreal as u
from pathlib import Path
runpy.run_path(str(Path(u.Paths.project_dir())/'Content/Python/polish_shallow_water.py'),init_globals={'APPLY':True})
