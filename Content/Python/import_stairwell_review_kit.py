"""Import generated kit to isolated review assets; no existing gameplay map edits."""
from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u
import json
from pathlib import Path
SRC=Path(u.Paths.project_dir())/'ArtSource/Stairwell_Modular/Production/v001'
DEST='/Game/Constellation/Environments/Stairwell/ReviewKit'
report=load_current_json((SRC/'reports/asset_manifest.json').read_text(encoding='utf-8'))
spec=load_current_json((SRC/'reports/material_spec.json').read_text(encoding='utf-8'))
AT=u.AssetToolsHelpers.get_asset_tools(); E=u.EditorAssetLibrary; M=u.MaterialEditingLibrary
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
u.SystemLibrary.execute_console_command(world,'Interchange.FeatureFlags.Import.FBX 0')
def task(file,dest,opts=None):
    t=u.AssetImportTask(); t.filename=str(file); t.destination_path=dest; t.automated=True; t.save=True
    t.replace_existing=True; t.replace_existing_settings=True
    if opts: t.options=opts; t.factory=u.FbxFactory()
    return t
textures={}
ts=[task(f,DEST+'/Textures') for f in (SRC/'textures').glob('*.png')]
AT.import_asset_tasks(ts)
for t in ts:
    assert t.imported_object_paths,t.filename
    tex=E.load_asset(t.imported_object_paths[0]); name=Path(t.filename).stem
    if name.startswith('ORM_'): tex.set_editor_property('srgb',False); tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_MASKS)
    if name.startswith('NormalGL_'):
        tex.set_editor_property('srgb',False); tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_NORMALMAP); tex.set_editor_property('flip_green_channel',True)
    E.save_loaded_asset(tex); textures[name]=tex
def const(mat,value):
    n=M.create_material_expression(mat,u.MaterialExpressionConstant); n.r=value; return n
def color(mat,rgb):
    n=M.create_material_expression(mat,u.MaterialExpressionConstant3Vector); n.constant=u.LinearColor(*rgb,1); return n
def connect(mat,n,pin,prop): M.connect_material_property(n,pin,prop)
def texture(mat,tex,linear=False,normal=False):
    n=M.create_material_expression(mat,u.MaterialExpressionTextureSample); n.texture=tex
    if normal: n.sampler_type=u.MaterialSamplerType.SAMPLERTYPE_NORMAL
    elif linear: n.sampler_type=u.MaterialSamplerType.SAMPLERTYPE_MASKS
    return n
