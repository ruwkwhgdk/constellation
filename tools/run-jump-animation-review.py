import unreal as u,traceback
from pathlib import Path
from datetime import datetime
JUMP_REVIEW_DIR=Path(u.Paths.project_dir())/'Saved/JumpAcquisition'/datetime.now().strftime('AnimationIntegration_%Y%m%d_%H%M%S_%f')
JUMP_REVIEW_DIR.mkdir(parents=True)
try:exec((Path(u.Paths.project_dir())/'tools/review-jump-animations.py').read_text(encoding='utf8'),globals())
except:
 p=JUMP_REVIEW_DIR
 (p/'setup-error.txt').write_text(traceback.format_exc(),encoding='utf8');u.log_error(traceback.format_exc());u.SystemLibrary.quit_editor()
