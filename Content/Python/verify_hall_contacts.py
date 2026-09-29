"""Independent saved-map contact checks; no editing or gameplay."""
import unreal as u
from pathlib import Path
source=(Path(u.Paths.project_dir())/'Content/Python/capture_hall_contacts.py').read_text()
exec(compile(source.split('\nscript=')[0],'verify_contacts','exec'),globals())
u.SystemLibrary.quit_editor()
