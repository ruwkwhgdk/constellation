"""v010: Tripo stem geometry + bowed masked painted leaf clusters."""
import unreal as u,json,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v010'
D='/Game/Constellation/Environments/OvergrownHall/TripoFull';MAP='/Game/Constellation/Worlds/OvergrownHall/Maps/L_OvergrownHall_TripoFull'
E=u.EditorAssetLibrary;ML=u.MaterialEditingLibrary;AT=u.AssetToolsHelpers.get_asset_tools();L=u.get_editor_subsystem(u.LevelEditorSubsystem);A=u.get_editor_subsystem(u.EditorActorSubsystem);SM=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
assert L.load_level(MAP)
source=(ROOT/'Content/Python/apply_hall_growth_water.py').read_text();exec(source[source.index('class Graph:'):source.index('\nmoss_keys=')])
task=u.AssetImportTask();task.filename=str(OUT/'painted_leaves.png');task.destination_path=D+'/FoliagePaint';task.destination_name='T_OH_PaintedLeaves';task.automated=True;task.replace_existing=True;task.save=True;AT.import_asset_tasks([task]);tex=E.load_asset(D+'/FoliagePaint/T_OH_PaintedLeaves');assert tex
tex.set_editor_property('srgb',True);tex.set_editor_property('power_of_two_mode',u.TexturePowerOfTwoSetting.RESIZE_TO_SPECIFIC_RESOLUTION);tex.set_editor_property('resize_during_build_x',1024);tex.set_editor_property('resize_during_build_y',1024);tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_DEFAULT);tex.set_editor_property('compression_no_alpha',False);tex.set_editor_property('never_stream',False);tex.set_editor_property('mip_gen_settings',u.TextureMipGenSettings.TMGS_SIMPLE_AVERAGE)
tex.set_editor_property('do_scale_mips_for_alpha_coverage',True);tex.set_editor_property('alpha_coverage_thresholds',u.Vector4(0,0,0,.3));E.save_loaded_asset(tex)
materials={}
for far in [False,True]:
    name='M_OH_LeafFar' if far else 'M_OH_LeafNear';dest=D+'/FoliagePaint';mat=E.load_asset(dest+'/'+name) if E.does_asset_exist(dest+'/'+name) else AT.create_asset(name,dest,u.Material,u.MaterialFactoryNew())
    mat.modify();ML.delete_all_material_expressions(mat);mat.set_editor_property('blend_mode',u.BlendMode.BLEND_MASKED);mat.set_editor_property('two_sided',True);mat.set_editor_property('opacity_mask_clip_value',.3);mat.set_editor_property('shading_model',u.MaterialShadingModel.MSM_TWO_SIDED_FOLIAGE)
    g=Graph(mat);sample=g.n(u.MaterialExpressionTextureSample);sample.texture=tex;sample.sampler_type=u.MaterialSamplerType.SAMPLERTYPE_COLOR
    sample.set_editor_property('mip_value_mode',u.TextureMipValueMode.TMVM_MIP_BIAS);sample.set_editor_property('const_mip_value',1 if far else 0)
    color=g.lerp(sample,g.color((.35,.55,.18)),g.c(.35 if far else .08))
    g.prop(color,u.MaterialProperty.MP_BASE_COLOR);g.prop(sample,u.MaterialProperty.MP_OPACITY_MASK,'A');g.prop(g.mul(color,g.c(.5)),u.MaterialProperty.MP_SUBSURFACE_COLOR);g.prop(g.c(.55),u.MaterialProperty.MP_OPACITY)
    g.prop(g.c(.95),u.MaterialProperty.MP_ROUGHNESS);g.prop(g.c(.08),u.MaterialProperty.MP_SPECULAR);g.prop(g.mul(color,g.c(8 if far else 1.5)),u.MaterialProperty.MP_EMISSIVE_COLOR)
    ML.recompile_material(mat);assert E.save_loaded_asset(mat,only_if_is_dirty=False);materials['far' if far else 'near']=mat
u.SystemLibrary.execute_console_command(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(),'Interchange.FeatureFlags.Import.FBX 0')
meshes={}
for kind in ['Tree','Shrub','Crown']:
    name='SM_OH_Painted'+kind;opts=u.FbxImportUI();opts.automated_import_should_detect_type=False;opts.import_mesh=True;opts.import_as_skeletal=False;opts.import_materials=False;opts.import_textures=False;opts.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
    opts.static_mesh_import_data.combine_meshes=True;opts.static_mesh_import_data.auto_generate_collision=False;opts.static_mesh_import_data.convert_scene_unit=True;opts.static_mesh_import_data.normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
    t=u.AssetImportTask();t.filename=str(OUT/(name+'.fbx'));t.destination_path=D+'/Meshes';t.automated=True;t.save=True;t.replace_existing=True;t.options=opts;t.factory=u.FbxFactory();AT.import_asset_tasks([t]);mesh=E.load_asset(t.imported_object_paths[0]);assert mesh
    mesh.set_material(0,materials['near'])
    if kind!='Crown':mesh.set_material(1,E.load_asset(D+'/IllustratedMaterials/M_OH_Illustrated_'+('19' if kind=='Tree' else '17')))
    if kind=='Tree':
        old=E.load_asset(D+'/Meshes/SM_OH_Soft_19_Tree');body=mesh.get_editor_property('body_setup');body.set_editor_property('agg_geom',old.get_editor_property('body_setup').get_editor_property('agg_geom'));body.set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX);assert SM.get_simple_collision_count(mesh)>0
    E.save_loaded_asset(mesh);meshes[kind]=mesh
counts={};changes=[]
for actor in A.get_all_level_actors():
    comp=actor.get_component_by_class(u.StaticMeshComponent)
    if not comp or not comp.static_mesh:continue
    old=comp.static_mesh.get_name();kind={'SM_OH_Soft_19_Tree':'Tree','SM_OH_Soft_17_Shrub':'Shrub','SM_OH_TripoCrown':'Crown','SM_OH_PaintedTree':'Tree','SM_OH_PaintedShrub':'Shrub','SM_OH_PaintedCrown':'Crown'}.get(old)
    if not kind:continue
    name=actor.get_actor_label();far=kind=='Crown' and actor.get_actor_location().y>2900
    actor.modify();comp.set_static_mesh(meshes[kind]);comp.set_material(0,materials['far' if far else 'near'])
    if kind!='Crown':comp.set_material(1,meshes[kind].get_material(1))
    else:comp.set_collision_profile_name('NoCollision')
    counts[kind]=counts.get(kind,0)+1;changes.append(dict(label=name,kind=kind,far=far))
assert counts['Tree']==19 and counts['Crown']==54 and counts['Shrub']>=69,counts
assert L.save_current_level()
(OUT/'applied.json').write_text(json.dumps(dict(map=MAP,counts=counts,changes=changes,light_water_flock_unchanged=True,playtest=False,performance_test=False),indent=2))
runpy.run_path(str(ROOT/'Content/Python/capture_painted_hall_foliage.py'))
