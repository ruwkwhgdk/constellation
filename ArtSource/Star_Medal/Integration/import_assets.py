import unreal as u, json
from pathlib import Path
P=Path(u.Paths.project_dir())/'ArtSource/Star_Medal'
D='/Game/Constellation/Environments/Shared/Props/Star_Medal'
E=u.EditorAssetLibrary; AT=u.AssetToolsHelpers.get_asset_tools(); M=u.MaterialEditingLibrary
u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
def imp(file,name,options=None):
 t=u.AssetImportTask();t.filename=str(file);t.destination_path=D;t.destination_name=name;t.automated=True;t.save=True;t.replace_existing=True
 if options:t.options=options;t.factory=u.FbxFactory()
 AT.import_asset_tasks([t]);assert t.imported_object_paths,name
 return E.load_asset(D+'/'+name)
textures={}
for suffix,pattern in [('BaseColor','*basecolor.*'),('Normal','*normal.*'),('Roughness','*roughness.*'),('Metallic','*metallic.*')]:
 tex=imp(next((P/'Source').rglob(pattern)),'T_Star_Medal_'+suffix)
 if suffix!='BaseColor':
  tex.set_editor_property('srgb',False)
  tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_NORMALMAP if suffix=='Normal' else u.TextureCompressionSettings.TC_MASKS)
 E.save_loaded_asset(tex,False);textures[suffix]=tex
mi=E.load_asset(D+'/MI_Star_Medal') if E.does_asset_exist(D+'/MI_Star_Medal') else AT.create_asset('MI_Star_Medal',D,u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
M.set_material_instance_parent(mi,u.load_asset('/Game/Constellation/MaterialLibrary/Materials/M_Base_PBR'))
for param,key in [('BaseColor','BaseColor'),('Normal','Normal'),('Roughness','Roughness'),('Metalic','Metallic')]:
 M.set_material_instance_texture_parameter_value(mi,param,textures[key])
 assert M.get_material_instance_texture_parameter_value(mi,param)==textures[key]
M.update_material_instance(mi);E.save_loaded_asset(mi,False)
opts=u.FbxImportUI();opts.import_mesh=True;opts.import_as_skeletal=False;opts.import_materials=False;opts.import_textures=False;opts.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH;opts.automated_import_should_detect_type=False
opts.static_mesh_import_data.combine_meshes=True;opts.static_mesh_import_data.auto_generate_collision=False;opts.static_mesh_import_data.convert_scene_unit=True
mesh=imp(next((P/'Source').glob('*.fbx')),'SM_Star_Medal',opts)
for i in range(len(mesh.static_materials)):mesh.set_material(i,mi)
E.save_loaded_asset(mesh,False)
b=mesh.get_bounding_box()
data={'mesh':mesh.get_path_name(),'min':[b.min.x,b.min.y,b.min.z],'max':[b.max.x,b.max.y,b.max.z]}
(P/'Integration/import.json').write_text(json.dumps(data,indent=2))
u.log('STAR_MEDAL_IMPORTED '+str(data))
