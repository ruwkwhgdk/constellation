import unreal,json,re,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;BASE='/Game/Constellation/Characters/Heroine/Refined';N='player_heroine_new'
source=P.parent/'RigContourFix/Delivery/Heroine_Skeletal.fbx';data=json.loads((P/'materials.json').read_text())
asset=unreal.EditorAssetLibrary;at=unreal.AssetToolsHelpers.get_asset_tools();lib=unreal.MaterialEditingLibrary
def load(p):return unreal.load_asset(p)
def run_import(file,dest,name,opt=None):
 t=unreal.AssetImportTask();t.filename=str(file);t.destination_path=dest;t.destination_name=name;t.automated=True;t.replace_existing=True;t.save=True
 if opt:t.options=opt;t.factory=unreal.FbxFactory()
 at.import_asset_tasks([t]);return list(t.imported_object_paths)
opt=unreal.FbxImportUI();opt.import_as_skeletal=True;opt.mesh_type_to_import=unreal.FBXImportType.FBXIT_SKELETAL_MESH;opt.automated_import_should_detect_type=False;opt.import_materials=False;opt.import_textures=False;opt.import_animations=False;opt.create_physics_asset=True
opt.skeletal_mesh_import_data.import_uniform_scale=100.0;opt.skeletal_mesh_import_data.convert_scene=True;opt.skeletal_mesh_import_data.convert_scene_unit=True;opt.skeletal_mesh_import_data.normal_import_method=unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
mesh=load(BASE+'/SK_'+N)
if not mesh:
 run_import(source,BASE,'SK_'+N,opt);mesh=load(BASE+'/SK_'+N)
assert isinstance(mesh,unreal.SkeletalMesh)
skel=load(BASE+'/SKEL_'+N) or mesh.skeleton;phys=load(BASE+'/PHYS_'+N) or mesh.get_editor_property('physics_asset')
mesh.call_method('SetSkeleton',args=(skel,))
if phys:mesh.set_editor_property('physics_asset',phys)
assert skel
if not phys:
 helper=unreal.get_default_object(unreal.load_class(None,'/Script/PhysicsToolsets.PhysicsAssetToolset'))
 phys=helper.call_method('CreateFromMesh',args=(BASE+'/SK_'+N,True))
 assert phys
 mesh.set_editor_property('physics_asset',phys)
for obj,name in [(skel,'SKEL_'+N),(phys,'PHYS_'+N)]:
 if obj.get_name()!=name:assert asset.rename_loaded_asset(obj,BASE+'/'+name)
textures={}
for name,info in data['textures'].items():
 run_import(info['path'],BASE+'/Textures',name);tex=load(BASE+'/Textures/'+name);assert tex
 tex.set_editor_property('srgb',info['srgb']);asset.save_loaded_asset(tex);textures[name]=tex
master=load(BASE+'/Materials/M_'+N)
if not master:master=at.create_asset('M_'+N,BASE+'/Materials',unreal.Material,unreal.MaterialFactoryNew())
lib.delete_all_material_expressions(master);master.set_editor_property('two_sided',True)
def expr(cls,x,y):return lib.create_material_expression(master,cls,x,y)
tex=expr(unreal.MaterialExpressionTextureSampleParameter2D,-600,0);tex.set_editor_property('parameter_name','BaseColorTexture');tex.set_editor_property('texture',next(iter(textures.values())))
tint=expr(unreal.MaterialExpressionVectorParameter,-600,200);tint.set_editor_property('parameter_name','BaseColorTint');tint.set_editor_property('default_value',unreal.LinearColor(1,1,1,1))
use=expr(unreal.MaterialExpressionScalarParameter,-600,400);use.set_editor_property('parameter_name','UseTexture');use.set_editor_property('default_value',1.0)
lerp=expr(unreal.MaterialExpressionLinearInterpolate,-280,80)
lib.connect_material_expressions(tint,'',lerp,'A');lib.connect_material_expressions(tex,'RGB',lerp,'B');lib.connect_material_expressions(use,'',lerp,'Alpha');lib.connect_material_property(lerp,'',unreal.MaterialProperty.MP_BASE_COLOR)
for name,prop,default,y in [('Roughness',unreal.MaterialProperty.MP_ROUGHNESS,.7,450),('Metallic',unreal.MaterialProperty.MP_METALLIC,0,600),('Specular',unreal.MaterialProperty.MP_SPECULAR,.23,750)]:
 e=expr(unreal.MaterialExpressionScalarParameter,-280,y);e.set_editor_property('parameter_name',name);e.set_editor_property('default_value',default);lib.connect_material_property(e,'',prop)
