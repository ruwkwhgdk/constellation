import unreal as u,json,hashlib,shutil
from pathlib import Path
P=Path(u.Paths.project_dir())/'ArtSource/SchoolGymDoor/Polish_v002'
R=Path(u.Paths.project_dir());M=u.MaterialEditingLibrary;E=u.EditorAssetLibrary
D='/Game/Constellation/Environments/School/Props/GymDoor/M_GymDoor_Weathered'
protected=['Content/Constellation/Environments/School/Sets/GymCorridor/SM_GymDoorLeaf.uasset','Content/Constellation/Environments/School/Blueprints/BP_School_Gate.uasset','Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap']
def hashes():return {x:hashlib.sha256((R/x).read_bytes()).hexdigest() for x in protected}
before=hashes()
source=R/'Content/Constellation/Environments/School/Props/GymDoor/M_GymDoor_Weathered.uasset'
backup=P/'Backup/M_GymDoor_Weathered.before.uasset'
if not backup.exists():shutil.copy2(source,backup)
mat=u.load_asset(D)
customs=[x for x in u.ObjectIterator(u.MaterialExpressionCustom) if x.get_outer()==mat]
surface=[x for x in customs if 'PaintColor' in [str(i.get_editor_property('input_name')) for i in x.get_editor_property('inputs')]]
assert len(surface)==1
surface[0].set_editor_property('code',(P/'weathering.hlsl').read_text())
def node(cls,**kw):
 obj=M.create_material_expression(mat,cls)
 for k,v in kw.items():obj.set_editor_property(k,v)
 return obj
normal=[x for x in customs if [str(i.get_editor_property('input_name')) for i in x.get_editor_property('inputs')]==['P','W','N']]
if normal:
 normal=normal[0];normal.set_editor_property('code',(P/'surface_normal.hlsl').read_text())
else:
 world=node(u.MaterialExpressionWorldPosition)
 local=node(u.MaterialExpressionTransformPosition,transform_source_type=u.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_WORLD,transform_type=u.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_LOCAL)
 assert M.connect_material_expressions(world,'',local,'')
 vertex=node(u.MaterialExpressionVertexNormalWS)
 inputs=[]
 for name in ['P','W','N']:
  i=u.CustomInput();i.set_editor_property('input_name',name);inputs.append(i)
 normal=node(u.MaterialExpressionCustom,inputs=inputs,output_type=u.CustomMaterialOutputType.CMOT_FLOAT3,code=(P/'surface_normal.hlsl').read_text())
 for src,pin in [(local,'P'),(world,'W'),(vertex,'N')]:assert M.connect_material_expressions(src,'',normal,pin)
mat.set_editor_property('tangent_space_normal',False)
assert M.connect_material_property(normal,'',u.MaterialProperty.MP_NORMAL)
M.layout_material_expressions(mat);M.recompile_material(mat)
preview_only=globals().get('PREVIEW_ONLY',False)
if not preview_only:assert E.save_loaded_asset(mat,False)
after=hashes();assert before==after,'Protected mesh, Blueprint or map changed'
(P/'Reports'/('preview-applied.json' if preview_only else 'applied.json')).write_text(json.dumps({'material':D,'protected_hashes':after,'protected_assets_unchanged':True,'surface_normal':'world-space derivative bump; no displacement','changed_assets':[D],'saved':not preview_only},indent=2))
u.log('GYM_DOOR_SURFACE_V002_PREVIEW' if preview_only else 'GYM_DOOR_SURFACE_V002_SAVED')

