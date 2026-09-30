"""v012 shallow transparent water. Run PROBE first; APPLY saves the reviewed result."""
from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u,json,math
from pathlib import Path
APPLY=globals().get('APPLY',False)
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v012';OUT.mkdir(exist_ok=True)
D='/Game/Constellation/Environments/OvergrownHall/TripoFull';MAP='/Game/Constellation/Worlds/OvergrownHall/Maps/L_OvergrownHall_TripoFull'
E=u.EditorAssetLibrary;ML=u.MaterialEditingLibrary;AT=u.AssetToolsHelpers.get_asset_tools();L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert L.load_level(MAP)
actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
source=(ROOT/'Content/Python/apply_hall_growth_water.py').read_text();exec(source[source.index('class Graph:'):source.index('\nmoss_keys=')])
dest=D+'/ReferenceMaterials';name='M_OH_ShallowTransmission'
m=E.load_asset(dest+'/'+name) if E.does_asset_exist(dest+'/'+name) else AT.create_asset(name,dest,u.Material,u.MaterialFactoryNew())
m.modify();ML.delete_all_material_expressions(m)
for key,value in [('blend_mode',u.BlendMode.BLEND_TRANSLUCENT),('shading_model',u.MaterialShadingModel.MSM_DEFAULT_LIT),('tangent_space_normal',False),('translucency_lighting_mode',u.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING),('use_planar_forward_reflections',True),('use_hq_forward_reflections',True),('screen_space_reflections',True)]:m.set_editor_property(key,value)
m.set_editor_property('translucency_pass',u.MaterialTranslucencyPass.MTP_BEFORE_DOF)
g=Graph(m)
# Reuse the exact approved analytic world-space ripple graph, not its opaque pigment.
wave_source=(ROOT/'Content/Python/apply_water_ruins.py').read_text()
exec(wave_source[wave_source.index('pos=g.n('):wave_source.index('noise=g.noise(')])
g.prop(g.color((.62,.80,.70)),u.MaterialProperty.MP_BASE_COLOR)
g.prop(g.c(.92),u.MaterialProperty.MP_METALLIC);g.prop(g.c(.85),u.MaterialProperty.MP_SPECULAR);g.prop(g.c(.04),u.MaterialProperty.MP_ROUGHNESS)
fresnel=g.n(u.MaterialExpressionFresnel);fresnel.set_editor_property('exponent',3.0);fresnel.set_editor_property('base_reflect_fraction',.05)
opacity=g.lerp(g.c(.65),g.c(.94),fresnel)
fade=g.n(u.MaterialExpressionDepthFade);g.wire(opacity,fade,'Opacity');g.wire(g.c(8),fade,'FadeDistance');g.prop(fade,u.MaterialProperty.MP_OPACITY)
ML.recompile_material(m);assert E.save_loaded_asset(m,only_if_is_dirty=False)
water=actors['OH_SM_OH_Blockout_21'];water.modify();water.static_mesh_component.set_material(0,m)
basepath=OUT/'baseline.json'
if not basepath.exists():
    basepath.write_text(json.dumps({n:dict(position=[a.get_actor_location().x,a.get_actor_location().y,a.get_actor_location().z],rotation=[a.get_actor_rotation().pitch,a.get_actor_rotation().yaw,a.get_actor_rotation().roll]) for n,a in actors.items() if n.startswith('OH_FULL_13_')},indent=2))
base=load_current_json(basepath.read_text());old_submerged=load_current_json((OUT.parent/'v009/applied.json').read_text())['submerged_floor_tiles'];changes=[]
for n,b in base.items():
    x,y,z=b['position'];position=b['position'][:]
    if n in old_submerged:
        # Varied shallow depths while keeping the maximum vertical change under 5cm.
        drop=2.8+1.1*math.sin(x*.013+y*.005)+.7*math.cos(y*.017)
        position[2]-=drop
        a=actors[n];a.modify();a.set_actor_location(u.Vector(*position),False,False)
        changes.append(dict(label=n,position=position,drop_cm=drop))
assert len(changes)==47
shore_changes=[]
if (OUT/'SM_OH_ShoreSlab.fbx').exists():
    u.SystemLibrary.execute_console_command(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(),'Interchange.FeatureFlags.Import.FBX 0')
    opts=u.FbxImportUI();opts.automated_import_should_detect_type=False;opts.import_mesh=True;opts.import_as_skeletal=False;opts.import_materials=False;opts.import_textures=False;opts.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
    opts.static_mesh_import_data.combine_meshes=True;opts.static_mesh_import_data.auto_generate_collision=False;opts.static_mesh_import_data.convert_scene_unit=True;opts.static_mesh_import_data.normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
    task=u.AssetImportTask();task.filename=str(OUT/'SM_OH_ShoreSlab.fbx');task.destination_path=D+'/Meshes';task.automated=True;task.save=True;task.replace_existing=True;task.options=opts;task.factory=u.FbxFactory();AT.import_asset_tasks([task]);mesh=E.load_asset(task.imported_object_paths[0]);assert mesh
    mesh.set_material(0,E.load_asset(D+'/WeatheredMaterials/M_OH_Weathered_13'));mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);assert E.save_loaded_asset(mesh,only_if_is_dirty=False)
    # Small dry slabs at the shoreline only; never chip the large underlying collision floor.
    for n,b in base.items():
        a=actors[n];p=b['position'];s=a.get_actor_scale3d()
        if n=='OH_FULL_13_0276' or (-550<p[0]<500 and 650<p[1]<1250 and p[2]>-10 and n not in old_submerged):
            a.modify();a.static_mesh_component.set_static_mesh(mesh);shore_changes.append(n)
if APPLY:assert L.save_current_level()
(OUT/('applied.json' if APPLY else 'probe.json')).write_text(json.dumps(dict(map=MAP,material=m.get_name(),saved=APPLY,floor_changes=changes,shore_slabs=shore_changes,water_height_cm=2.2,translucent=True,refraction=False),indent=2))
script=(ROOT/'Content/Python/capture_hall_exposure.py').read_text().replace('ArtSource/OvergrownHall/Scene/v001','ArtSource/OvergrownHall/TripoReplacement/v012').replace("assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level('/Game/Constellation/Environments/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout')",'# Capture current probe without reloading the maintained map.').replace('unreal_exposure_fixed.png','unreal_shallows.png' if APPLY else 'probe.png')
script=script.replace('pp=next',"u.EditorLevelLibrary.set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation())\nu.EditorLevelLibrary.pilot_level_actor(cam)\npp=next").replace("'r.ScreenPercentage 100'","'ShowFlag.ReflectionEnvironment 1'")
exec(compile(script,'capture_shallows','exec'),globals())
