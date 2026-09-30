"""Import only the isolated OvergrownHall blockout, preserving other levels."""
from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u, json, math
from pathlib import Path
ROOT=Path(u.Paths.project_dir()); SRC=Path(globals().get('SOURCE_DIR',ROOT/'ArtSource/OvergrownHall/Blockout/v002'))
DEST=globals().get('DESTINATION','/Game/Constellation/Environments/OvergrownHall/Blockout'); MAP=DEST+'/Maps/'+globals().get('MAP_NAME','L_OvergrownHall_Blockout')
E=u.EditorAssetLibrary; AT=u.AssetToolsHelpers.get_asset_tools(); M=u.MaterialEditingLibrary
A=u.get_editor_subsystem(u.EditorActorSubsystem); L=u.get_editor_subsystem(u.LevelEditorSubsystem)
spec=load_current_json((SRC/'unreal_manifest.json').read_text())
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
u.SystemLibrary.execute_console_command(world,'Interchange.FeatureFlags.Import.FBX 0')
materials={}
for name,s in spec['materials'].items():
    path=DEST+'/Materials/M_'+name
    mat=E.load_asset(path) if E.does_asset_exist(path) else AT.create_asset('M_'+name,DEST+'/Materials',u.Material,u.MaterialFactoryNew())
    M.delete_all_material_expressions(mat)
    n=M.create_material_expression(mat,u.MaterialExpressionConstant3Vector); n.constant=u.LinearColor(*s['color'],1)
    mat.set_editor_property('two_sided',s.get('two_sided',False))
    if s.get('surface_detail') in ['plaster','floor']:
        low=M.create_material_expression(mat,u.MaterialExpressionConstant3Vector); low.constant=u.LinearColor(.10,.16,.16,1)
        high=M.create_material_expression(mat,u.MaterialExpressionConstant3Vector); high.constant=u.LinearColor(.22,.29,.28,1) if s['surface_detail']=='plaster' else u.LinearColor(.20,.27,.25,1)
        noise=M.create_material_expression(mat,u.MaterialExpressionNoise); noise.set_editor_property('scale',.012 if s['surface_detail']=='plaster' else .008); noise.set_editor_property('levels',2)
        blend=M.create_material_expression(mat,u.MaterialExpressionLinearInterpolate)
        M.connect_material_expressions(low,'',blend,'A'); M.connect_material_expressions(high,'',blend,'B'); M.connect_material_expressions(noise,'',blend,'Alpha'); n=blend
    M.connect_material_property(n,'',u.MaterialProperty.MP_BASE_COLOR)
    for v,p in [(s['roughness'],u.MaterialProperty.MP_ROUGHNESS),(s['metallic'],u.MaterialProperty.MP_METALLIC)]:
        n=M.create_material_expression(mat,u.MaterialExpressionConstant); n.r=v; M.connect_material_property(n,'',p)
    M.recompile_material(mat); assert E.save_loaded_asset(mat); materials[name]=mat
opts=u.FbxImportUI(); opts.import_mesh=True; opts.import_as_skeletal=False; opts.import_materials=False; opts.import_textures=False
opts.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
d=opts.static_mesh_import_data; d.combine_meshes=True; d.auto_generate_collision=False; d.convert_scene_unit=True; d.transform_vertex_to_absolute=True; d.generate_lightmap_u_vs=False
meshes={}; checks=[]
for row in spec['assets']:
    t=u.AssetImportTask(); t.filename=str(SRC/'FBX'/(row['name']+'.fbx')); t.destination_path=DEST+'/Meshes'; t.destination_name=row['name']
    t.automated=True; t.save=True; t.replace_existing=True; t.replace_existing_settings=True; t.options=opts; t.factory=u.FbxFactory()
    AT.import_asset_tasks([t]); assert t.imported_object_paths,t.filename
    mesh=E.load_asset(t.imported_object_paths[0]); assert isinstance(mesh,u.StaticMesh)
    for i,slot in enumerate(mesh.get_editor_property('static_materials')):
        key=str(slot.material_slot_name); assert key in materials,key; mesh.set_material(i,materials[key])
    bounds=mesh.get_bounding_box()
    lo=[bounds.min.x,bounds.min.y,bounds.min.z]; hi=[bounds.max.x,bounds.max.y,bounds.max.z]
    for actual,expected in [(lo,row['bounds_min_cm']),(hi,row['bounds_max_cm'])]:
        assert all(abs(a-b)<.2 for a,b in zip(actual,expected)),(row['name'],actual,expected)
    mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    assert E.save_loaded_asset(mesh); meshes[row['name']]=mesh
    checks.append(dict(name=row['name'],bounds_min_cm=lo,bounds_max_cm=hi,collision=row['collision']))