mats={}
for name,s in spec.items():
    path=DEST+'/Materials/'+name
    mat=E.load_asset(path) if E.does_asset_exist(path) else AT.create_asset(name,DEST+'/Materials',u.Material,u.MaterialFactoryNew())
    M.delete_all_material_expressions(mat)
    base=color(mat,s['color'])
    # Broad rough surface modulation in world coordinates: the same scale across modules.
    if s['noise']:
        noise=M.create_material_expression(mat,u.MaterialExpressionNoise); noise.set_editor_property('scale',.45)
        noise.set_editor_property('quality',1); noise.set_editor_property('levels',3)
        mul=M.create_material_expression(mat,u.MaterialExpressionMultiply); M.connect_material_expressions(const(mat,.28),'',mul,'B'); M.connect_material_expressions(noise,'',mul,'A')
        add=M.create_material_expression(mat,u.MaterialExpressionAdd); M.connect_material_expressions(const(mat,.72),'',add,'B'); M.connect_material_expressions(mul,'',add,'A')
        tint=M.create_material_expression(mat,u.MaterialExpressionMultiply); M.connect_material_expressions(base,'',tint,'A'); M.connect_material_expressions(add,'',tint,'B'); base=tint
    connect(mat,base,'',u.MaterialProperty.MP_BASE_COLOR)
    connect(mat,const(mat,s['roughness']),'',u.MaterialProperty.MP_ROUGHNESS)
    connect(mat,const(mat,s['metallic']),'',u.MaterialProperty.MP_METALLIC)
    if s['emission']:
        n=color(mat,[x*s['emission'] for x in s['color']]); connect(mat,n,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
    M.recompile_material(mat); E.save_loaded_asset(mat); mats[name]=mat
light_name='tripo_material_4aa20774-e697-4117-a168-527ce0f5a17f'
path=DEST+'/Materials/M_Kit_TripoLight'
mat=E.load_asset(path) if E.does_asset_exist(path) else AT.create_asset('M_Kit_TripoLight',DEST+'/Materials',u.Material,u.MaterialFactoryNew())
M.delete_all_material_expressions(mat)
for prefix,prop,pin in [('Color_',u.MaterialProperty.MP_BASE_COLOR,'RGB'),('ORM_',u.MaterialProperty.MP_ROUGHNESS,'G'),('NormalGL_',u.MaterialProperty.MP_NORMAL,'RGB')]:
    tex=next(v for k,v in textures.items() if k.startswith(prefix)); n=texture(mat,tex,prefix=='ORM_',prefix=='NormalGL_'); connect(mat,n,pin,prop)
    if prefix=='ORM_': connect(mat,n,'R',u.MaterialProperty.MP_AMBIENT_OCCLUSION); connect(mat,n,'B',u.MaterialProperty.MP_METALLIC)
M.recompile_material(mat); E.save_loaded_asset(mat); mats[light_name]=mat
opts=u.FbxImportUI(); opts.import_mesh=True; opts.import_as_skeletal=False; opts.import_materials=False; opts.import_textures=False; opts.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
d=opts.static_mesh_import_data; d.combine_meshes=True; d.auto_generate_collision=False; d.one_convex_hull_per_ucx=True; d.convert_scene_unit=True; d.transform_vertex_to_absolute=False; d.generate_lightmap_u_vs=True
rows=[r for r in report['assets'] if not r.get('notes',{}).get('existing_unreal_asset')]
tasks=[task(SRC/'FBX'/(r['name']+'.fbx'),DEST+'/Meshes',opts) for r in rows]
AT.import_asset_tasks(tasks)
meshes={}; checks=[]
for r,t in zip(rows,tasks):
    assert t.imported_object_paths,r['name']; mesh=E.load_asset(t.imported_object_paths[0])
    slots=mesh.get_editor_property('static_materials')
    for i,s in enumerate(slots):
        key=str(s.material_slot_name)
        target=mats.get(key) or mats.get(key.rsplit('.',1)[0])
        assert target,(r['name'],key,list(mats)); mesh.set_material(i,target)
    E.save_loaded_asset(mesh); meshes[r['name']]=mesh
    bounds=mesh.get_bounding_box(); size=bounds.max-bounds.min; dims=[size.x,size.y,size.z]
    assert all(abs(a-b)<.05 for a,b in zip(dims,r['dimensions_cm'])),(r['name'],dims,r['dimensions_cm'])
    geom=mesh.get_editor_property('body_setup').get_editor_property('agg_geom')
    count=sum(len(geom.get_editor_property(p)) for p in ['convex_elems','box_elems','sphere_elems','sphyl_elems'])
    assert count==r['collision_hulls'],(r['name'],count,r['collision_hulls'])
    checks.append(dict(name=r['name'],dimensions_cm=dims,bounds_min_cm=[bounds.min.x,bounds.min.y,bounds.min.z],bounds_max_cm=[bounds.max.x,bounds.max.y,bounds.max.z],collision_hulls=count,materials=len(slots),path=mesh.get_path_name()))
    (SRC/'reports/unreal_mesh_checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
for r in report['assets']:
    if r.get('notes',{}).get('existing_unreal_asset'):
        meshes[r['name']]=E.load_asset('/Game/Constellation/Environments/Stairwell/Meshes/'+r['name']); assert meshes[r['name']]
level=u.get_editor_subsystem(u.LevelEditorSubsystem); actors=u.get_editor_subsystem(u.EditorActorSubsystem)
map_path='/Game/Constellation/Review/Stairwell/Maps/L_Stairwell_KitReview'
if E.does_asset_exist(map_path):
    assert level.load_level(map_path)
    for a in actors.get_all_level_actors():
        if str(a.get_actor_label()).startswith('SWReview_'): actors.destroy_actor(a)
else: assert level.new_level(map_path)
def spawn(mesh,name,pos,rot=0):
    a=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*pos),u.Rotator(pitch=0,yaw=rot,roll=0)); a.set_actor_label('SWReview_'+name); a.static_mesh_component.set_static_mesh(mesh); return a
