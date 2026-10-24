import unreal as u,json
from pathlib import Path
P=Path(__file__).resolve().parent
reg=u.AssetRegistryHelpers.get_asset_registry();reg.search_all_assets(True)
base='/Game/Constellation/Characters/Enemies/Slime_Normal'
out={}
for n in ['SKM_Slime_Normal','SM_Slime_Normal','SKM_Slime_Normal_CtrlRig','MI_Slime_Normal','MI_Slime_Yellow','T_Slime_Normal','T_Slime_Yellow']:
 p=base+'/'+n
 loaded_refs=u.EditorAssetLibrary.find_package_referencers_for_asset(p,True) if u.EditorAssetLibrary.does_asset_exist(p) else []
 registry_refs=reg.get_referencers(p,u.AssetRegistryDependencyOptions(include_hard_package_references=True,include_soft_package_references=True)) or []
 out[p]=sorted(set(str(x) for x in (loaded_refs or [])) | set(str(x) for x in registry_refs))
(P/'remaining-old-references.json').write_text(json.dumps(out,indent=2))
out={}
for name in ['AM_Slime_Idle','AM_Slime_Attack']:
 path=base+'/Animation/'+name
 if not u.EditorAssetLibrary.does_asset_exist(path):continue
 a=u.load_asset(path)
 out[name]={'length':a.get_play_length(),'slots':str(a.get_editor_property('slot_anim_tracks'))}
(P/'montage-audit.json').write_text(json.dumps(out,indent=2))
