import unreal as u
from pathlib import Path
R=Path(u.Paths.project_dir())
s=(R/'tools/commit-jump-animations.py').read_text().replace('finally:u.SystemLibrary.quit_editor()','')
exec(s,globals())
if not (out/'saved.json').exists():u.SystemLibrary.quit_editor()
else:exec((R/'tools/run-jump-animation-review.py').read_text(),globals())