assert L.load_level(MAP) if E.does_asset_exist(MAP) else L.new_level(MAP)
for a in A.get_all_level_actors():
    if a.get_actor_label().startswith('OH_'): A.destroy_actor(a)
for row in spec['assets']:
    a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0),u.Rotator())
    a.set_actor_label('OH_'+row['name']); c=a.static_mesh_component; c.set_static_mesh(meshes[row['name']])
    if row['collision']: c.set_collision_profile_name('BlockAll')
    else:
        c.set_collision_profile_name('NoCollision')
        c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
def spawn(cls,name,pos,rotation=(0,0,0)):
    a=A.spawn_actor_from_class(cls,u.Vector(*pos),u.Rotator(pitch=rotation[0],yaw=rotation[1],roll=rotation[2])); a.set_actor_label('OH_'+name); return a
sun=spawn(u.DirectionalLight,'Sun',(800,1000,1600),(-53,-143,0))
sc=sun.get_component_by_class(u.DirectionalLightComponent); sc.set_mobility(u.ComponentMobility.MOVABLE); sc.set_intensity(25000); sc.set_light_color(u.LinearColor(1,.85,.61,1))
spawn(u.SkyAtmosphere,'Atmosphere',(0,0,0))
sky=spawn(u.SkyLight,'Sky',(0,0,800)); sk=sky.get_component_by_class(u.SkyLightComponent); sk.set_mobility(u.ComponentMobility.MOVABLE); sk.set_editor_property('real_time_capture',True)
cam=spawn(u.CameraActor,'ReferenceCamera',(0,200,155),(math.degrees(math.atan2(1.60,15)),90,0))
cc=cam.get_component_by_class(u.CameraComponent); cc.set_field_of_view(math.degrees(2*math.atan(36/44))); cc.set_aspect_ratio(1200/640)
cc.set_editor_property('constrain_aspect_ratio',True)
spawn(u.PlayerStart,'PlayerStart',(0,400,110),(0,90,0))
pp=spawn(u.PostProcessVolume,'Exposure',(0,0,0)); pp.set_editor_property('unbound',True)
settings=pp.get_editor_property('settings')
for key,value in [('override_auto_exposure_min_brightness',True),('override_auto_exposure_max_brightness',True),('auto_exposure_min_brightness',10.0),('auto_exposure_max_brightness',10.0)]: settings.set_editor_property(key,value)
pp.set_editor_property('settings',settings)
import runpy
runpy.run_path(str(ROOT/'Content/Python/hall_exposure_settings.py'))['apply_hall_exposure'](pp)
ws=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world().get_world_settings()
mode=E.load_blueprint_class('/Game/Constellation/Core/BP_GameMode'); assert mode; ws.set_editor_property('default_game_mode',mode)
assert L.save_current_level(); assert E.save_directory(DEST,only_if_is_dirty=True,recursive=True)
report=dict(status='import_and_bounds_pass',map=MAP,mesh_categories=len(checks),assets=checks,player_start_cm=[0,400,110],collision='static architecture complex; water and vegetation disabled',playtest='not_run',visual_verification='pending',bird_rig='not_created',materials='procedural first detail pass' if any(s.get('surface_detail') for s in spec['materials'].values()) else 'temporary blockout')
(SRC/'unreal_import.json').write_text(json.dumps(report,indent=2))
u.log('OVERGROWN_HALL_IMPORT_PASS '+MAP)
