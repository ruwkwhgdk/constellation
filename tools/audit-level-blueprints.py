"""Read-only level-script compile/export. Never changes or saves maps."""
import gc
import json
from pathlib import Path
import unreal as u

root = Path(u.Paths.project_dir()).resolve()
out = root / 'Saved/ProjectAudit/20261001'
rows = json.loads((out / 'inventory.json').read_text(encoding='utf-8'))
results = []
for row in rows:
    if row['class'] != 'World':
        continue
    path = row['path']
    u.log('AUDIT_LEVEL_BEGIN ' + path)
    try:
        world = u.load_asset(path)
        assert world is not None, 'World failed to load'
        text = u.ResourceRecoveryLibrary.export_level_blueprint_graphs(world)
        file = out / 'levels' / (path.split('.')[0].removeprefix('/Game/') + '.txt')
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text, encoding='utf-8')
        results.append({'path': path, 'result': text.splitlines()[0] if text else 'EMPTY'})
        world = None
    except Exception as exc:
        results.append({'path': path, 'error': str(exc)})
    (out / 'level-results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    gc.collect()
    u.SystemLibrary.collect_garbage()
u.log('AUDIT_LEVELS_COMPLETE ' + str(len(results)))
