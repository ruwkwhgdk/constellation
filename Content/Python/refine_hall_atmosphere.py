"""v008 asymmetric moisture islands, varied vines, Tripo leaf cleanup and backlight."""
import unreal as u,json,random,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v008';OUT.mkdir(exist_ok=True)
D='/Game/Environment/OvergrownHall/TripoFull';MAP=D+'/Maps/L_OvergrownHall_TripoFull'
E=u.EditorAssetLibrary;ML=u.MaterialEditingLibrary;AT=u.AssetToolsHelpers.get_asset_tools()
A=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem);SM=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
assert L.load_level(MAP)
source=(ROOT/'Content/Python/apply_hall_growth_water.py').read_text();exec(source[source.index('class Graph:'):source.index('\nmoss_keys=')])
source=(ROOT/'Content/Python/paint_hall_surfaces.py').read_text();exec(source[source.index('def sample('):source.index('\nfor row in rows:')])
tex=E.load_asset(D+'/IllustratedTextures/T_OH_PaintedMineral');assert tex
# Large, deliberately asymmetric wet zones, in world cm. Zero outside their influence.
zones=[((-595,755,90),(190,280,230),.95),((-595,1420,495),(140,200,410),.78),((590,1130,680),(130,340,290),1),((590,1825,75),(200,180,145),.8),((-355,1950,210),(310,120,300),1),((340,1950,370),(150,100,280),.64),((85,1890,50),(95,240,130),.6),((-330,1080,4),(210,310,70),.7),((380,1570,4),(180,150,65),.6)]
materials={}
for key in ['01','02','03','04','05','09','11','12','13','26']:
    name='M_OH_Weathered_'+key;dest=D+'/WeatheredMaterials'
    mat=E.load_asset(dest+'/'+name) if E.does_asset_exist(dest+'/'+name) else AT.create_asset(name,dest,u.Material,u.MaterialFactoryNew())
    mat.modify();ML.delete_all_material_expressions(mat);g=Graph(mat);pos=g.n(u.MaterialExpressionWorldPosition)
    normal=g.n(u.MaterialExpressionVertexNormalWS);ab=g.n(u.MaterialExpressionAbs);g.wire(normal,ab)
    sharp=g.mul(ab,ab);sharp=g.mul(sharp,sharp);weights=[g.mask(sharp,i) for i in range(3)]
    total=g.add(g.add(weights[0],weights[1]),g.add(weights[2],g.c(.0001)))
    p=g.mul(pos,g.c(1/(240 if key=='13' else 330)))
    layers=[g.mul(sample(g,tex,pair(g,p,*axes),1),divide(g,w,total)) for axes,w in zip([(1,2),(0,2),(0,1)],weights)]
    base=g.mul(g.add(g.add(layers[0],layers[1]),layers[2]),g.color((.70,.83,.88)))
    wet=g.c(0)
    for center,radius,strength in zones:
        q=g.mul(g.sub(pos,g.color(center)),g.color(tuple(1/r for r in radius)))
        d=g.n(u.MaterialExpressionDotProduct);g.wire(q,d,'A');g.wire(q,d,'B')
        island=g.clamp(g.sub(g.c(1),d));wet=g.add(wet,g.mul(island,g.c(strength)))
    broad=g.noise(pos,.0035);detail=g.noise(pos,.010)
    # Large wet islands with sparse broken edges, no regular leopard-like speckling.
    warped=g.sub(g.add(wet,g.mul(g.sub(broad,g.c(.5)),g.c(.35))),g.c(.12))
    mask=g.mul(g.clamp(g.mul(warped,g.c(2.1))),g.clamp(g.mul(wet,g.c(5))))
    variation=g.add(g.c(.68),g.mul(detail,g.c(.22)))
    amount=g.mul(mask,variation)
    moss=g.lerp(g.color((.065,.14,.055)),g.color((.17,.25,.085)),broad)
    g.prop(g.lerp(base,moss,amount),u.MaterialProperty.MP_BASE_COLOR)
    g.prop(g.lerp(g.c(.90),g.c(.98),amount),u.MaterialProperty.MP_ROUGHNESS);g.prop(g.c(.1),u.MaterialProperty.MP_SPECULAR)
    ML.recompile_material(mat);assert E.save_loaded_asset(mat,only_if_is_dirty=False);materials[key]=mat

u.SystemLibrary.execute_console_command(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(),'Interchange.FeatureFlags.Import.FBX 0')
shapes=json.loads((OUT/'foliage_shapes.json').read_text());meshes={}
for row in shapes:
    key=row['id'];opts=u.FbxImportUI();opts.automated_import_should_detect_type=False;opts.import_mesh=True;opts.import_as_skeletal=False;opts.import_materials=False;opts.import_textures=False;opts.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
    opts.static_mesh_import_data.combine_meshes=True;opts.static_mesh_import_data.auto_generate_collision=False;opts.static_mesh_import_data.convert_scene_unit=True;opts.static_mesh_import_data.normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
    t=u.AssetImportTask();t.filename=str(OUT/(key+'_'+row['name'])/(row['mesh']+'.fbx'));t.destination_path=D+'/Meshes';t.automated=True;t.save=True;t.replace_existing=True;t.options=opts;t.factory=u.FbxFactory();AT.import_asset_tasks([t])
    mesh=E.load_asset(t.imported_object_paths[0]);mesh.set_material(0,E.load_asset(D+'/IllustratedMaterials/M_OH_Illustrated_'+key))
    if key=='19':
        original=E.load_asset(D+'/Meshes/SM_OH_Clean_19_Tree');body=mesh.get_editor_property('body_setup')
        body.set_editor_property('agg_geom',original.get_editor_property('body_setup').get_editor_property('agg_geom'))
        body.set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX);assert SM.get_simple_collision_count(mesh)>0
    assert E.save_loaded_asset(mesh,only_if_is_dirty=False);meshes[key]=mesh

