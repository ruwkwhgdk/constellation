import unreal,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;B='/Game/Resources/Characters/PC/player_heroine_new'
a=unreal.load_asset(B+'/Animations/AS_player_heroine_new_Walk_Timid');m=unreal.load_asset(B+'/SK_player_heroine_new_WalkPreview')
a.set_preview_skeletal_mesh(m)
assert unreal.EditorAssetLibrary.save_loaded_asset(a,only_if_is_dirty=False)
lib=unreal.AnimationLibrary
markers=[{'name':str(s.marker_name),'time':s.time} for s in lib.get_animation_sync_markers(a)]
assert len(markers)==2 and abs(a.sequence_length-4/3)<.001
assert m.skeleton==a.get_editor_property('skeleton')
assert all(s.material_interface for s in m.materials)
poses={}
for n in ['root','pelvis','thigh_l','calf_l','foot_l','thigh_r','foot_r','head']:
 poses[n]=[str(lib.get_bone_pose_for_time(a,n,t,False)) for t in [0,1/3,2/3,1,4/3]]
registry=unreal.AssetRegistryHelpers.get_asset_registry()
deps=[str(x) for x in registry.get_dependencies('/Game/Resources/Characters/CommonAnimation/BS_Move',unreal.AssetRegistryDependencyOptions(include_hard_package_references=True))]
assert '/Game/Resources/Characters/CommonAnimation/Walk' in deps
report={'pass':True,'asset':a.get_path_name(),'preview_mesh':m.get_path_name(),'height_cm':m.get_bounds().box_extent.z*2,'skeleton':m.skeleton.get_path_name(),'duration_s':a.sequence_length,'sync_markers':markers,'source':a.get_editor_property('asset_import_data').get_first_filename(),'source_sha256':hashlib.sha256((P/'AS_player_heroine_new_Walk_Timid.fbx').read_bytes()).hexdigest(),'reference_blend_dependencies':deps,'pose_samples':poses}
(P/'unreal_import.json').write_text(json.dumps(report,indent=2));print('WALK_SAVED_ASSETS_VERIFIED')
