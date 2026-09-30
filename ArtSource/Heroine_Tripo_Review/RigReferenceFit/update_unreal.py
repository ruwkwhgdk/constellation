import unreal,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;B='/Game/Constellation/Characters/Heroine/Refined';N='player_heroine_new'
asset=unreal.EditorAssetLibrary;at=unreal.AssetToolsHelpers.get_asset_tools()
mesh=unreal.load_asset(B+'/SK_'+N);skel=mesh.skeleton
old_slots={str(s.material_slot_name):s.material_interface for s in mesh.materials}
old_import=mesh.get_editor_property('asset_import_data')
old_import.set_editor_property('import_uniform_scale',100.0)
old_import.set_editor_property('update_skeleton_reference_pose',True)
old_import.scripted_add_filename(str(P/'Delivery/Heroine_Skeletal.fbx'),0,'')
opt=unreal.FbxImportUI();opt.import_as_skeletal=True;opt.import_mesh=True;opt.import_animations=False;opt.import_materials=False;opt.import_textures=False;opt.create_physics_asset=False;opt.skeleton=skel
opt.mesh_type_to_import=unreal.FBXImportType.FBXIT_SKELETAL_MESH;opt.automated_import_should_detect_type=False
opt.skeletal_mesh_import_data.import_uniform_scale=100.0;opt.skeletal_mesh_import_data.set_editor_property('update_skeleton_reference_pose',True)
opt.skeletal_mesh_import_data.normal_import_method=unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
def import_file(source,dest,name,options):
 task=unreal.AssetImportTask();task.filename=str(source);task.destination_path=dest;task.destination_name=name;task.automated=True;task.replace_existing=True;task.replace_existing_settings=True;task.save=True;task.options=options;task.factory=unreal.FbxFactory()
 at.import_asset_tasks([task]);return list(task.imported_object_paths)
paths=import_file(P/'Delivery/Heroine_Skeletal.fbx',B,'SK_'+N,opt)
mesh=unreal.load_asset(B+'/SK_'+N)
slots=list(mesh.materials)
for slot in slots:
 assert str(slot.material_slot_name) in old_slots
 slot.material_interface=old_slots[str(slot.material_slot_name)]
mesh.set_editor_property('materials',slots)
assert asset.save_loaded_asset(mesh,only_if_is_dirty=False);assert asset.save_loaded_asset(skel,only_if_is_dirty=False)
anim=unreal.load_asset(B+'/Animations/AS_'+N+'_PreviewRelaxed')
if anim:
 data=anim.get_editor_property('asset_import_data');data.set_editor_property('import_uniform_scale',100.0);data.scripted_add_filename(str(P/'Delivery/PreviewRelaxed.fbx'),0,'')
opt=unreal.FbxImportUI();opt.import_mesh=False;opt.import_as_skeletal=True;opt.import_animations=True;opt.mesh_type_to_import=unreal.FBXImportType.FBXIT_ANIMATION;opt.automated_import_should_detect_type=False;opt.skeleton=skel;opt.import_materials=False;opt.import_textures=False;opt.create_physics_asset=False;opt.anim_sequence_import_data.import_uniform_scale=100.0
paths+=import_file(P/'Delivery/PreviewRelaxed.fbx',B+'/Animations','AS_'+N+'_PreviewRelaxed',opt)
assert asset.save_directory(B,only_if_is_dirty=True,recursive=True)
ref=unreal.load_asset('/Game/Constellation/Characters/Heroine/Base/Player_Heroine')
report={'mesh':mesh.get_path_name(),'skeleton':mesh.skeleton.get_path_name(),'height_cm':mesh.get_bounds().box_extent.z*2,'materials':len(slots),'source':mesh.get_editor_property('asset_import_data').get_first_filename(),'source_sha256':hashlib.sha256((P/'Delivery/Heroine_Skeletal.fbx').read_bytes()).hexdigest(),'reference_source':ref.get_editor_property('asset_import_data').get_first_filename(),'imported':paths}
assert abs(report['height_cm']-160)<.1 and mesh.skeleton==skel and all(s.material_interface for s in slots)
report['pass']=True;(P/'unreal_update.json').write_text(json.dumps(report,indent=2));print('REFERENCE_FIT_IMPORTED',json.dumps(report))
