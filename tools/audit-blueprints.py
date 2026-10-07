"""Read-only project Blueprint inventory and graph export; run with Unreal Python."""
import json
from pathlib import Path
import unreal as u

root = Path(u.Paths.project_dir()).resolve()
out = root / 'Saved/ProjectAudit/20261001'
out.mkdir(parents=True, exist_ok=True)
registry = u.AssetRegistryHelpers.get_asset_registry()
registry.search_all_assets(True)
assets = registry.get_assets_by_path('/Game', recursive=True, include_only_on_disk_assets=True)
rows = []
blueprints = []
for asset in assets:
    cls = str(asset.asset_class_path.asset_name)
    if 'Blueprint' not in cls and cls not in ('World', 'QuestDefinition', 'QuestDatabase'):
        continue
    path = str(asset.package_name) + '.' + str(asset.asset_name)
    row = {'path': path, 'class': cls}
    if 'Blueprint' in cls:
        blueprints.append(path)
        obj = asset.get_asset()
        row['loaded'] = obj is not None
        if obj:
            try:
                text = u.ResourceRecoveryLibrary.export_blueprint_graphs(obj)
                file = out / 'graphs' / (str(asset.package_name).removeprefix('/Game/') + '.txt')
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text(text, encoding='utf-8')
                row['graph_file'] = str(file.relative_to(out))
                row['graph_count'] = text.count('\nGRAPH ')
                row['node_count'] = text.count('Begin Object Class=')
            except Exception as exc:
                row['export_error'] = str(exc)
    rows.append(row)
    (out / 'inventory.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
(out / 'blueprints.txt').write_text('\n'.join(blueprints) + '\n', encoding='ascii')
u.log('PROJECT_AUDIT_EXPORT_COMPLETE blueprints=' + str(len(blueprints)))
