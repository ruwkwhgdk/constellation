"""Remove retired review/backup assets only after external reference checks."""
import unreal as u, json
from pathlib import Path
E=u.EditorAssetLibrary; R=u.AssetRegistryHelpers.get_asset_registry(); R.search_all_assets(True)
root='/Game/Environment/StairwellModular'
assets=E.list_assets(root,recursive=True,include_folder=False)
candidates={p.split('.')[0] for p in assets if '/L_Stairwell_Before' in p or p.split('.')[0].endswith('/L_Stairwell_DoorVerification')}
backup='/Game/Blueprints/Character/PC/CameraBackups/BP_Player_Heroine_BeforeStairCamera'
if E.does_asset_exist(backup): candidates.add(backup)
opts=u.AssetRegistryDependencyOptions(include_soft_package_references=True,include_hard_package_references=True,include_searchable_names=False,include_soft_management_references=True,include_hard_management_references=True)
refs={p:[str(x) for x in R.get_referencers(p,opts)] for p in candidates}
# Any reference from a retained package protects the candidate, transitively.
deletable=set(candidates)
while True:
    blocked={p for p in deletable if any(r!=p and r not in deletable for r in refs[p])}
    if not blocked: break
    deletable-=blocked
out=Path(u.Paths.project_dir())/'ArtSource/Stairwell_Modular/Workflow'; out.mkdir(parents=True,exist_ok=True)
report=dict(candidates=sorted(candidates),references=refs,protected=sorted(candidates-deletable),deleted=[],failed=[])
(out/'asset_cleanup.json').write_text(json.dumps(report,indent=2))
for p in sorted(deletable):
    (report['deleted'] if E.delete_asset(p) else report['failed']).append(p)
for p in report['deleted']: assert not E.does_asset_exist(p),p
for p in [root+'/Scene/Maps/L_Stairwell_PlayScale2',root+'/Scene/Maps/L_Stairwell_Reference',root+'/ReviewKit/Maps/L_Stairwell_KitReview','/Game/Blueprints/Character/PC/BP_Player_Heroine']:
    assert E.does_asset_exist(p),p
report['retained_assets']=E.list_assets(root,recursive=True,include_folder=False)
(out/'asset_cleanup.json').write_text(json.dumps(report,indent=2))
u.log('STAIRWELL_ASSET_CLEANUP '+json.dumps({k:v for k,v in report.items() if k in ['deleted','failed','protected']}))
