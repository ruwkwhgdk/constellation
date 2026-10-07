"""Upgrade saved Scene Director controls without modifying original Level Sequences.
Run with the editor closed via UnrealEditor-Cmd -ExecutePythonScript or ExecCmds=py.
Backups and a validation report are written under Saved/SceneAuthoringRefinement.
"""
import unreal as u
import json,shutil,hashlib,traceback,re
from pathlib import Path
from datetime import datetime
root=Path(u.Paths.project_dir()).resolve()
out=root/'Saved/SceneAuthoringRefinement'
backup=out/('Backup-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
registry=u.AssetRegistryHelpers.get_asset_registry()
registry.search_all_assets(True)
items=registry.get_assets_by_class(u.TopLevelAssetPath('/Script/SceneDirectorRuntime','SceneDirectorAsset'),True)
report={'assets':[],'success':False}
try:
 for item in items:
  asset=item.get_asset()
  if not asset:continue
  package=str(item.package_name)
  if not package.startswith('/Game/'):continue
  local=root/'Content'/Path(package.removeprefix('/Game/')+'.uasset')
  if local.exists():
   target=backup/local.relative_to(root);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(local,target)
  changed=asset.upgrade_control_nodes()
  if not changed:continue
  result=u.SceneDirectorLibrary.compile_authoring_events(asset)
  assert re.fullmatch(r"\d+ events, \d+ nodes compiled",str(result)) and not asset.get_editor_property("needs_compile"),(package,result)
  assert u.EditorAssetLibrary.save_loaded_asset(asset,False),package
  report['assets'].append({'path':package,'compilation':str(result)})
 baseline=root/'Saved/SceneEventIntegration/sequences.json'
 if baseline.exists():
  originals=json.loads(baseline.read_text(encoding='utf-8-sig'))
  assert all(hashlib.sha256((root/'Content'/Path(e['path'].removeprefix('/Game/')+'.uasset')).read_bytes()).hexdigest()==e['sha256'] for e in originals),'Original sequence changed'
  report['original_sequences_unchanged']=len(originals)
 report['success']=True
except Exception:report['error']=traceback.format_exc()
out.mkdir(parents=True,exist_ok=True)
(out/'migration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
u.log('SCENE_AUTHORING_UPGRADE '+json.dumps(report,ensure_ascii=False))
u.SystemLibrary.quit_editor()
