"""Delete only the explicit, recoverable, freshly unreferenced package manifest."""
import datetime, hashlib, json
from pathlib import Path
import unreal as u

ROOT=Path(u.Paths.project_dir()).resolve()
OUT=ROOT/'Saved/ResourceCleanup/20260930-Large'
plan=json.loads((OUT/'plan.json').read_text(encoding='utf-8'))
entries={x['package']:x for x in plan['entries']}; chosen=set(entries)
assert len(chosen)==232 and plan['local_lfs_recovery_verified']
assert not (OUT/'deletion.json').exists(), 'Do not repeat a destructive batch; inspect its result first.'
r=u.AssetRegistryHelpers.get_asset_registry();r.search_all_assets(True);r.scan_paths_synchronous(['/Game'],force_rescan=True)
opts=u.AssetRegistryDependencyOptions(include_soft_package_references=True,include_hard_package_references=True,include_searchable_names=True,include_soft_management_references=True,include_hard_management_references=True)
assets={}
for a in r.get_assets_by_path('/Game',recursive=True,include_only_on_disk_assets=True):
    assets.setdefault(str(a.package_name),[]).append(a)
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
    return h.hexdigest()
for p,row in entries.items():
    f=(ROOT/row['path']).resolve()
    assert f.is_relative_to(ROOT/'Content') and f.suffix=='.uasset'
    assert p in assets and not p.startswith(('/Game/Environment/','/Game/__External','/Game/Resources/Characters/PC/'))
    assert digest(f)==row['sha256'], 'Candidate modified: '+p
    external={str(x) for x in (r.get_referencers(p,opts) or [])}-chosen-{p}
    assert not external,(p,external)
# Verify the dependency direction independently against every retained package.
for p in assets.keys()-chosen:
    assert not ({str(x) for x in (r.get_dependencies(p,opts) or [])}&chosen), 'Retained dependency: '+p
loaded=[];resolved=[]
for p in sorted(chosen):
    for a in assets[p]:
        obj=a.get_asset()
        assert obj is not None,'Load failed: '+p
        actual=obj.get_outermost().get_name()
        # Never follow a redirector into an unselected destination asset.
        assert actual==p,(p,actual)
        loaded.append(obj);resolved.append(obj.get_path_name())
u.SystemLibrary.collect_garbage()
# Loading may discover more dependencies. Recheck before the first mutation.
for p in chosen:
    assert not ({str(x) for x in (r.get_referencers(p,opts) or [])}-chosen-{p}),p
report={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'planned_count':len(chosen),'planned_bytes':sum(x['bytes'] for x in entries.values()),'loaded_objects':resolved,'outside_referencers':0,'deleted':[],'remaining':[],'head':plan['head']}
(OUT/'deletion.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
ok=u.EditorAssetLibrary.delete_loaded_assets(loaded)
report['api_success']=ok
for p,row in entries.items():
    (report['remaining'] if (ROOT/row['path']).exists() else report['deleted']).append(p)
report['deleted_bytes']=sum(entries[p]['bytes'] for p in report['deleted'])
report['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(OUT/'deletion.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
assert ok and not report['remaining'],report['remaining']
u.log('LARGE_RESOURCE_CLEANUP_OK '+str(len(report['deleted']))+' packages '+str(report['deleted_bytes'])+' bytes')
