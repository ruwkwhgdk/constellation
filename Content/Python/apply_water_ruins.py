"""v011 incremental edit; preserves the approved v010 foliage, flock and lighting."""
from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u,json,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v011'
D='/Game/Constellation/Environments/OvergrownHall/TripoFull';MAP='/Game/Constellation/Worlds/OvergrownHall/Maps/L_OvergrownHall_TripoFull'
E=u.EditorAssetLibrary;ML=u.MaterialEditingLibrary;AT=u.AssetToolsHelpers.get_asset_tools()
L=u.get_editor_subsystem(u.LevelEditorSubsystem);A=u.get_editor_subsystem(u.EditorActorSubsystem)
assert L.load_level(MAP)
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
source=(ROOT/'Content/Python/apply_hall_growth_water.py').read_text();exec(source[source.index('class Graph:'):source.index('\nmoss_keys=')])
name='M_OH_RippleWater';dest=D+'/ReferenceMaterials'
m=E.load_asset(dest+'/'+name) if E.does_asset_exist(dest+'/'+name) else AT.create_asset(name,dest,u.Material,u.MaterialFactoryNew())
m.modify();ML.delete_all_material_expressions(m);m.set_editor_property('tangent_space_normal',False);g=Graph(m)
pos=g.n(u.MaterialExpressionWorldPosition);time=g.n(u.MaterialExpressionTime)
x=g.mask(pos,0);y=g.mask(pos,1)
# Analytic world-space normal avoids reliance on the old sheet's missing UV/tangents.
phases=[g.add(g.mul(g.add(x,g.mul(y,g.c(.36))),g.c(1/115)),g.mul(time,g.c(.075))),g.add(g.mul(g.add(y,g.mul(x,g.c(-.22))),g.c(1/73)),g.mul(time,g.c(-.052)))]
sin=[];cos=[]
for phase in phases:
    sn=g.n(u.MaterialExpressionSine);g.wire(phase,sn);sin.append(sn)
    cs=g.n(u.MaterialExpressionCosine);g.wire(phase,cs);cos.append(cs)
wave=g.add(g.mul(sin[0],g.c(.075)),g.mul(sin[1],g.c(.045)))
g.prop(g.mul(g.color((0,0,1)),wave),u.MaterialProperty.MP_WORLD_POSITION_OFFSET)
nx=g.add(g.mul(cos[0],g.c(-.025)),g.mul(cos[1],g.c(.008)))
ny=g.add(g.mul(cos[0],g.c(-.008)),g.mul(cos[1],g.c(-.025)))
normal=g.op(u.MaterialExpressionAppendVector,g.op(u.MaterialExpressionAppendVector,nx,ny),g.c(1))
norm=g.n(u.MaterialExpressionNormalize);g.wire(normal,norm);g.prop(norm,u.MaterialProperty.MP_NORMAL)
noise=g.noise(pos,.0025)
g.prop(g.lerp(g.color((.46,.66,.57)),g.color((.69,.82,.65)),noise),u.MaterialProperty.MP_BASE_COLOR)
g.prop(g.c(.92),u.MaterialProperty.MP_METALLIC)
g.prop(g.add(g.c(.035),g.mul(noise,g.c(.035))),u.MaterialProperty.MP_ROUGHNESS)
g.prop(g.color((3.5,8,6.5)),u.MaterialProperty.MP_EMISSIVE_COLOR)
ML.recompile_material(m);assert E.save_loaded_asset(m,only_if_is_dirty=False)
u.SystemLibrary.execute_console_command(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(),'Interchange.FeatureFlags.Import.FBX 0')
meshes={}
for row in load_current_json((OUT/'assets.json').read_text()):
    name=row['mesh'];opts=u.FbxImportUI();opts.automated_import_should_detect_type=False;opts.import_mesh=True;opts.import_as_skeletal=False;opts.import_materials=False;opts.import_textures=False;opts.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
    data=opts.static_mesh_import_data;data.combine_meshes=True;data.auto_generate_collision=False;data.convert_scene_unit=True;data.normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
    task=u.AssetImportTask();task.filename=str(OUT/(name+'.fbx'));task.destination_path=D+'/Meshes';task.automated=True;task.save=True;task.replace_existing=True;task.options=opts;task.factory=u.FbxFactory();AT.import_asset_tasks([task])
    mesh=E.load_asset(task.imported_object_paths[0]);assert mesh
    mesh.set_material(0,m if row['kind']=='water' else E.load_asset(D+'/WeatheredMaterials/M_OH_Weathered_04'))
    if row['kind']=='arch':mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    assert E.save_loaded_asset(mesh,only_if_is_dirty=False);meshes[name]=mesh
changes=[]
for label,variant in [('OH_FULL_04_0279','A'),('OH_FULL_04_0281','B'),('OH_FULL_04_0291','B')]:
    actor=actors[label];comp=actor.static_mesh_component
    # Restore input is stable across repeated application, not the last run's output.
    original='SM_OH_Chipped_04' if label in load_current_json((OUT.parent/'v009/applied.json').read_text())['chipped'] else 'SM_OH_Clean_04_SideArch'
    before=D+'/Meshes/'+original+'.'+original
    actor.modify();comp.set_static_mesh(meshes['SM_OH_BrokenArch'+variant]);changes.append(dict(label=label,mesh=comp.static_mesh.get_name(),previous=before))
water=actors['OH_SM_OH_Blockout_21'];water.modify();water.static_mesh_component.set_static_mesh(meshes['SM_OH_RippleSheet']);water.static_mesh_component.set_material(0,m);water.static_mesh_component.set_collision_profile_name('NoCollision')
assert L.save_current_level()
(OUT/'applied.json').write_text(json.dumps(dict(map=MAP,changes=changes,water_mesh='SM_OH_RippleSheet',water_material=m.get_name(),water_max_displacement_cm=.12,physical_transmission=False,foliage_version='v010'),indent=2))
runpy.run_path(str(ROOT/'Content/Python/capture_water_ruins.py'))
