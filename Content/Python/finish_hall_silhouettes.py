from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u,json,runpy,math
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v021';D='/Game/Constellation/Environments/OvergrownHall/TripoFull';MAP='/Game/Constellation/Worlds/OvergrownHall/Maps/L_OvergrownHall_TripoFull'
E=u.EditorAssetLibrary;ML=u.MaterialEditingLibrary;AT=u.AssetToolsHelpers.get_asset_tools();A=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert L.load_level(MAP);actors={a.get_actor_label():a for a in A.get_all_level_actors()}
if not (OUT/'baseline.json').exists():
    data={}
    for n,a in actors.items():
        p=a.get_actor_location();s=a.get_actor_scale3d();r=a.get_actor_rotation();data[n]=dict(position=[p.x,p.y,p.z],scale=[s.x,s.y,s.z],rotation=[r.pitch,r.yaw,r.roll])
        if isinstance(a,u.StaticMeshActor):data[n].update(mesh=a.static_mesh_component.static_mesh.get_path_name() if a.static_mesh_component.static_mesh else None,materials=[a.static_mesh_component.get_material(i).get_path_name() if a.static_mesh_component.get_material(i) else None for i in range(a.static_mesh_component.get_num_materials())])
    (OUT/'baseline.json').write_text(json.dumps(data,indent=2))
for n,a in actors.items():
    if n.startswith('OH_Silhouette_'):A.destroy_actor(a)
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
source=(ROOT/'Content/Python/apply_hall_growth_water.py').read_text();exec(source[source.index('class Graph:'):source.index('\nmoss_keys=')])
def make(name,src):
    path=D+'/AtmosphereFinish/'+name;m=E.load_asset(path) if E.does_asset_exist(path) else E.duplicate_asset(src,path);assert m;m.modify();return m
def save(m):ML.recompile_material(m);assert E.save_loaded_asset(m,only_if_is_dirty=False)
archmat=make('M_OH_SlateArch',D+'/PainterlyFinish/M_OH_Weathered_04');g=Graph(archmat);pos=g.n(u.MaterialExpressionWorldPosition);n=g.noise(pos,.003)
g.prop(g.lerp(g.color((.12,.20,.22)),g.color((.28,.37,.36)),n),u.MaterialProperty.MP_BASE_COLOR);g.prop(g.c(.96),u.MaterialProperty.MP_ROUGHNESS);save(archmat)
roofmat=E.load_asset(D+'/PainterlyFinish/M_OH_CeilingSoft')
u.SystemLibrary.execute_console_command(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(),'Interchange.FeatureFlags.Import.FBX 0')
meshes={}
for row in load_current_json((OUT/'assets.json').read_text()):
    opts=u.FbxImportUI();opts.automated_import_should_detect_type=False;opts.import_mesh=True;opts.import_as_skeletal=False;opts.import_materials=False;opts.import_textures=False;opts.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
    opts.static_mesh_import_data.combine_meshes=True;opts.static_mesh_import_data.auto_generate_collision=False;opts.static_mesh_import_data.convert_scene_unit=True;opts.static_mesh_import_data.normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
    t=u.AssetImportTask();t.filename=str(OUT/(row['mesh']+'.fbx'));t.destination_path=D+'/Meshes';t.automated=True;t.save=True;t.replace_existing=True;t.options=opts;t.factory=u.FbxFactory();AT.import_asset_tasks([t]);m=E.load_asset(t.imported_object_paths[0]);m.set_material(0,archmat if row['kind']=='arch' else roofmat);m.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);assert E.save_loaded_asset(m,only_if_is_dirty=False);meshes[row['mesh']]=m
mapping={'0279':'A','0280':'C','0281':'B','0290':'B','0291':'A','0292':'C'};changed=[]
for n,a in actors.items():
    if n.startswith('OH_FULL_04_'):
        a.modify();a.static_mesh_component.set_material(0,archmat)
        if n[-4:] in mapping:a.static_mesh_component.set_static_mesh(meshes['SM_OH_FracturedSideArch'+mapping[n[-4:]]]);changed.append(n)
    if n.startswith('OH_FULL_10_'):
        a.modify();a.static_mesh_component.set_static_mesh(meshes['SM_OH_FracturedRoofTruss']);a.static_mesh_component.set_material(0,roofmat);changed.append(n)
# Root each hanging member at the underside of the closed roof; keep well above play space.
beam=E.load_asset(D+'/Meshes/SM_OH_Clean_11_BrokenBeam');box=beam.get_bounding_box();size=box.max-box.min;added=[]
assert size.x>size.y and size.x>size.z,(size.x,size.y,size.z)
for i,(side,y,length,dx) in enumerate([(-1,730,250,85),(1,890,185,110),(-1,1190,320,100),(1,1330,260,60),(-1,1680,170,75),(1,1810,245,125)]):
    start=u.Vector(side*470,y,1280-470*.24-18);end=start+u.Vector(-side*dx,35,-length)
    midpoint=(start+end)*.5;a=A.spawn_actor_from_class(u.StaticMeshActor,midpoint,u.MathLibrary.find_look_at_rotation(start,end));a.set_actor_label('OH_Silhouette_Hanging_%02d'%i);c=a.static_mesh_component;c.set_static_mesh(beam);c.set_material(0,roofmat);a.set_actor_scale3d(u.Vector((end-start).length()/size.x,.65,.65));center,_=a.get_actor_bounds(False);a.set_actor_location(a.get_actor_location()+midpoint-center,False,False);c.set_collision_profile_name('NoCollision');added.append(a.get_actor_label())
birdmat=make('M_OH_BirdCream',D+'/PainterlyFinish/M_OH_PigeonWarm');ML.delete_all_material_expressions(birdmat);g=Graph(birdmat);sample=g.n(u.MaterialExpressionTextureSample);sample.texture=E.load_asset('/Game/Constellation/Environments/OvergrownHall/Bird/Tripo/Textures/OH_Pigeon_Tripo_v001_basecolor');sample.sampler_type=u.MaterialSamplerType.SAMPLERTYPE_COLOR
color=g.lerp(sample,g.color((1,.92,.73)),g.c(.82));g.prop(color,u.MaterialProperty.MP_BASE_COLOR);g.prop(g.mul(color,g.c(750)),u.MaterialProperty.MP_EMISSIVE_COLOR);g.prop(g.c(.95),u.MaterialProperty.MP_ROUGHNESS);save(birdmat)
seq=E.load_asset(D+'/Sequences/LS_OvergrownHall_Flock');seq.modify();bird_scales={}
for i,binding in enumerate(seq.get_bindings()):
    n=binding.get_name();assert n.startswith('OH_Flock_Bird_'),n
    index=int(n.rsplit('_',1)[1])-1;scale=[.30,.43,.27,.58,.36,.48,.32][index%7];a=actors[n];a.modify();a.set_actor_scale3d(u.Vector(scale,scale,scale));a.skeletal_mesh_component.set_material(0,birdmat)
    track=next(t for t in binding.get_tracks() if isinstance(t,u.MovieScene3DTransformTrack));channels=track.get_sections()[0].get_all_channels()
    for ch in channels[6:9]:
        for key in ch.get_keys():key.set_value(scale)
    bird_scales[n]=scale
assert E.save_loaded_asset(seq,only_if_is_dirty=False);assert L.save_current_level()
(OUT/'applied.json').write_text(json.dumps(dict(map=MAP,changed_meshes=changed,added=added,bird_scales=bird_scales,playtest=False),indent=2))
runpy.run_path(str(ROOT/'Content/Python/capture_hall_silhouettes.py'))
