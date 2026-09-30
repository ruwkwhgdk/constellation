import unreal,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
B='/Game/Constellation/Characters/Heroine/Refined'
skel=unreal.load_asset(B+'/SKEL_player_heroine_new')
canonical=unreal.load_asset(B+'/SK_player_heroine_new')
preview=unreal.load_asset(B+'/SK_player_heroine_new_RunPreview')
opt=unreal.FbxImportUI();opt.import_mesh=False;opt.import_as_skeletal=True;opt.import_animations=True;opt.mesh_type_to_import=unreal.FBXImportType.FBXIT_ANIMATION;opt.automated_import_should_detect_type=False;opt.skeleton=skel;opt.import_materials=False;opt.import_textures=False;opt.create_physics_asset=False
opt.anim_sequence_import_data.import_uniform_scale=100.0
opt.anim_sequence_import_data.set_editor_property('use_default_sample_rate',True)
task=unreal.AssetImportTask();task.filename=str(P/'AS_player_heroine_new_Run_Soft.fbx');task.destination_path=B+'/Animations';task.destination_name='AS_player_heroine_new_Run_Soft';task.automated=True;task.replace_existing=True;task.save=True;task.options=opt;task.factory=unreal.FbxFactory()
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
a=unreal.load_asset(B+'/Animations/AS_player_heroine_new_Run_Soft');assert a and a.get_editor_property('skeleton')==skel
a.set_editor_property('enable_root_motion',False)
a.set_preview_skeletal_mesh(preview)
lib=unreal.AnimationLibrary
if not lib.is_valid_anim_notify_track_name(a,'Default'):lib.add_animation_notify_track(a,'Default')
lib.remove_all_animation_sync_markers(a)
lib.add_animation_sync_marker(a,'LeftPlant',0.375,'Default')
lib.add_animation_sync_marker(a,'RightPlant',0.875,'Default')
assert len(lib.get_animation_sync_markers(a))==2
unreal.EditorAssetLibrary.set_metadata_tag(a,'SuggestedSpeedCmPerSecond','168')
unreal.EditorAssetLibrary.set_metadata_tag(a,'ReferenceAnimation','/Game/Constellation/Characters/Shared/Animations/Run')
unreal.EditorAssetLibrary.set_metadata_tag(a,'Style','Source-retargeted compact run; corrected garment follow; planted toe stabilization; in-place')
assert unreal.EditorAssetLibrary.save_loaded_asset(a,only_if_is_dirty=False)
bs=unreal.load_asset('/Game/Constellation/Characters/Shared/Animations/BS_Move')
registry=unreal.AssetRegistryHelpers.get_asset_registry()
samples=[str(x) for x in registry.get_dependencies('/Game/Constellation/Characters/Shared/Animations/BS_Move',unreal.AssetRegistryDependencyOptions(include_hard_package_references=True))]
report={'asset':a.get_path_name(),'skeleton':a.get_editor_property('skeleton').get_path_name(),'duration_s':a.sequence_length,'source':a.get_editor_property('asset_import_data').get_first_filename(),'source_sha256':hashlib.sha256((P/'AS_player_heroine_new_Run_Soft.fbx').read_bytes()).hexdigest(),'reference_blend_samples':samples}
assert abs(a.sequence_length-1.0)<.001
report['preview_mesh']=preview.get_path_name();report['suggested_speed_cm_s']=168;report['pass']=True;(P/'unreal_import.json').write_text(json.dumps(report,indent=2));print('WALK_IMPORTED',report)
