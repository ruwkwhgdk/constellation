"""One-time user-requested cleanup. Abort on references outside the retired set."""
import unreal,json
from pathlib import Path
P=Path(__file__).resolve().parent;B='/Game/Resources/Characters/PC/player_heroine_new'
r=unreal.AssetRegistryHelpers.get_asset_registry();r.search_all_assets(True)
opt=unreal.AssetRegistryDependencyOptions(include_soft_package_references=True,include_hard_package_references=True,include_searchable_names=True,include_soft_management_references=True,include_hard_management_references=True)
maps=[B+'/Preview/L_player_heroine_new_Run_'+n for n in ['Natural','Polish']]
clips=[B+'/Animations/AS_player_heroine_new_Run_'+n for n in ['Natural','Retarget','Polish']]
targets=set(maps+clips)
for p in targets:
 refs={str(x) for x in (r.get_referencers(p,opt) or [])}
 assert not (refs-targets),(p,refs-targets)
latest=unreal.load_asset(B+'/Animations/AS_player_heroine_new_Run_Soft');mesh=unreal.load_asset(B+'/SK_player_heroine_new_RunPreview')
assert latest and mesh and abs(latest.sequence_length-1)<.001
source=P.parent/'RunSoft/SK_player_heroine_new_RunPreview.fbx'
assert source.is_file()
mesh.get_editor_property('asset_import_data').scripted_add_filename(str(source),0,'')
assert unreal.EditorAssetLibrary.save_loaded_asset(mesh,only_if_is_dirty=False)
deleted=[]
for p in maps+clips:
 if unreal.EditorAssetLibrary.does_asset_exist(p):
  assert unreal.EditorAssetLibrary.delete_asset(p),p
  deleted.append(p)
assert all(not unreal.EditorAssetLibrary.does_asset_exist(p) for p in clips)
assert unreal.EditorAssetLibrary.does_asset_exist(B+'/Animations/AS_player_heroine_new_Walk_Timid')
assert unreal.EditorAssetLibrary.does_asset_exist(B+'/Animations/AS_player_heroine_new_Run_Soft')
(P/'unreal_cleanup_result.json').write_text(json.dumps({'deleted':deleted,'retired_targets':sorted(targets),'remaining_maps':[p for p in maps if unreal.EditorAssetLibrary.does_asset_exist(p)],'mesh_source':str(source),'latest_and_walk_preserved':True},indent=2))
print('LEGACY_ASSETS_REMOVED',len(deleted))
