"""Run only after saved-asset, rendered playback and gameplay gates pass."""
import unreal as u,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=Path(u.Paths.project_dir()).resolve()
for file in ['asset-verification.json','saved-verification.json','playback-report.json']:
 assert json.loads((P/file).read_text())['success'],file
combat=json.loads((ROOT/'Saved/CombatAudit/PlayRuns/38c4924dda034d0cbd794efbcd4b7404/result.json').read_text(encoding='utf-8-sig'))
assert combat['passed']
OLD='/Game/Constellation/Characters/Enemies/Slime_Normal';NEW='/Game/Constellation/Characters/Enemies/Slime_Liquid'
reg=u.AssetRegistryHelpers.get_asset_registry();reg.search_all_assets(True)
opts=u.AssetRegistryDependencyOptions(include_hard_package_references=True,include_soft_package_references=True)
report=json.loads((P/'cleanup-report.json').read_text()) if (P/'cleanup-report.json').exists() else {'deleted':[],'replaced':[],'remaining':{}}
def checkpoint():(P/'cleanup-report.json').write_text(json.dumps(report,indent=2))
def refs(path):return sorted(set(str(x) for x in reg.get_referencers(path,opts)) | set(str(x) for x in u.EditorAssetLibrary.find_package_referencers_for_asset(path,True)))
def remove(path):
 if not u.EditorAssetLibrary.does_asset_exist(path):return
 remaining=refs(path)
 assert not remaining,(path,remaining)
 obj=u.load_asset(path,follow_redirectors=False)
 assert obj and obj.get_path_name().split('.')[0]==path,(path,str(obj))
 assert u.EditorAssetLibrary.delete_loaded_asset(obj),path
 report['deleted'].append(path)
 checkpoint()
def consolidate(old,new):
 if not u.EditorAssetLibrary.does_asset_exist(old):return
 a=u.load_asset(old)
 if not a:return
 target=u.load_asset(new);assert target
 before=refs(old)
 referencers=[u.load_asset(p) for p in before]
 referencers=[o for o in referencers if o]
 old_object=u.SoftObjectPath(old+'.'+old.rsplit('/',1)[1])
 new_object=u.SoftObjectPath(new+'.'+new.rsplit('/',1)[1])
 u.AssetToolsHelpers.get_asset_tools().rename_referencing_soft_object_paths([o.get_outermost() for o in referencers],{old_object:new_object})
 for o in referencers:
  if isinstance(o,u.AnimSequence) and isinstance(target,u.SkeletalMesh):
   o.set_retarget_source_asset(target);o.set_preview_skeletal_mesh(target)
  if isinstance(o,u.MaterialInterface) and isinstance(target,u.StaticMesh):
   o.set_editor_property('preview_mesh',u.SoftObjectPath(new+'.'+new.rsplit('/',1)[1]))
  u.EditorAssetLibrary.save_loaded_asset(o,False)
 if a!=target:assert u.EditorAssetLibrary.consolidate_assets(target,[a]),old
 report['replaced'].append({'from':old,'to':new,'previous_referencers':before})
 checkpoint()
 # Engine consolidation saves references and leaves a redirector. Remove it only
 # once the registry confirms no surviving hard or soft references.
 if u.EditorAssetLibrary.does_asset_exist(old):remove(old)
remove(OLD+'/SKM_Slime_Normal_CtrlRig')
consolidate(OLD+'/SKM_Slime_Normal',NEW+'/SKM_Slime_Liquid')
consolidate(OLD+'/SM_Slime_Normal',NEW+'/SM_Slime_Liquid')
consolidate(OLD+'/Animation/AM_Slime_Idle',NEW+'/AM_Slime_Liquid_Idle')
for name in ['MI_Slime_Normal','MI_Slime_Yellow','T_Slime_Normal','T_Slime_Yellow']:
 remove(OLD+'/'+name)
for name in ['SKM_Slime_Liquid_Anim']:
 p=NEW+'/'+name
 if u.EditorAssetLibrary.does_asset_exist(p) and not refs(p):remove(p)
for name in ['SKM_Slime_Normal','SM_Slime_Normal','SKM_Slime_Normal_CtrlRig','MI_Slime_Normal','MI_Slime_Yellow','T_Slime_Normal','T_Slime_Yellow','Animation/AM_Slime_Idle']:
 path=OLD+'/'+name
 assert not u.EditorAssetLibrary.does_asset_exist(path),path
 report['remaining'][path]=refs(path)
 assert not report['remaining'][path]
report['success']=True
(P/'cleanup-report.json').write_text(json.dumps(report,indent=2))
