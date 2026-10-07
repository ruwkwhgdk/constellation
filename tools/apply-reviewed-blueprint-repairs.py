"""Apply reviewed failure-path repairs, retaining byte-for-byte backups."""
import hashlib
import json
import shutil
from pathlib import Path
import unreal as u

root = Path(u.Paths.project_dir()).resolve()
out = root / 'Saved/ProjectAudit/20261001'
repairs = {
    '/Game/Constellation/Gameplay/Interaction/Actors/BP_QuestProgressTrigger': (0, 2),
    '/Game/Constellation/Characters/Enemies/Blueprints/AI/BTT_Attack': (0, 1),
    '/Game/Constellation/Characters/Enemies/Blueprints/AI/BTT_GetNextPatrolPoint': (0, 1, 2, 4),
    '/Game/Constellation/Characters/Enemies/Blueprints/AI/BTS_CheckDistance': (0, 1),
}
report = out / 'applied-blueprint-repairs.json'
results = json.loads(report.read_text(encoding='utf-8')) if report.exists() else []
for path, expected in repairs.items():
    relative = Path(path.removeprefix('/Game/') + '.uasset')
    source = root / 'Content' / relative
    backup = out / 'backups' / relative
    backup.parent.mkdir(parents=True, exist_ok=True)
    if not backup.exists():
        shutil.copy2(source, backup)
    before_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    bp = u.load_asset(path)
    preview = u.ResourceRecoveryLibrary.repair_known_blueprint_logic(bp, False)
    assert preview in tuple(f'PREVIEW changes={n} errors=0 warnings=0' for n in expected), preview
    if preview == 'PREVIEW changes=0 errors=0 warnings=0':
        u.log('BLUEPRINT_REPAIR_ALREADY_APPLIED ' + path)
        continue
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before_hash, 'Asset changed during repair'
    result = u.ResourceRecoveryLibrary.repair_known_blueprint_logic(bp, True)
    assert 'errors=0 warnings=0' in result, result
    assert u.EditorAssetLibrary.save_loaded_asset(bp, False), path
    check = u.ResourceRecoveryLibrary.repair_known_blueprint_logic(bp, False)
    assert check == 'PREVIEW changes=0 errors=0 warnings=0', check
    results.append({'path': path, 'before_sha256': before_hash, 'after_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'result': result, 'idempotence': check})
    report.write_text(json.dumps(results, indent=2), encoding='utf-8')
    u.log('BLUEPRINT_REPAIR_SAVED ' + path + ' ' + result)
