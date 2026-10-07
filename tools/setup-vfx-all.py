from pathlib import Path
import unreal as u,runpy
runpy.run_path(str(Path(u.Paths.project_dir()).resolve()/'tools/setup-vfx-review.py'),run_name='__main__')
