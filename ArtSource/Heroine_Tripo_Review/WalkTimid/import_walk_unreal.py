import unreal,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
B='/Game/Constellation/Characters/Heroine/Refined'
skel=unreal.load_asset(B+'/SKEL_player_heroine_new')
canonical=unreal.load_asset(B+'/SK_player_heroine_new')
mo=unreal.FbxImportUI();mo.import_as_skeletal=True;mo.import_mesh=True;mo.import_animations=False;mo.import_materials=False;mo.import_textures=False;mo.create_physics_asset=False;mo.skeleton=skel;mo.mesh_type_to_import=unreal.FBXImportType.FBXIT_SKELETAL_MESH;mo.automated_import_should_detect_type=False
mo.skeletal_mesh_import_data.import_uniform_scale=100.0
mo.skeletal_mesh_import_data.set_editor_property('update_skeleton_reference_pose',False)
mo.skeletal_mesh_import_data.normal_import_method=unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
mt=unreal.AssetImportTask();mt.filename=str(P/'SK_player_heroine_new_WalkPreview.fbx');mt.destination_path=B;mt.destination_name='SK_player_heroine_new_WalkPreview';mt.automated=True;mt.replace_existing=True;mt.save=True;mt.options=mo;mt.factory=unreal.FbxFactory()
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([mt])
preview=unreal.load_asset(B+'/SK_player_heroine_new_WalkPreview')
slots={str(s.material_slot_name):s.material_interface for s in canonical.materials};items=list(preview.materials)
for item in items:
 name=str(item.material_slot_name)
 if name not in slots and name.endswith('_001'):name=name[:-4]
 assert name in slots,(name,list(slots))
 item.material_interface=slots[name];item.material_slot_name=name
preview.set_editor_property('materials',items);preview.set_editor_property('physics_asset',canonical.get_editor_property('physics_asset'))
assert unreal.EditorAssetLibrary.save_loaded_asset(preview,only_if_is_dirty=False)
opt=unreal.FbxImportUI();opt.import_mesh=False;opt.import_as_skeletal=True;opt.import_animations=True;opt.mesh_type_to_import=unreal.FBXImportType.FBXIT_ANIMATION;opt.automated_import_should_detect_type=False;opt.skeleton=skel;opt.import_materials=False;opt.import_textures=False;opt.create_physics_asset=False
opt.anim_sequence_import_data.import_uniform_scale=100.0
opt.anim_sequence_import_data.set_editor_property('use_default_sample_rate',True)
task=unreal.AssetImportTask();task.filename=str(P/'AS_player_heroine_new_Walk_Timid.fbx');task.destination_path=B+'/Animations';task.destination_name='AS_player_heroine_new_Walk_Timid';task.automated=True;task.replace_existing=True;task.save=True;task.options=opt;task.factory=unreal.FbxFactory()
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
a=unreal.load_asset(B+'/Animations/AS_player_heroine_new_Walk_Timid');assert a and a.get_editor_property('skeleton')==skel
a.set_editor_property('enable_root_motion',False)
a.set_preview_skeletal_mesh(preview)
lib=unreal.AnimationLibrary
if not lib.is_valid_anim_notify_track_name(a,'Default'):lib.add_animation_notify_track(a,'Default')
lib.remove_all_animation_sync_markers(a)
lib.add_animation_sync_marker(a,'LeftPlant',0.0,'Default')
lib.add_animation_sync_marker(a,'RightPlant',2/3,'Default')
assert len(lib.get_animation_sync_markers(a))==2
unreal.EditorAssetLibrary.set_metadata_tag(a,'SuggestedSpeedCmPerSecond','48')
unreal.EditorAssetLibrary.set_metadata_tag(a,'ReferenceAnimation','/Game/Constellation/Characters/Shared/Animations/Walk')
unreal.EditorAssetLibrary.set_metadata_tag(a,'Style','Timid careful walk; short stride; in-place')
assert unreal.EditorAssetLibrary.save_loaded_asset(a,only_if_is_dirty=False)
bs=unreal.load_asset('/Game/Constellation/Characters/Shared/Animations/BS_Move')
registry=unreal.AssetRegistryHelpers.get_asset_registry()
samples=[str(x) for x in registry.get_dependencies('/Game/Constellation/Characters/Shared/Animations/BS_Move',unreal.AssetRegistryDependencyOptions(include_hard_package_references=True))]
report={'asset':a.get_path_name(),'skeleton':a.get_editor_property('skeleton').get_path_name(),'duration_s':a.sequence_length,'source':a.get_editor_property('asset_import_data').get_first_filename(),'source_sha256':hashlib.sha256((P/'AS_player_heroine_new_Walk_Timid.fbx').read_bytes()).hexdigest(),'reference_blend_samples':samples}
assert abs(a.sequence_length-4/3)<.001
report['pass']=True;(P/'unreal_import.json').write_text(json.dumps(report,indent=2));print('WALK_IMPORTED',report)
