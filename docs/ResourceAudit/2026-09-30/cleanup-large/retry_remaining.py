"""Retry the two original, unchanged survivors after batch memory references are gone."""
import datetime,hashlib,json,shutil
from pathlib import Path
import unreal as u
root=Path(u.Paths.project_dir()).resolve();out=root/'Saved/ResourceCleanup/20260930-Large'
plan=json.loads((out/'plan.json').read_text());report=json.loads((out/'deletion.json').read_text())
entries={x['package']:x for x in plan['entries']}
expected={'/Game/LuosCaves/Sounds/S_Credits_Loop2','/Game/Resources/Environments/Props/Common/Red_Brick_Wall/T_Red_Brick_Wall_Roughness'}
assert set(report['remaining'])==expected
assert not (out/'deletion_attempt1.json').exists()
shutil.copy2(out/'deletion.json',out/'deletion_attempt1.json')
r=u.AssetRegistryHelpers.get_asset_registry();r.search_all_assets(True);r.scan_paths_synchronous(['/Game'],force_rescan=True)
opts=u.AssetRegistryDependencyOptions(include_soft_package_references=True,include_hard_package_references=True,include_searchable_names=True,include_soft_management_references=True,include_hard_management_references=True)
for p in expected:
    assert hashlib.sha256((root/entries[p]['path']).read_bytes()).hexdigest()==entries[p]['sha256']
    assert not ({str(x) for x in (r.get_referencers(p,opts) or [])}-{p}),p
retry=[]
for p in sorted(expected):
    ok=u.EditorAssetLibrary.delete_asset(p)
    absent=not (root/entries[p]['path']).exists()
    retry.append({'package':p,'api_success':ok,'absent_on_disk':absent})
report['retry']=retry
report['first_batch_api_success']=report['api_success']
report['api_success']=all(x['api_success'] and x['absent_on_disk'] for x in retry)
report['deleted']=sorted(p for p,e in entries.items() if not (root/e['path']).exists())
report['remaining']=sorted(set(entries)-set(report['deleted']))
report['deleted_bytes']=sum(entries[p]['bytes'] for p in report['deleted'])
report['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(out/'deletion.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
assert report['api_success'] and not report['remaining'],report['remaining']
u.log('LARGE_RESOURCE_RETRY_OK '+str(len(report['deleted'])))
