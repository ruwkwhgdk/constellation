"""Import the approved kit. No map changes in this script."""
from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u,json
from pathlib import Path
R=Path(u.Paths.project_dir());S=R/'ArtSource/SubwayEntrance/Production/v001';D='/Game/Constellation/Environments/SubwayEntrance'
AT=u.AssetToolsHelpers.get_asset_tools();E=u.EditorAssetLibrary;M=u.MaterialEditingLibrary
manifest=load_current_json((S/'manifest.json').read_text());spec=load_current_json((S/'materials.json').read_text())
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();u.SystemLibrary.execute_console_command(world,'Interchange.FeatureFlags.Import.FBX 0')
def task(f,d,options=None):
    t=u.AssetImportTask();t.filename=str(f);t.destination_path=d;t.automated=True;t.replace_existing=True;t.save=True
    if options:t.options=options;t.factory=u.FbxFactory()
    AT.import_asset_tasks([t]);assert t.imported_object_paths,t.filename;return E.load_asset(t.imported_object_paths[0])
tex=task(S/'textures/T_SE_StationSign.png',D+'/Textures')
def constant(mat,v):
    n=M.create_material_expression(mat,u.MaterialExpressionConstant);n.r=v;return n
def connect(mat,n,prop,pin=''):M.connect_material_property(n,pin,prop)
mats={}
for key,sp in spec.items():
    name='M_SE_'+key;path=D+'/Materials/'+name
    mat=E.load_asset(path) if E.does_asset_exist(path) else AT.create_asset(name,D+'/Materials',u.Material,u.MaterialFactoryNew());M.delete_all_material_expressions(mat)
    if sp['texture']:
        n=M.create_material_expression(mat,u.MaterialExpressionTextureSample);n.texture=tex;connect(mat,n,u.MaterialProperty.MP_BASE_COLOR,'RGB')
    else:
        n=M.create_material_expression(mat,u.MaterialExpressionConstant3Vector);n.constant=u.LinearColor(*sp['color'],1)
        if key in ['Stone','WarmTile','Soffit']:
            noise=M.create_material_expression(mat,u.MaterialExpressionNoise);noise.set_editor_property('scale',.004);noise.set_editor_property('quality',1);noise.set_editor_property('levels',1)
            mul=M.create_material_expression(mat,u.MaterialExpressionMultiply);M.connect_material_expressions(noise,'',mul,'A');M.connect_material_expressions(constant(mat,.025),'',mul,'B')
            add=M.create_material_expression(mat,u.MaterialExpressionAdd);M.connect_material_expressions(mul,'',add,'A');M.connect_material_expressions(constant(mat,.98),'',add,'B')
            tint=M.create_material_expression(mat,u.MaterialExpressionMultiply);M.connect_material_expressions(n,'',tint,'A');M.connect_material_expressions(add,'',tint,'B');n=tint
        connect(mat,n,u.MaterialProperty.MP_BASE_COLOR)
    connect(mat,constant(mat,sp['roughness']),u.MaterialProperty.MP_ROUGHNESS);connect(mat,constant(mat,sp['metallic']),u.MaterialProperty.MP_METALLIC)
    if sp['glass']:
        mat.set_editor_property('blend_mode',u.BlendMode.BLEND_TRANSLUCENT);mat.set_editor_property('two_sided',True);connect(mat,constant(mat,.23),u.MaterialProperty.MP_OPACITY)
    if sp['emission']:
        em=M.create_material_expression(mat,u.MaterialExpressionConstant3Vector);em.constant=u.LinearColor(*[v*sp['emission'] for v in sp['color']],1);connect(mat,em,u.MaterialProperty.MP_EMISSIVE_COLOR)
    M.recompile_material(mat);E.save_loaded_asset(mat);mats[key]=mat
opts=u.FbxImportUI();opts.import_mesh=True;opts.import_as_skeletal=False;opts.import_materials=False;opts.import_textures=False;opts.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
d=opts.static_mesh_import_data;d.combine_meshes=True;d.auto_generate_collision=False;d.one_convex_hull_per_ucx=True;d.convert_scene_unit=True;d.transform_vertex_to_absolute=False;d.generate_lightmap_u_vs=True
checks=[]
for row in manifest['assets']:
    mesh=task(S/'FBX'/(row['name']+'.fbx'),D+'/Meshes',opts)
    for i,slot in enumerate(mesh.get_editor_property('static_materials')):
        key=str(slot.material_slot_name);assert key in mats,(row['name'],key);mesh.set_material(i,mats[key])
    b=mesh.get_bounding_box();dims=b.max-b.min;actual=[dims.x,dims.y,dims.z]
    assert all(abs(a-b)<.2 for a,b in zip(actual,row['dimensions_cm'])),(row['name'],actual,row['dimensions_cm'])
    g=mesh.get_editor_property('body_setup').get_editor_property('agg_geom');count=sum(len(g.get_editor_property(p)) for p in ['convex_elems','box_elems','sphere_elems','sphyl_elems'])
    assert count==row['collision_hulls'],(row['name'],count,row['collision_hulls'])
    E.save_loaded_asset(mesh);checks.append(dict(name=row['name'],bounds_cm=actual,collision_hulls=count))
island=task(S/'FBX/SM_SE_IslandWithStairwell.fbx',D+'/Meshes',opts)
body=island.get_editor_property('body_setup');body.set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
E.save_loaded_asset(island)
(S/'unreal_import.json').write_text(json.dumps(dict(assets=checks,island_collision=str(body.get_editor_property('collision_trace_flag')),maps_changed=False),indent=2),encoding='utf-8')
u.log('SUBWAY_IMPORT_OK')
