"""Fresh process, saved-map checks only. No edits or gameplay."""
import unreal as u
from pathlib import Path
source=(Path(u.Paths.project_dir())/'Content/Python/capture_hall_painterly_finish.py').read_text()
exec(compile(source.split('\nscript=')[0],'verify_painterly_finish','exec'),globals())
u.SystemLibrary.quit_editor()
