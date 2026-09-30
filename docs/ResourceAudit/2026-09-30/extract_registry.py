"""Read-only asset metadata extraction. Never loads/saves/deletes assets."""
import json, datetime
from pathlib import Path
import unreal as u

root = Path(u.Paths.project_dir()).resolve()
out = root / 'Saved/ResourceAudit/20260930'
r = u.AssetRegistryHelpers.get_asset_registry()
r.search_all_assets(True)
r.scan_paths_synchronous(['/Game'], force_rescan=True)
options = u.AssetRegistryDependencyOptions(include_soft_package_references=True, include_hard_package_references=True, include_searchable_names=True, include_soft_management_references=True, include_hard_management_references=True)
assets = r.get_assets_by_path('/Game', recursive=True, include_only_on_disk_assets=True)
rows = {}
for a in assets:
    p = str(a.package_name)
    if p not in rows:
        rows[p] = {'classes': [], 'dependencies': sorted(str(x) for x in (r.get_dependencies(p, options) or [])), 'referencers': sorted(str(x) for x in (r.get_referencers(p, options) or [])), 'tags': {}, 'indexed_asset': True}
    rows[p]['classes'].append(str(a.asset_class_path.asset_name))
    for tag in ['SourceFile', 'AssetImportData']:
        v = a.get_tag_value(tag)
        if v:
            rows[p]['tags'][tag] = str(v)
for f in (root / 'Content').rglob('*'):
    if f.suffix.lower() not in ('.uasset', '.umap'):
        continue
    p = '/Game/' + f.relative_to(root / 'Content').with_suffix('').as_posix()
    if p not in rows:
        rows[p] = {'classes': [], 'dependencies': sorted(str(x) for x in (r.get_dependencies(p, options) or [])), 'referencers': sorted(str(x) for x in (r.get_referencers(p, options) or [])), 'tags': {}, 'indexed_asset': False}
(out / 'registry.json').write_text(json.dumps({'generated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'packages': rows}, ensure_ascii=False, indent=2), encoding='utf-8')
u.log('RESOURCE_AUDIT_EXTRACTION_OK packages=' + str(len(rows)))
