import unreal as u,json,shutil,hashlib
from pathlib import Path
P=Path(u.Paths.project_dir())/'ArtSource/SchoolGymDoor/Polish_v001'
D='/Game/Constellation/Environments/School/Props/GymDoor'
B='/Game/Constellation/Environments/School/Blueprints/BP_School_Gate'
S='/Game/Constellation/Environments/School/Sets/GymCorridor/SM_GymDoorLeaf'
E=u.EditorAssetLibrary;M=u.MaterialEditingLibrary;AT=u.AssetToolsHelpers.get_asset_tools()
backup=P/'Source/Backup';backup.mkdir(exist_ok=True)
for path in [B,S]:
 src=Path(u.Paths.project_content_dir())/(path.removeprefix('/Game/')+'.uasset')
 dest=backup/src.name
 if not dest.exists():shutil.copy2(src,dest)
bp=u.load_asset(B);mesh=u.load_asset(S)
graph=u.ResourceRecoveryLibrary.export_blueprint_graphs(bp)
(P/'Reports/graphs-before.txt').write_text(graph,encoding='utf8')
def node(mat,cls,**kw):
 x=M.create_material_expression(mat,cls)
 for k,v in kw.items():x.set_editor_property(k,v)
 return x
def link(a,b,pin='',out=''):assert M.connect_material_expressions(a,out,b,pin)
def prop(a,p,out=''):assert M.connect_material_property(a,out,p)
mat=E.load_asset(D+'/M_GymDoor_Weathered') if E.does_asset_exist(D+'/M_GymDoor_Weathered') else AT.create_asset('M_GymDoor_Weathered',D,u.Material,u.MaterialFactoryNew())
M.delete_all_material_expressions(mat)
world=node(mat,u.MaterialExpressionWorldPosition)
local=node(mat,u.MaterialExpressionTransformPosition,transform_source_type=u.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_WORLD,transform_type=u.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_LOCAL);link(world,local)
paint=node(mat,u.MaterialExpressionVectorParameter,parameter_name='PaintColor',default_value=u.LinearColor(.025,.041,.061,1))
finish=node(mat,u.MaterialExpressionScalarParameter,parameter_name='Finish',default_value=0)
inputs=[]
for name in ['P','PaintColor','Finish']:
 i=u.CustomInput();i.set_editor_property('input_name',name);inputs.append(i)
surface=node(mat,u.MaterialExpressionCustom,code=(P/'weathering.hlsl').read_text(),inputs=inputs,output_type=u.CustomMaterialOutputType.CMOT_FLOAT4)
link(local,surface,'P');link(paint,surface,'PaintColor');link(finish,surface,'Finish')
rgb=node(mat,u.MaterialExpressionComponentMask,r=True,g=True,b=True,a=False);link(surface,rgb);prop(rgb,u.MaterialProperty.MP_BASE_COLOR)
rough=node(mat,u.MaterialExpressionComponentMask,r=False,g=False,b=False,a=True);link(surface,rough);prop(rough,u.MaterialProperty.MP_ROUGHNESS)
metallic=node(mat,u.MaterialExpressionScalarParameter,parameter_name='Metallic',default_value=.12);prop(metallic,u.MaterialProperty.MP_METALLIC)
spec=node(mat,u.MaterialExpressionConstant,r=.35);prop(spec,u.MaterialProperty.MP_SPECULAR)
M.layout_material_expressions(mat);M.recompile_material(mat);E.save_loaded_asset(mat,False)
instances=[]
for name,f,col,metal in [('MI_GymDoor_Navy',0,(.007,.013,.022),.05),('MI_GymDoor_Trim',1,(.009,.013,.018),.16),('MI_GymDoor_Hardware',2,(.1,.1,.1),.55)]:
 mi=E.load_asset(D+'/'+name) if E.does_asset_exist(D+'/'+name) else AT.create_asset(name,D,u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
 M.set_material_instance_parent(mi,mat);M.set_material_instance_scalar_parameter_value(mi,'Finish',f);M.set_material_instance_scalar_parameter_value(mi,'Metallic',metal);M.set_material_instance_vector_parameter_value(mi,'PaintColor',u.LinearColor(*col,1));M.update_material_instance(mi);E.save_loaded_asset(mi,False);instances.append(mi)
# Preserve the exact existing static mesh, UVs, collision hulls, lightmap and glass.
old_slots=[x.material_interface.get_path_name() for x in mesh.static_materials]
for i,mi in enumerate(instances):mesh.set_material(i,mi)
assert E.save_loaded_asset(mesh,False)
def settings(c):
 tr=c.get_relative_transform()
 return {'location':[tr.translation.x,tr.translation.y,tr.translation.z],'rotation':[tr.rotation.x,tr.rotation.y,tr.rotation.z,tr.rotation.w],'scale':[tr.scale3d.x,tr.scale3d.y,tr.scale3d.z],'collision':str(c.get_collision_enabled()),'profile':str(c.get_collision_profile_name()),'overlaps':c.get_editor_property('generate_overlap_events')}
changed=[]
for c in u.ObjectIterator(u.StaticMeshComponent):
 if not c.get_path_name().startswith(B+'.') or not c.get_name().startswith(('DoorLeft','DoorRight')):continue
 before=settings(c);c.modify();c.set_static_mesh(mesh);c.set_editor_property('override_materials',[]);assert settings(c)==before
 changed.append({'name':c.get_name(),'preserved':before})
assert len(changed)==2,changed
u.BlueprintEditorLibrary.compile_blueprint(bp)
after=u.ResourceRecoveryLibrary.export_blueprint_graphs(bp)
(P/'Reports/graphs-after.txt').write_text(after,encoding='utf8')
assert graph==after,'Unexpected Blueprint graph change'
assert E.save_loaded_asset(bp,False)
(P/'Reports/applied.json').write_text(json.dumps({'mesh':S,'blueprint':B,'old_materials':old_slots,'new_materials':[x.material_interface.get_path_name() for x in mesh.static_materials],'components':changed,'graph_sha256':hashlib.sha256(graph.encode()).hexdigest(),'graph_unchanged':True,'geometry_reimported':False,'map_saved':False},indent=2))
u.log('GYM_DOOR_POLISH_APPLIED')
