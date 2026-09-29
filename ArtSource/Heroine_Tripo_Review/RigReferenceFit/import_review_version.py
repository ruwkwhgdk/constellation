import unreal,json
from pathlib import Path
P=Path(__file__).resolve().parent
OLD='/Game/Resources/Characters/PC/player_heroine_new';B=OLD+'/ReferenceFit';N='player_heroine_new_ReferenceFit'
asset=unreal.EditorAssetLibrary;at=unreal.AssetToolsHelpers.get_asset_tools()
source_mesh=unreal.load_asset(OLD+'/SK_player_heroine_new');materials={str(s.material_slot_name):s.material_interface for s in source_mesh.materials}
def imp(file,path,name,opt):
 t=unreal.AssetImportTask();t.filename=str(file);t.destination_path=path;t.destination_name=name;t.automated=True;t.replace_existing=True;t.save=True;t.options=opt;t.factory=unreal.FbxFactory();at.import_asset_tasks([t]);return list(t.imported_object_paths)
opt=unreal.FbxImportUI();opt.import_as_skeletal=True;opt.import_mesh=True;opt.import_animations=False;opt.import_materials=False;opt.import_textures=False;opt.create_physics_asset=False;opt.mesh_type_to_import=unreal.FBXImportType.FBXIT_SKELETAL_MESH;opt.automated_import_should_detect_type=False
opt.skeletal_mesh_import_data.import_uniform_scale=100.0;opt.skeletal_mesh_import_data.normal_import_method=unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
mesh=unreal.load_asset(B+'/SK_'+N)
if not mesh:imp(P/'Delivery/Heroine_Skeletal.fbx',B,'SK_'+N,opt);mesh=unreal.load_asset(B+'/SK_'+N)
assert mesh and abs(mesh.get_bounds().box_extent.z*2-160)<.1
skel=mesh.skeleton
if skel.get_name()!='SKEL_'+N:assert asset.rename_loaded_asset(skel,B+'/SKEL_'+N)
slots=list(mesh.materials)
for s in slots:s.material_interface=materials[str(s.material_slot_name)]
mesh.set_editor_property('materials',slots)
helper=unreal.get_default_object(unreal.load_class(None,'/Script/PhysicsToolsets.PhysicsAssetToolset'))
phys=mesh.get_editor_property('physics_asset') or helper.call_method('CreateFromMesh',args=(B+'/SK_'+N,True))
assert phys
if phys.get_name()!='PHYS_'+N:assert asset.rename_loaded_asset(phys,B+'/PHYS_'+N)
mesh.set_editor_property('physics_asset',phys)
for a in [mesh,skel,phys]:assert asset.save_loaded_asset(a,only_if_is_dirty=False)
opt=unreal.FbxImportUI();opt.import_mesh=False;opt.import_as_skeletal=True;opt.import_animations=True;opt.mesh_type_to_import=unreal.FBXImportType.FBXIT_ANIMATION;opt.automated_import_should_detect_type=False;opt.skeleton=skel;opt.import_materials=False;opt.import_textures=False;opt.create_physics_asset=False;opt.anim_sequence_import_data.import_uniform_scale=100.0
anim=unreal.load_asset(B+'/AS_'+N+'_PreviewRelaxed')
if not anim:
 paths=imp(P/'Delivery/PreviewRelaxed.fbx',B,'AS_'+N+'_PreviewRelaxed',opt)
 anim=next(unreal.load_asset(p) for p in paths if isinstance(unreal.load_asset(p),unreal.AnimSequence))
 if anim.get_name()!='AS_'+N+'_PreviewRelaxed':assert asset.rename_loaded_asset(anim,B+'/AS_'+N+'_PreviewRelaxed')
assert asset.save_loaded_asset(anim,only_if_is_dirty=False)
(P/'review_import.json').write_text(json.dumps({'mesh':mesh.get_path_name(),'skeleton':skel.get_path_name(),'animation':anim.get_path_name(),'height_cm':mesh.get_bounds().box_extent.z*2,'pass':True},indent=2))
