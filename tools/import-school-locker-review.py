"""Import the approved locker redesign into review assets, without editing gameplay assets."""
import unreal as u,json
from pathlib import Path
R=Path(u.Paths.project_dir()).resolve();SRC=R/'ArtSource/SchoolLocker';D='/Game/Constellation/Review/SchoolLocker';AT=u.AssetToolsHelpers.get_asset_tools();E=u.EditorAssetLibrary;M=u.MaterialEditingLibrary
APPLY='LockerApply' in u.SystemLibrary.get_command_line()
if APPLY:
 D='/Game/Constellation/Environments/School/Props/SM_Locker'
 import shutil
 backup=R/'Saved/SchoolLocker/Backup-before-apply';backup.mkdir(exist_ok=True)
 for rel in ['Content/Constellation/Environments/School/Props/SM_Locker','Content/SceneDirector/School/S0']:
  dest=backup/Path(rel).name
  if not dest.exists():shutil.copytree(R/rel,dest)
 for rel in ['Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap','Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool_BuiltData.uasset','Content/SceneDirector/School/DA_S0_Opening.uasset']:
  dest=backup/Path(rel).name
  if not dest.exists():shutil.copy2(R/rel,dest)
w=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();u.SystemLibrary.execute_console_command(w,'Interchange.FeatureFlags.Import.FBX 0')
def task(f,d,opts=None):
 t=u.AssetImportTask();t.filename=str(f);t.destination_path=d;t.automated=True;t.save=True;t.replace_existing=True;t.replace_existing_settings=True
 if opts:t.options=opts;t.factory=u.FbxFactory()
 AT.import_asset_tasks([t]);assert t.imported_object_paths,str(f);return E.load_asset(t.imported_object_paths[0])
tex={}
for f in (SRC/'Source/Textures').glob('*.png'):
 t=task(f,D+'/Textures');tex[f.stem]=t
 if f.stem.endswith('Normal'):t.set_editor_property('srgb',False);t.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_NORMALMAP)
 if f.stem.endswith(('ORM','Roughness','Metallic')):t.set_editor_property('srgb',False);t.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_MASKS)
 E.save_loaded_asset(t,False)
mats={}
master=u.load_asset('/Game/Constellation/MaterialLibrary/Materials/M_Base_PBR');assert master
for name,key in [('LockerPaint','Paint'),('WornSteel','Steel'),('DarkRubber','Rubber')]:
 path=D+'/MI_Rusty_Teal_Locker' if APPLY and name=='LockerPaint' else D+'/Materials/MI_'+name
 m=E.load_asset(path) if E.does_asset_exist(path) else AT.create_asset('MI_'+name,D+'/Materials',u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
 M.set_material_instance_parent(m,master)
 M.clear_all_material_instance_parameters(m)
 for param,suffix in [('BaseColor','Base'),('Roughness','Roughness'),('Metalic','Metallic')]:
  M.set_material_instance_texture_parameter_value(m,param,tex['T_Locker_'+key+'_'+suffix])
 M.set_material_instance_texture_parameter_value(m,'Normal',tex['T_Locker_Paint_Normal'] if key=='Paint' else u.load_asset('/Engine/EngineMaterials/DefaultNormal'))
 M.update_material_instance(m)
 assert m.get_editor_property('parent')==master
 assert M.get_material_instance_texture_parameter_value(m,'BaseColor')==tex['T_Locker_'+key+'_Base']
 E.save_loaded_asset(m,False);mats[name]=m
opts=u.FbxImportUI();opts.import_mesh=True;opts.import_as_skeletal=False;opts.import_materials=False;opts.import_textures=False;opts.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
s=opts.static_mesh_import_data;s.combine_meshes=True;s.auto_generate_collision=False;s.one_convex_hull_per_ucx=True;s.convert_scene_unit=True;s.transform_vertex_to_absolute=False;s.generate_lightmap_u_vs=True
report=[]
for n in ['SM_Locker','SM_Locker_Body','SM_Locker_Door']:
 target=D+'/'+n if APPLY else D+'/Meshes/'+n
 if E.does_asset_exist(target):
  data=E.load_asset(target).get_editor_property('asset_import_data')
  if data:data.scripted_add_filename(str(SRC/'Export'/(n+'.fbx')),0,'')
 mesh=task(SRC/'Export'/(n+'.fbx'),D if APPLY else D+'/Meshes',opts)
 for i,slot in enumerate(mesh.get_editor_property('static_materials')):
  sn=str(slot.get_editor_property('imported_material_slot_name'));key=next((k for k in mats if k in sn),'LockerPaint');mesh.set_material(i,mats[key])
 b=mesh.get_bounding_box()
 manifest=next(x for x in json.loads((SRC/'Export/manifest.json').read_text()) if x['name']==n);lo,hi=manifest['blender_bounds_cm']
 expected=[lo[0],-hi[1],lo[2],hi[0],-lo[1],hi[2]]
 assert all(abs(a-b)<.1 for a,b in zip([b.min.x,b.min.y,b.min.z,b.max.x,b.max.y,b.max.z],expected)),(n,str(b),expected)
 E.save_loaded_asset(mesh,False);report.append({'name':n,'min':[b.min.x,b.min.y,b.min.z],'max':[b.max.x,b.max.y,b.max.z],'slots':[str(x.material_slot_name) for x in mesh.get_editor_property('static_materials')]})
(SRC/('Review/applied-assets.json' if APPLY else 'Review/import.json')).write_text(json.dumps(report,indent=2));u.log('LOCKER_CANDIDATE_IMPORTED')
if APPLY:
 exec(compile((R/'tools/apply-school-locker-stage.py').read_text(encoding='utf-8-sig'),'apply-school-locker-stage.py','exec'))
import time
u.EditorPythonScripting.set_keep_python_script_alive(True);started=time.monotonic()
def finish(dt):
 if time.monotonic()-started>5:u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(finish)
