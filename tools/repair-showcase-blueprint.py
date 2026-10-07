"""Remove a confirmed obsolete editor-only call; save only after a clean compile."""
import hashlib
import json
import shutil
from pathlib import Path
import unreal as u

root = Path(u.Paths.project_dir()).resolve()
out = root / 'Saved/ProjectAudit/20261001'
path = '/Game/LuosCaves/Maps/LCaves_Will_Chambers_Contribution_Showcase'
relative = Path(path.removeprefix('/Game/') + '.umap')
source = root / 'Content' / relative
backup = out / 'backups' / relative
backup.parent.mkdir(parents=True, exist_ok=True)
if not backup.exists():
    shutil.copy2(source, backup)
before = hashlib.sha256(source.read_bytes()).hexdigest()
world = u.load_asset(path)
assert world is not None
for actor in u.GameplayStatics.get_all_actors_of_class(world, u.Actor):
    assert not any(s in actor.get_class().get_name().lower() for s in ('sequence', 'matinee', 'camera')), actor.get_path_name()
result = u.ResourceRecoveryLibrary.repair_obsolete_showcase_call(world)
assert result in ('APPLY changes=2 errors=0 warnings=0', 'APPLY changes=0 errors=0 warnings=0'), result
assert hashlib.sha256(source.read_bytes()).hexdigest() == before
if 'changes=2' in result:
    assert u.EditorLoadingAndSavingUtils.save_packages([world.get_outer()], False)
check = u.ResourceRecoveryLibrary.repair_obsolete_showcase_call(world)
assert check == 'APPLY changes=0 errors=0 warnings=0', check
(out / 'showcase-repair.json').write_text(json.dumps({
    'path': path, 'result': result, 'idempotence': check,
    'before_sha256': before, 'after_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
}, indent=2), encoding='utf-8')
u.log('SHOWCASE_REPAIR_SAVED ' + result)