lib.set_material_usage(master,unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH);lib.recompile_material(master);asset.save_loaded_asset(master)
slots=list(mesh.materials);assignments=[]
for slot in slots:
 raw=str(slot.material_slot_name)
 key=raw if raw in data['materials'] else re.sub(r'(_|\.)\d{3}$','',raw)
 assert key in data['materials'],('UNKNOWN_MATERIAL_SLOT',raw)
 m=data['materials'][key];suffix=re.sub('[^A-Za-z0-9_]+','_',key.removeprefix('M_'));name='MI_'+N+'_'+suffix
 mi=load(BASE+'/Materials/'+name)
 if not mi:mi=at.create_asset(name,BASE+'/Materials',unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew())
 lib.set_material_instance_parent(mi,master)
 base=m['links'].get('Base Color');lib.set_material_instance_scalar_parameter_value(mi,'UseTexture',1.0 if isinstance(base,str) else 0.0)
 if isinstance(base,str):lib.set_material_instance_texture_parameter_value(mi,'BaseColorTexture',textures[base])
 lib.set_material_instance_vector_parameter_value(mi,'BaseColorTint',unreal.LinearColor(*m['base_color']))
 for param,k in [('Roughness','roughness'),('Metallic','metallic'),('Specular','specular')]:lib.set_material_instance_scalar_parameter_value(mi,param,float(m[k]))
 lib.update_material_instance(mi);asset.save_loaded_asset(mi);slot.material_interface=mi;assignments.append({'slot':raw,'material':mi.get_path_name()})
mesh.set_editor_property('materials',slots);asset.save_loaded_asset(mesh);asset.save_loaded_asset(skel);asset.save_loaded_asset(phys)
opt=unreal.FbxImportUI();opt.import_mesh=False;opt.import_as_skeletal=True;opt.import_animations=True;opt.mesh_type_to_import=unreal.FBXImportType.FBXIT_ANIMATION;opt.automated_import_should_detect_type=False;opt.skeleton=skel;opt.import_materials=False;opt.import_textures=False;opt.create_physics_asset=False
opt.anim_sequence_import_data.import_uniform_scale=100.0
oldanim=load(BASE+'/Animations/AS_'+N+'_PreviewRelaxed')
if oldanim:oldanim.get_editor_property('asset_import_data').set_editor_property('import_uniform_scale',100.0)
paths=run_import(P/'PreviewRelaxed.fbx',BASE+'/Animations','AS_'+N+'_PreviewRelaxed',opt)
animations=[]
for path in paths:
 a=load(path)
 if isinstance(a,unreal.AnimSequence):
  wanted=BASE+'/Animations/AS_'+N+'_PreviewRelaxed'
  if a.get_path_name().split('.')[0]!=wanted:assert asset.rename_loaded_asset(a,wanted)
  animations.append(a.get_path_name());asset.save_loaded_asset(a)
assert animations
asset.save_directory(BASE,only_if_is_dirty=True,recursive=True)
report={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'mesh':mesh.get_path_name(),'skeleton':skel.get_path_name(),'physics_asset':phys.get_path_name(),'height_cm':mesh.get_bounds().box_extent.z*2,'materials':assignments,'textures':list(textures),'animations':animations,'assets':list(asset.list_assets(BASE,recursive=True,include_folder=False)),'pass':abs(mesh.get_bounds().box_extent.z*2-160)<.1 and all(s.material_interface for s in mesh.materials)}
assert report['pass'],report
(P/'import_result.json').write_text(json.dumps(report,indent=2));print('PLAYER_HEROINE_NEW_IMPORTED',json.dumps(report))
