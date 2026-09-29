"""Independent saved-map verification without reapplying edits or running PIE."""
import unreal as u
from pathlib import Path
source=(Path(u.Paths.project_dir())/'Content/Python/capture_hall_roof.py').read_text()
exec(compile(source.split('\nscript=')[0],'verify_saved_roof','exec'),globals())
u.SystemLibrary.quit_editor()
