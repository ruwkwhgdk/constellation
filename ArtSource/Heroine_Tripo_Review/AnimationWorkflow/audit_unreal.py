import unreal,json
from pathlib import Path
P=Path(__file__).resolve().parent;B='/Game/Resources/Characters/PC/player_heroine_new'
registry=unreal.AssetRegistryHelpers.get_asset_registry();registry.search_all_assets(True)
options=unreal.AssetRegistryDependencyOptions(include_soft_package_references=True,include_hard_package_references=True,include_searchable_names=True,include_soft_management_references=True,include_hard_management_references=True)
names=['Natural','Retarget','Polish']
targets=[B+'/Animations/AS_player_heroine_new_Run_'+n for n in names]
targets += [B+'/Preview/L_player_heroine_new_Run_'+n for n in names]
result={p:{'exists':unreal.EditorAssetLibrary.does_asset_exist(p),'referencers':[str(r) for r in (registry.get_referencers(p,options) or [])]} for p in targets}
(P/'unreal_cleanup_audit.json').write_text(json.dumps(result,indent=2))
print('CLEANUP_AUDIT',json.dumps(result))
