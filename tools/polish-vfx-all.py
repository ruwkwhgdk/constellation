import runpy,unreal as u
from pathlib import Path
r=Path(u.Paths.project_dir()).resolve()
runpy.run_path(str(r/'tools/setup-vfx-materials.py'),run_name='__main__')
runpy.run_path(str(r/'tools/polish-vfx-gallery.py'),run_name='__main__')
