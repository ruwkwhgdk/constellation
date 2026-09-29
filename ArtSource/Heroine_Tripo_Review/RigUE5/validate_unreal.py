import unreal,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
t=unreal.AssetImportTask();t.filename=str(P/'Delivery/Heroine_Skeletal.fbx');t.destination_path='/Game/RigValidationFinal';t.destination_name='SK_Heroine';t.automated=True;t.replace_existing=True;t.save=True
opt=unreal.FbxImportUI();opt.import_as_skeletal=True;opt.mesh_type_to_import=unreal.FBXImportType.FBXIT_SKELETAL_MESH;opt.automated_import_should_detect_type=False;opt.import_materials=False;opt.import_textures=False;opt.import_animations=False;opt.create_physics_asset=False
opt.skeletal_mesh_import_data.import_uniform_scale=1.0;opt.skeletal_mesh_import_data.convert_scene=True;opt.skeletal_mesh_import_data.convert_scene_unit=True
t.options=opt
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
result={'fbx_sha256':hashlib.sha256(Path(t.filename).read_bytes()).hexdigest(),'imported_paths':list(t.imported_object_paths),'objects':[]}
for path in t.imported_object_paths:
 o=unreal.load_asset(path)
 data={'path':path,'class':o.get_class().get_name()}
 if isinstance(o,unreal.SkeletalMesh):
  b=o.get_bounds();data['bounds_origin']=str(b.origin);data['bounds_extent']=str(b.box_extent);data['height_cm']=b.box_extent.z*2
  data['skeleton']=o.skeleton.get_path_name()
 result['objects'].append(data)
result['pass']=any(o['class']=='SkeletalMesh' and abs(o.get('height_cm',0)-160)<1 for o in result['objects'])
(P/'Delivery/unreal_validation.json').write_text(json.dumps(result,indent=2))
print('HEROINE_IMPORT_VALIDATION',json.dumps(result))
