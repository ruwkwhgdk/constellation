"""v013: rear ruin silhouette, localized growing seams, lighting and shoreline debris."""
import unreal as u,json,random,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v013';D='/Game/Environment/OvergrownHall/TripoFull';MAP=D+'/Maps/L_OvergrownHall_TripoFull'
E=u.EditorAssetLibrary;ML=u.MaterialEditingLibrary;AT=u.AssetToolsHelpers.get_asset_tools();L=u.get_editor_subsystem(u.LevelEditorSubsystem);A=u.get_editor_subsystem(u.EditorActorSubsystem)
assert L.load_level(MAP)
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
if not (OUT/'baseline.json').exists():
    (OUT/'baseline.json').write_text(json.dumps({n:dict(mesh=a.static_mesh_component.static_mesh.get_path_name(),materials=[a.static_mesh_component.get_material(i).get_path_name() if a.static_mesh_component.get_material(i) else None for i in range(a.static_mesh_component.get_num_materials())]) for n,a in actors.items() if n.startswith('OH_FULL_') and a.get_component_by_class(u.StaticMeshComponent)},indent=2))
for n,a in actors.items():
    if n.startswith('OH_Finish_'):A.destroy_actor(a)
# Reuse only pure graph/helper definitions and the existing world-projected paint recipe.
source=(ROOT/'Content/Python/apply_hall_growth_water.py').read_text();exec(source[source.index('class Graph:'):source.index('\nmoss_keys=')])
source=(ROOT/'Content/Python/paint_hall_surfaces.py').read_text();exec(source[source.index('def sample('):source.index('\nfor row in rows:')])
tex=E.load_asset(D+'/IllustratedTextures/T_OH_PaintedMineral')
source=(ROOT/'Content/Python/refine_hall_atmosphere.py').read_text();block=source[source.index('# Large,'):source.index('\nu.SystemLibrary')]
block=block.replace("['01','02','03','04','05','09','11','12','13','26']","['05','09']").replace("D+'/WeatheredMaterials'","D+'/FinishMaterials'")
block=block.replace('materials={}',"zones += [((470,1943,280),(105,75,155),1.1),((-390,1943,275),(110,70,160),1.0),((575,1943,760),(55,75,220),.95),((-500,1943,650),(65,75,170),.8)]\nmaterials={}")
exec(compile(block,'finish_seam_materials','exec'))
u.SystemLibrary.execute_console_command(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(),'Interchange.FeatureFlags.Import.FBX 0')
meshes={}
for row in json.loads((OUT/'assets.json').read_text()):
    key=row['id'];opts=u.FbxImportUI();opts.automated_import_should_detect_type=False;opts.import_mesh=True;opts.import_as_skeletal=False;opts.import_materials=False;opts.import_textures=False;opts.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
    opts.static_mesh_import_data.combine_meshes=True;opts.static_mesh_import_data.auto_generate_collision=False;opts.static_mesh_import_data.convert_scene_unit=True;opts.static_mesh_import_data.normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
    t=u.AssetImportTask();t.filename=str(OUT/(row['mesh']+'.fbx'));t.destination_path=D+'/Meshes';t.automated=True;t.save=True;t.replace_existing=True;t.options=opts;t.factory=u.FbxFactory();AT.import_asset_tasks([t]);mesh=E.load_asset(t.imported_object_paths[0]);assert mesh
    mat=materials[key] if key in materials else E.load_asset(D+'/IllustratedMaterials/M_OH_Illustrated_'+key);mesh.set_material(0,mat)
    mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);assert E.save_loaded_asset(mesh,only_if_is_dirty=False);meshes[key]=mesh
changes=[]
targets={'05':['OH_FULL_05_0226','OH_FULL_05_0229','OH_FULL_05_0278'],'06':['OH_FULL_06_0301','OH_FULL_06_0313','OH_FULL_06_0306'],'07':['OH_FULL_07_0303'],'09':['OH_FULL_09_0235','OH_FULL_09_0238','OH_FULL_09_0231']}
for key,names in targets.items():
    for name in names:
        a=actors[name];a.modify();c=a.static_mesh_component;c.set_static_mesh(meshes[key]);c.set_material(0,meshes[key].get_material(0));changes.append(dict(label=name,mesh=meshes[key].get_name()))
seams=[]
for name,a in actors.items():
    if name.startswith(('OH_FULL_05_','OH_FULL_09_')) and a.get_actor_location().y>1900:
        a.modify();a.static_mesh_component.set_material(0,materials[name.split('_')[2]]);seams.append(name)
