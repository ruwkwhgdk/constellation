"""Read-only saved v019 verification; no PIE or edits."""
import unreal as u
from pathlib import Path
source=(Path(u.Paths.project_dir())/'Content/Python/capture_hall_reference_finish.py').read_text()
exec(compile(source.split('\nscript=')[0],'verify_reference_finish','exec'),globals())
u.SystemLibrary.quit_editor()
