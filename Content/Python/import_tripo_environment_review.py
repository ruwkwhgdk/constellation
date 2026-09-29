"""Apply candidate Tripo replacements to a review copy of the maintained hall."""
import unreal as u,json,math,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir()); SRC=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v001'
D='/Game/Environment/OvergrownHall/TripoReplacement'; MAP=D+'/Maps/L_OvergrownHall_TripoReview'
E=u.EditorAssetLibrary; AT=u.AssetToolsHelpers.get_asset_tools(); ML=u.MaterialEditingLibrary
A=u.get_editor_subsystem(u.EditorActorSubsystem); L=u.get_editor_subsystem(u.LevelEditorSubsystem)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
u.SystemLibrary.execute_console_command(world,'Interchange.FeatureFlags.Import.FBX 0')
def import_mesh(file):
    opts=u.FbxImportUI(); opts.automated_import_should_detect_type=False; opts.import_mesh=True; opts.import_as_skeletal=False; opts.import_materials=False; opts.import_textures=False
    opts.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
    opts.static_mesh_import_data.combine_meshes=True; opts.static_mesh_import_data.auto_generate_collision=False; opts.static_mesh_import_data.convert_scene_unit=True
    task=u.AssetImportTask(); task.filename=str(file); task.destination_path=D+'/Meshes'; task.automated=True; task.save=True; task.replace_existing=True; task.options=opts; task.factory=u.FbxFactory()
    AT.import_asset_tasks([task]); mesh=E.load_asset(task.imported_object_paths[0]); assert isinstance(mesh,u.StaticMesh); return mesh
meshes={}
for kind in ['Pillar','Tree']:
    folder=SRC/kind; info=json.loads((folder/'inspection.json').read_text())
    meshes[kind]=import_mesh(folder/('SM_OH_Tripo_'+kind+'.fbx'))
    name='M_OH_Tripo_'+kind; path=D+'/Materials/'+name
    mat=E.load_asset(path) if E.does_asset_exist(path) else AT.create_asset(name,D+'/Materials',u.Material,u.MaterialFactoryNew())
    mat.modify(); mat.set_editor_property('two_sided',kind=='Tree'); ML.delete_all_material_expressions(mat)
    for suffix in ['basecolor','normal','rm']:
        task=u.AssetImportTask(); task.filename=str(folder/(suffix+'.png')); task.destination_path=D+'/Textures'; task.destination_name='T_'+kind+'_'+suffix; task.automated=True; task.save=True; task.replace_existing=True
        AT.import_asset_tasks([task]); tex=E.load_asset(task.imported_object_paths[0]); tex.modify()
        if suffix!='basecolor':tex.set_editor_property('srgb',False)
        if suffix=='normal': tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_NORMALMAP); tex.set_editor_property('flip_green_channel',True)
        E.save_loaded_asset(tex,only_if_is_dirty=False)
        node=ML.create_material_expression(mat,u.MaterialExpressionTextureSample); node.texture=tex
        node.sampler_type=u.MaterialSamplerType.SAMPLERTYPE_NORMAL if suffix=='normal' else u.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR if suffix=='rm' else u.MaterialSamplerType.SAMPLERTYPE_COLOR
        if suffix=='basecolor':ML.connect_material_property(node,'RGB',u.MaterialProperty.MP_BASE_COLOR)
        elif suffix=='normal':ML.connect_material_property(node,'RGB',u.MaterialProperty.MP_NORMAL)
        else:
            ML.connect_material_property(node,'G',u.MaterialProperty.MP_ROUGHNESS); ML.connect_material_property(node,'B',u.MaterialProperty.MP_METALLIC)
    ML.recompile_material(mat); E.save_loaded_asset(mat,only_if_is_dirty=False)
    meshes[kind].set_material(0,mat); E.save_loaded_asset(meshes[kind],only_if_is_dirty=False)
remaining=import_mesh(SRC/'SM_OH_RemainingPiers.fbx')
placements=json.loads((SRC/'placements.json').read_text())
for i,n in enumerate(placements['remaining_materials']):remaining.set_material(i,E.load_asset('/Game/Environment/OvergrownHall/Scene/Materials/M_'+n))
remaining.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE); E.save_loaded_asset(remaining,only_if_is_dirty=False)
if not E.does_asset_exist(MAP):assert E.duplicate_asset('/Game/Environment/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout',MAP)
assert L.load_level(MAP)
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
for label,a in actors.items():
    if label.startswith('OH_Tripo_'):A.destroy_actor(a)
actors['OH_SM_OH_Blockout_02'].static_mesh_component.set_static_mesh(remaining)
old=actors.get('OH_SM_OH_Blockout_19')
if old:A.destroy_actor(old)
def place(kind,pos,index,scale=1,angle=0):
    a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*pos),u.Rotator(pitch=0,yaw=angle,roll=0)); a.set_actor_label('OH_Tripo_'+kind+'_%02d'%index)
    a.static_mesh_component.set_static_mesh(meshes[kind]); a.set_actor_scale3d(u.Vector(scale,scale,scale)); a.static_mesh_component.set_collision_profile_name('BlockAll')
for i,pos in enumerate(placements['pillar_segments']):place('Pillar',pos,i,angle=(i%4)*90)
trees=[(x,y,0) for x in [-1150,1150] for y in [350,900,1450,2000,2550]]+[(x,2450,0) for x in [-750,-400,0,400,750]]+[(x,2950,0) for x in [-900,-300,300,900]]
for i,pos in enumerate(trees):place('Tree',pos,i,scale=1+.10*math.sin(i*2),angle=i*137.5)
assert L.save_current_level()
# Bind a dedicated sequence to this level's bird instances.
runpy.run_path(str(ROOT/'Content/Python/build_overgrown_flock.py'),init_globals={'FLOCK_DEST':D,'FLOCK_MAP':'L_OvergrownHall_TripoReview','FLOCK_OUT':SRC/'Flock'})
(SRC/'unreal_import.json').write_text(json.dumps(dict(map=MAP,pillar_segments=len(placements['pillar_segments']),trees=len(trees),status='candidate_applied_for_review',meshes={k:v.get_path_name() for k,v in meshes.items()},adoption='pending user appearance review'),indent=2))
u.log('TRIPO_ENV_REVIEW_IMPORT_PASS')
