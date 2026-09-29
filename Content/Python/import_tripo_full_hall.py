"""Import the complete Tripo kit and replace old visible geometry in a dedicated level."""
import unreal as u,json,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir());SRC=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v002'
D='/Game/Environment/OvergrownHall/TripoFull';MAP=D+'/Maps/L_OvergrownHall_TripoFull'
E=u.EditorAssetLibrary;AT=u.AssetToolsHelpers.get_asset_tools();ML=u.MaterialEditingLibrary
A=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem);SM=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
u.SystemLibrary.execute_console_command(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(),'Interchange.FeatureFlags.Import.FBX 0')
manifest=json.loads((SRC/'kit_manifest.json').read_text());meshes={};dimensions={};material_paths=[]
for row in manifest:
    id=row['id'];folder=SRC/(id+'_'+row['name']);name=row['mesh']
    opts=u.FbxImportUI();opts.automated_import_should_detect_type=False;opts.import_mesh=True;opts.import_as_skeletal=False;opts.import_materials=False;opts.import_textures=False;opts.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
    opts.static_mesh_import_data.combine_meshes=True;opts.static_mesh_import_data.auto_generate_collision=False;opts.static_mesh_import_data.convert_scene_unit=True
    task=u.AssetImportTask();task.filename=str(folder/(name+'.fbx'));task.destination_path=D+'/Meshes';task.automated=True;task.save=True;task.replace_existing=True;task.options=opts;task.factory=u.FbxFactory()
    AT.import_asset_tasks([task]);mesh=E.load_asset(task.imported_object_paths[0]);assert isinstance(mesh,u.StaticMesh)
    matname='M_OH_T_'+id;matpath=D+'/Materials/'+matname
    mat=E.load_asset(matpath) if E.does_asset_exist(matpath) else AT.create_asset(matname,D+'/Materials',u.Material,u.MaterialFactoryNew())
    mat.modify();mat.set_editor_property('two_sided',id in ['16','17','18']);ML.delete_all_material_expressions(mat)
    for suffix in ['basecolor','normal','rm']:
        task=u.AssetImportTask();task.filename=str(folder/(suffix+'.png'));task.destination_path=D+'/Textures';task.destination_name='T_OH_'+id+'_'+suffix;task.automated=True;task.save=True;task.replace_existing=True
        AT.import_asset_tasks([task]);tex=E.load_asset(task.imported_object_paths[0]);tex.modify()
        if suffix!='basecolor':tex.set_editor_property('srgb',False)
        if suffix=='normal':tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_NORMALMAP);tex.set_editor_property('flip_green_channel',True)
        E.save_loaded_asset(tex,only_if_is_dirty=False)
        node=ML.create_material_expression(mat,u.MaterialExpressionTextureSample);node.texture=tex
        node.sampler_type=u.MaterialSamplerType.SAMPLERTYPE_NORMAL if suffix=='normal' else u.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR if suffix=='rm' else u.MaterialSamplerType.SAMPLERTYPE_COLOR
        if suffix=='basecolor':ML.connect_material_property(node,'RGB',u.MaterialProperty.MP_BASE_COLOR)
        elif suffix=='normal':ML.connect_material_property(node,'RGB',u.MaterialProperty.MP_NORMAL)
        else:
            ML.connect_material_property(node,'G',u.MaterialProperty.MP_ROUGHNESS);ML.connect_material_property(node,'B',u.MaterialProperty.MP_METALLIC)
    ML.recompile_material(mat);E.save_loaded_asset(mat,only_if_is_dirty=False);material_paths.append(matpath)
    mesh.set_material(0,mat)
    if id=='13':
        # UCX box is imported from the Blender-authored FBX (also works in commandlets).
        mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
    elif id not in ['16','17','18']:
        mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    E.save_loaded_asset(mesh,only_if_is_dirty=False);meshes[id]=mesh;dimensions[id]=row['dimensions_m']
meshes['02']=E.load_asset('/Game/Environment/OvergrownHall/TripoReplacement/Meshes/SM_OH_Tripo_Pillar');dimensions['02']=[.65,.65,3]
if not E.does_asset_exist(MAP):assert E.duplicate_asset('/Game/Environment/OvergrownHall/TripoReplacement/Maps/L_OvergrownHall_TripoReview',MAP)
assert L.load_level(MAP)
removed=[]
for a in A.get_all_level_actors():
    label=a.get_actor_label()
    if (label.startswith('OH_SM_OH_Blockout_') and not label.endswith('_21')) or label.startswith(('OH_Tripo_Pillar_','OH_FULL_')):
        removed.append(label);A.destroy_actor(a)
placements=json.loads((SRC/'placements.json').read_text());counts={}
for i,r in enumerate(placements):
    id=r['id'];a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*r['position']),u.Rotator(pitch=r['pitch'],yaw=r['yaw'],roll=r['roll']))
    a.set_actor_label('OH_FULL_'+id+'_%04d'%i);a.static_mesh_component.set_static_mesh(meshes[id])
    a.set_actor_scale3d(u.Vector(*[r['dimensions'][j]/dimensions[id][j] for j in range(3)]))
    a.static_mesh_component.set_collision_profile_name('NoCollision' if id in ['16','17','18'] else 'BlockAll')
    counts[id]=counts.get(id,0)+1
assert L.save_current_level()
runpy.run_path(str(ROOT/'Content/Python/build_overgrown_flock.py'),init_globals={'FLOCK_DEST':D,'FLOCK_MAP':'L_OvergrownHall_TripoFull','FLOCK_OUT':SRC/'Flock'})
(SRC/'unreal_import.json').write_text(json.dumps(dict(map=MAP,imported_meshes=19,instances=counts,retained_tripo_trees=19,removed_old_actors=removed,materials=material_paths,playtest=False),indent=2))
u.log('TRIPO_FULL_IMPORT_COMPLETE')