added=[];rng=random.Random(913)
def place(kind,mesh,mat,pos,scale,rotation=(0,0,0)):
    rot=u.Rotator(pitch=rotation[0],yaw=rotation[1],roll=rotation[2]);a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*pos),rot);label='OH_Finish_'+kind+'_%03d'%len(added);a.set_actor_label(label);a.set_actor_scale3d(u.Vector(*scale));c=a.static_mesh_component;c.set_static_mesh(mesh);c.set_material(0,mat);c.set_collision_profile_name('NoCollision');added.append(dict(label=label,kind=kind,position=pos,scale=scale,mesh=mesh.get_name()));return a
vine=E.load_asset(D+'/Meshes/SM_OH_Soft_18_Vine');vm=E.load_asset(D+'/IllustratedMaterials/M_OH_Illustrated_18')
crown=E.load_asset(D+'/Meshes/SM_OH_PaintedCrown');cm=E.load_asset(D+'/FoliagePaint/M_OH_LeafNear')
# Roots touch rear masonry/frames; trails descend from the broken sill and beam ends.
for i,(x,z) in enumerate([(485,270),(445,292),(-385,265),(-438,290),(520,740),(565,810),(-510,688),(-455,735),(230,722)]):
    sy=.55+rng.random()*.25;length=.40+rng.random()*.42
    place('AttachedVine',vine,vm,(x,1940,z),(.7+rng.random()*.4,sy,length),(180,rng.uniform(-9,9),rng.uniform(-6,6)))
    if i in [0,2,4,6,8]:place('SeamLeaves',crown,cm,(x,1935,z-10),(.10,.09,.12),(0,rng.uniform(0,360),0))
# Broken stepping fragments are shallow decorative stones, with the continuous floor below.
slab=E.load_asset(D+'/Meshes/SM_OH_ShoreSlab');smat=E.load_asset(D+'/WeatheredMaterials/M_OH_Weathered_13')
for i,(x,y) in enumerate([(-460,540),(-405,590),(-480,760),(-330,820),(400,660),(440,735),(370,875),(-240,1120),(325,1220)]):
    place('ShoreFragment',slab,smat,(x,y,-1.9 if i%3 else -3.1),(.16+rng.random()*.13,.13+rng.random()*.13,.19+rng.random()*.13),(rng.uniform(-2,2),rng.uniform(0,180),rng.uniform(-2,2)))
rubble=E.load_asset(D+'/Meshes/SM_OH_Clean_15_Rubble');rm=E.load_asset(D+'/IllustratedMaterials/M_OH_Illustrated_15')
for x,y in [(-515,730),(-430,865),(-360,1160),(475,750),(380,950),(430,1350)]:
    place('SubmergedRubble',rubble,rm,(x,y,-4),(.32,.28,.21),(0,rng.uniform(0,360),0))
# Keep the reference sun direction and fixed exposure; separate cool fill from warm focus.
for label in ['OH_Sun','OH_Sky','OH_WindowFill','OH_Exposure']:actors[label].modify()
c=actors['OH_Sun'].get_component_by_class(u.DirectionalLightComponent);c.set_editor_property('intensity',17500);c.set_light_color(u.LinearColor(1,.86,.65,1))
c=actors['OH_Sky'].get_component_by_class(u.SkyLightComponent);c.set_editor_property('intensity',1.35);c.set_light_color(u.LinearColor(.38,.70,1,1))
c=actors['OH_WindowFill'].get_component_by_class(u.RectLightComponent);c.set_editor_property('intensity',200000)
spot=A.spawn_actor_from_class(u.SpotLight,u.Vector(440,1710,840),u.MathLibrary.find_look_at_rotation(u.Vector(440,1710,840),u.Vector(120,1020,30)));spot.set_actor_label('OH_Finish_FocalSun');c=spot.get_component_by_class(u.SpotLightComponent);c.set_mobility(u.ComponentMobility.MOVABLE)
for key,val in [('intensity_units',u.LightUnits.CANDELAS),('intensity',300000),('attenuation_radius',1600),('inner_cone_angle',12),('outer_cone_angle',27),('source_radius',75),('volumetric_scattering_intensity',.65)]:c.set_editor_property(key,val)
c.set_light_color(u.LinearColor(1,.86,.60,1))
pp=actors['OH_Exposure'];s=pp.get_editor_property('settings')
for key,value in [('color_gain',u.Vector4(.96,1.03,1.06,1)),('color_contrast',u.Vector4(.94,.94,.94,1)),('color_gamma',u.Vector4(1.08,1.09,1.10,1))]:s.set_editor_property('override_'+key,True);s.set_editor_property(key,value)
pp.set_editor_property('settings',s)
assert L.save_current_level()
(OUT/'applied.json').write_text(json.dumps(dict(map=MAP,architecture=changes,seam_material_actors=seams,added=added,focal_light='OH_Finish_FocalSun',sun_intensity=17500,sky_intensity=1.35,water_version='v012',playtest='user',performance_test=False),indent=2))
runpy.run_path(str(ROOT/'Content/Python/capture_hall_final_art.py'))
