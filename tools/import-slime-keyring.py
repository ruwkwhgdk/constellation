import unreal as u
import json
from pathlib import Path
R=Path(u.Paths.project_dir()); S=R/'ArtSource/SchoolOpening/slime_keyring/Source'; O=R/'Saved/SlimeKeyring'; O.mkdir(exist_ok=True)
D='/Game/Constellation/Environments/School/Props/slime_keyring'
E=u.EditorAssetLibrary; AT=u.AssetToolsHelpers.get_asset_tools(); M=u.MaterialEditingLibrary
u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
def imp(file,name,options=None):
 if E.does_asset_exist(D+'/'+name):return E.load_asset(D+'/'+name)
 t=u.AssetImportTask(); t.filename=str(file); t.destination_path=D; t.destination_name=name; t.automated=True; t.save=True; t.replace_existing=False
 if options:t.options=options;t.factory=u.FbxFactory()
 AT.import_asset_tasks([t]); assert t.imported_object_paths; return E.load_asset(t.imported_object_paths[0])
textures={}
for suffix,glob in [('BaseColor','*basecolor.*'),('Normal','*normal.*'),('Roughness','*roughness.*'),('Metallic','*metallic.*')]:
 tex=imp(next(S.rglob(glob)),'T_slime_keyring_'+suffix)
 if suffix!='BaseColor':tex.set_editor_property('srgb',False);tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_NORMALMAP if suffix=='Normal' else u.TextureCompressionSettings.TC_MASKS)
 E.save_loaded_asset(tex,False); textures[suffix]=tex
mi=E.load_asset(D+'/MI_slime_keyring') if E.does_asset_exist(D+'/MI_slime_keyring') else AT.create_asset('MI_slime_keyring',D,u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew());assert mi
M.set_material_instance_parent(mi,u.load_asset('/Game/Constellation/MaterialLibrary/Materials/M_Base_PBR'))
for param,key in [('BaseColor','BaseColor'),('Normal','Normal'),('Roughness','Roughness'),('Metalic','Metallic')]:
 M.set_material_instance_texture_parameter_value(mi,param,textures[key])
 assert M.get_material_instance_texture_parameter_value(mi,param)==textures[key],param
M.update_material_instance(mi);E.save_loaded_asset(mi,False)
opts=u.FbxImportUI();opts.import_mesh=True;opts.import_as_skeletal=False;opts.import_materials=False;opts.import_textures=False;opts.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
opts.static_mesh_import_data.combine_meshes=True;opts.static_mesh_import_data.auto_generate_collision=False;opts.static_mesh_import_data.convert_scene_unit=True
mesh=imp(next(S.glob('*.fbx')),'SM_slime_keyring',opts)
for i in range(len(mesh.get_editor_property('static_materials'))):mesh.set_material(i,mi)
E.save_loaded_asset(mesh,False)
b=mesh.get_bounding_box();report={'mesh':mesh.get_path_name(),'min':[b.min.x,b.min.y,b.min.z],'max':[b.max.x,b.max.y,b.max.z]}
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
A=u.get_editor_subsystem(u.EditorActorSubsystem);actors=[]
for a in A.get_all_level_actors():
 if 'Charm' in a.get_actor_label() or a.get_actor_label()=='S0_LockerDoor':
  origin,extent=a.get_actor_bounds(False);parent=a.get_attach_parent_actor()
  actors.append(dict(label=a.get_actor_label(),path=a.get_path_name(),transform=str(a.get_actor_transform()),bounds=[str(origin),str(extent)],parent=parent.get_actor_label() if parent else None))
report['actors']=actors;(O/'import.json').write_text(json.dumps(report,indent=2),encoding='utf8');u.log('SLIME_IMPORTED '+str(report))
