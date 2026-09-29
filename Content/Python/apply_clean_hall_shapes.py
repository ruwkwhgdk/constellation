"""Import source-guided retopology and replace all 532 environment placements."""
import unreal as u,json,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v005'
D='/Game/Environment/OvergrownHall/TripoFull';MAP=D+'/Maps/L_OvergrownHall_TripoFull'
E=u.EditorAssetLibrary;AT=u.AssetToolsHelpers.get_asset_tools();ML=u.MaterialEditingLibrary
L=u.get_editor_subsystem(u.LevelEditorSubsystem);A=u.get_editor_subsystem(u.EditorActorSubsystem);SM=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
assert L.load_level(MAP)
u.SystemLibrary.execute_console_command(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(),'Interchange.FeatureFlags.Import.FBX 0')
rows=json.loads((OUT/'shape_manifest.json').read_text());settings=json.loads((OUT.parent/'v004/applied.json').read_text())['materials'];meshes={};mats={}
for row in rows:
    key=row['id'];folder=OUT/(key+'_'+row['name'])
    opts=u.FbxImportUI();opts.automated_import_should_detect_type=False;opts.import_mesh=True;opts.import_as_skeletal=False;opts.import_materials=False;opts.import_textures=False;opts.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
    opts.static_mesh_import_data.combine_meshes=True;opts.static_mesh_import_data.auto_generate_collision=False;opts.static_mesh_import_data.convert_scene_unit=True
    opts.static_mesh_import_data.normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
    t=u.AssetImportTask();t.filename=str(folder/(row['mesh']+'.fbx'));t.destination_path=D+'/Meshes';t.automated=True;t.save=True;t.replace_existing=True;t.options=opts;t.factory=u.FbxFactory();AT.import_asset_tasks([t])
    mesh=E.load_asset(t.imported_object_paths[0]);assert isinstance(mesh,u.StaticMesh)
    if row['organic']:
        mat=E.load_asset(D+'/PaintedMaterials/M_OH_Painted_'+key)
    else:
        t=u.AssetImportTask();t.filename=str(folder/'basecolor.png');t.destination_path=D+'/CleanTextures';t.destination_name='T_OH_Clean_'+key;t.automated=True;t.save=True;t.replace_existing=True;AT.import_asset_tasks([t]);tex=E.load_asset(t.imported_object_paths[0]);assert tex
        name='M_OH_Clean_'+key;dest=D+'/CleanMaterials';path=dest+'/'+name
        mat=E.load_asset(path) if E.does_asset_exist(path) else AT.create_asset(name,dest,u.Material,u.MaterialFactoryNew())
        mat.modify();ML.delete_all_material_expressions(mat)
        def node(cls):return ML.create_material_expression(mat,cls)
        def scalar(v):
            n=node(u.MaterialExpressionConstant);n.r=v;return n
        def wire(a,output,b,input):assert ML.connect_material_expressions(a,output,b,input)
        def prop(n,output,p):assert ML.connect_material_property(n,output,p)
        sample=node(u.MaterialExpressionTextureSample);sample.texture=tex;sample.sampler_type=u.MaterialSamplerType.SAMPLERTYPE_COLOR
        # Preserve clean edge definition; softness comes from pigment, not blur.
        sample.set_editor_property('mip_value_mode',u.TextureMipValueMode.TMVM_MIP_BIAS);sample.set_editor_property('const_mip_value',0)
        color=node(u.MaterialExpressionConstant3Vector);color.constant=u.LinearColor(*settings[key]['tint'],1)
        lerp=node(u.MaterialExpressionLinearInterpolate);wire(sample,'RGB',lerp,'A');wire(color,'',lerp,'B');wire(scalar(.58 if key not in ['06','07','08','10','25','14'] else .42),'',lerp,'Alpha');prop(lerp,'',u.MaterialProperty.MP_BASE_COLOR)
        prop(scalar(.87),'',u.MaterialProperty.MP_ROUGHNESS);prop(scalar(.15),'',u.MaterialProperty.MP_SPECULAR);prop(scalar(0),'',u.MaterialProperty.MP_METALLIC)
        ML.recompile_material(mat);assert E.save_loaded_asset(mat,only_if_is_dirty=False)
    mesh.set_material(0,mat)
    body=mesh.get_editor_property('body_setup')
    if key in ['13','19']:
        source=E.load_asset(D+'/Meshes/SM_OH_T_13_Floor' if key=='13' else '/Game/Environment/OvergrownHall/TripoReplacement/Meshes/SM_OH_Tripo_Tree')
        body.set_editor_property('agg_geom',source.get_editor_property('body_setup').get_editor_property('agg_geom'))
        if key=='19' and SM.get_simple_collision_count(mesh)==0:
            # The original tree FBX's UCX was not retained by its old import.
            # Add a trunk-only box, never a box enclosing the entire canopy.
            agg=body.get_editor_property('agg_geom');box=u.KBoxElem()
            box.set_editor_property('center',u.Vector(0,0,130))
            for field,value in [('x',40.0),('y',40.0),('z',260.0)]:box.set_editor_property(field,value)
            agg.set_editor_property('box_elems',[box]);body.set_editor_property('agg_geom',agg)
        body.set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
        assert SM.get_simple_collision_count(mesh)>0,key
    elif key not in ['16','17','18']:
        body.set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    assert E.save_loaded_asset(mesh,only_if_is_dirty=False)
    meshes[key]=mesh;mats[key]=mat
counts={}
for actor in A.get_all_level_actors():
    label=actor.get_actor_label()
    key=label.split('_')[2] if label.startswith('OH_FULL_') else '19' if label.startswith('OH_Tripo_Tree_') else '26' if label.startswith('OH_STRUCTURE_Roof_') else None
    if key in meshes:
        actor.modify();actor.static_mesh_component.set_static_mesh(meshes[key]);actor.static_mesh_component.set_material(0,mats[key]);counts[key]=counts.get(key,0)+1
assert sum(counts.values())==532,counts
assert L.save_current_level()
(OUT/'applied.json').write_text(json.dumps(dict(map=MAP,instances=counts,total=532,architectural_retopology=16,organic_cleanup=5,playtest=False),indent=2))
runpy.run_path(str(ROOT/'Content/Python/verify_clean_hall_shapes.py'))
script=(ROOT/'Content/Python/capture_hall_exposure.py').read_text().replace('ArtSource/OvergrownHall/Scene/v001','ArtSource/OvergrownHall/TripoReplacement/v005').replace('/Game/Environment/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout',MAP).replace('unreal_exposure_fixed.png','unreal_clean.png')
exec(compile(script,'capture_clean_hall','exec'),globals())