actors={a.get_actor_label():a for a in A.get_all_level_actors()}
baseline=OUT/'baseline.json'
if not baseline.exists():
    record={}
    for name,a in actors.items():
        if name.startswith(('OH_Growth_','OH_Tripo_Tree_')) or name in ['OH_Sun','OH_Sky','OH_WindowFill','OH_ReferenceFog']:
            p=a.get_actor_location();r=a.get_actor_rotation();s=a.get_actor_scale3d();record[name]=dict(position=[p.x,p.y,p.z],rotation=[r.pitch,r.yaw,r.roll],scale=[s.x,s.y,s.z])
    baseline.write_text(json.dumps(record,indent=2))
baseline=json.loads(baseline.read_text());counts={};replaced={}
for name,a in actors.items():
    if name.startswith('OH_FULL_18_') and name not in baseline:
        p=a.get_actor_location();r=a.get_actor_rotation();s=a.get_actor_scale3d()
        baseline[name]=dict(position=[p.x,p.y,p.z],rotation=[r.pitch,r.yaw,r.roll],scale=[s.x,s.y,s.z])
(OUT/'baseline.json').write_text(json.dumps(baseline,indent=2))
for name,a in actors.items():
    key=name.split('_')[2] if name.startswith('OH_FULL_') else '19' if name.startswith('OH_Tripo_Tree_') else '26' if name.startswith('OH_STRUCTURE_Roof_') else None
    if name.startswith('OH_Growth_'):key='18' if '_Vine_' in name else '17'
    if key in materials:a.modify();a.static_mesh_component.set_material(0,materials[key]);counts[key]=counts.get(key,0)+1
    if key in meshes:a.modify();a.static_mesh_component.set_static_mesh(meshes[key]);replaced[key]=replaced.get(key,0)+1

rng=random.Random(928);placements=[]
for name in sorted(n for n in actors if n.startswith(('OH_Growth_','OH_FULL_18_'))):
    a=actors[name];b=baseline[name];p=b['position'][:];s=b['scale'][:];r=b['rotation'][:]
    # Keep wall attachment depth; vary along its tangent and vertical axes.
    side=abs(p[0])>540
    p[1 if side else 0]+=rng.uniform(-42,42)
    p[2]=max(4,p[2]+rng.uniform(-70,55))
    factor=rng.choice([.28,.48,.8,1.2,1.65])
    s[0]*=factor;s[2]*=rng.uniform(.55,1.25)
    a.set_actor_location(u.Vector(*p),False,False);a.set_actor_scale3d(u.Vector(*s))
    a.static_mesh_component.set_collision_profile_name('NoCollision')
    placements.append(dict(label=name,position=p,scale=s))

# Fixed exposure is preserved; direction and fill create warm rear light / cool interior.
sun=actors['OH_Sun'];sun.set_actor_rotation(u.Rotator(pitch=-32,yaw=-125,roll=0),False)
c=sun.get_component_by_class(u.DirectionalLightComponent);c.set_editor_property('intensity',21000);c.set_editor_property('light_source_angle',6);c.set_light_color(u.LinearColor(1,.83,.56,1));c.set_editor_property('volumetric_scattering_intensity',1.5)
c=actors['OH_Sky'].get_component_by_class(u.SkyLightComponent);c.set_editor_property('intensity',1.15);c.set_light_color(u.LinearColor(.60,.83,1,1))
fill=actors['OH_WindowFill'];fill.set_actor_location(u.Vector(-330,2050,770),False,False)
c=fill.get_component_by_class(u.RectLightComponent);c.set_editor_property('intensity',180000);c.set_light_color(u.LinearColor(1,.89,.65,1));c.set_editor_property('source_width',600);c.set_editor_property('source_height',680)
fog=actors['OH_ReferenceFog'].get_component_by_class(u.ExponentialHeightFogComponent);fog.set_editor_property('fog_density',.018);fog.set_editor_property('enable_volumetric_fog',True);fog.set_editor_property('volumetric_fog_scattering_distribution',.55)
assert L.save_current_level()
(OUT/'applied.json').write_text(json.dumps(dict(map=MAP,moss_material_instances=counts,wet_zones=zones,foliage_mesh_replacements=replaced,growth=placements,sun=dict(pitch=-32,yaw=-125,intensity=21000),sky_intensity=1.15,exposure=1024,water_preserved=True,playtest=False),indent=2))
runpy.run_path(str(ROOT/'Content/Python/capture_hall_atmosphere.py'))
