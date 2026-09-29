"""Read-only registry audit before environment cleanup; includes hard/soft references."""
import unreal as u,json
from pathlib import Path
root=Path(u.Paths.project_dir());out=root/'ArtSource/OvergrownHall/Workflow';out.mkdir(parents=True,exist_ok=True)
R=u.AssetRegistryHelpers.get_asset_registry();R.search_all_assets(True)
O=u.AssetRegistryDependencyOptions(include_soft_package_references=True,include_hard_package_references=True,include_searchable_names=False,include_soft_management_references=True,include_hard_management_references=True)
assets={str(a.package_name):a for a in R.get_assets_by_path('/Game/Environment',recursive=True)}
rows={p:dict(dependencies=[str(x) for x in R.get_dependencies(p,O)],referencers=[str(x) for x in R.get_referencers(p,O)]) for p in assets}
main='/Game/Environment/OvergrownHall/TripoFull/Maps/L_OvergrownHall_TripoFull';seen=set();pending=[main]
while pending:
    p=pending.pop()
    if p in seen:continue
    seen.add(p)
    pending.extend(str(x) for x in R.get_dependencies(p,O) if str(x).startswith('/Game/'))
(out/'registry_audit.json').write_text(json.dumps(dict(assets=rows,final_map_closure=sorted(seen)),indent=2))
u.log('ENVIRONMENT_RELEASE_AUDIT_OK '+str(len(rows)))