for i,r in enumerate(report['assets']):
    x=(i%6)*380; y=(i//6)*420
    spawn(meshes[r['name']],r['name'],(x,y,30))
    label=actors.spawn_actor_from_class(u.TextRenderActor,u.Vector(x,y-45,10),u.Rotator(pitch=0,yaw=-90,roll=0)); label.set_actor_label('SWReview_Label_'+r['name']); label.text_render.set_text(r['id']+' '+r['name'].replace('SM_SW_','')); label.text_render.set_world_size(12)
floor_actor=spawn(E.load_asset('/Engine/BasicShapes/Cube'),'Floor',(950,1000,-10)); floor_actor.set_actor_scale3d(u.Vector(27,29,.1))
light=actors.spawn_actor_from_class(u.DirectionalLight,u.Vector(0,0,700),u.Rotator(pitch=-45,yaw=-30,roll=0)); light.set_actor_label('SWReview_Sun')
sky=actors.spawn_actor_from_class(u.SkyLight,u.Vector(0,0,500)); sky.set_actor_label('SWReview_Sky')
player=actors.spawn_actor_from_class(u.PlayerStart,u.Vector(100,-400,100),u.Rotator(pitch=0,yaw=90,roll=0)); player.set_actor_label('SWReview_PlayerStart')
# Exact-scale stair/landing/rail sample, separate from gallery.
origin=(0,-800,0)
spawn(meshes['SM_SW_01_Stair6'],'Assembly_Stairs',origin)
# Landing asset width is X, depth Y; rotate to align its 140cm width with stair Y.
spawn(meshes['SM_SW_02_Landing140'],'Assembly_Landing',(180,-940,90),90)
for y in [-800-8,-800-132]:
    rail=spawn(meshes['SM_SW_10_RailSlope'],'Assembly_Rail_'+str(y),(0,y,65))
    extension=spawn(meshes['SM_SW_10_RailSlope60'],'Assembly_RailExtension_'+str(y),(120,y,125))
    spawn(meshes['SM_SW_17_SlopeToLevel'],'Assembly_RailTransition_'+str(y),(180,y,155))
    transition=next(r for r in rows if r['name']=='SM_SW_17_SlopeToLevel')['notes']['end']
    horizontal=spawn(meshes['SM_SW_09_RailHorizontal'],'Assembly_RailLanding_'+str(y),(180+transition[0]*100,y,155+transition[2]*100))
    # UE imports Blender Y reversed. Mirror only Y on the near wall to keep slope X/Z.
    if y==-808:
        for a in [rail,extension,horizontal]: a.set_actor_scale3d(u.Vector(1,-1,1))
for i in range(6): spawn(meshes['SM_SW_16_Nosing140'],'Assembly_Nosing'+str(i),(i*30,-800,(i+1)*15))
# Movable rectangular light uses emissive material plus a separate real light in the review level.
lamp=spawn(meshes['SM_SW_15_LightFixture'],'Assembly_Lamp',(250,-870,350))
rect=actors.spawn_actor_from_class(u.RectLight,u.Vector(250,-870,337),u.Rotator(pitch=-90,yaw=0,roll=0)); rect.set_actor_label('SWReview_Assembly_LampLight')
level.save_current_level(); E.save_directory(DEST,only_if_is_dirty=True,recursive=True)
result=dict(status='review_import_verified',map=map_path,assets=checks,preserved_door_assets=2,appearance='pending_user_review',playtest='not_run',scene='gallery and fit sample; not a finished source-scene reconstruction')
(SRC/'reports/unreal_import_verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
u.log('STAIRWELL_KIT_IMPORTED '+str(len(checks)))
