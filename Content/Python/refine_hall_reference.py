"""v009 staged reference pass: forest, then light/water/weathering/framing/flock."""
from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u,json,math,random,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v009'
D='/Game/Constellation/Environments/OvergrownHall/TripoFull';MAP='/Game/Constellation/Worlds/OvergrownHall/Maps/L_OvergrownHall_TripoFull';STAGE=globals().get('STAGE',1)
if STAGE==1 and (OUT/'applied.json').exists() and load_current_json((OUT/'applied.json').read_text()).get('stage')==2:
    raise RuntimeError('This level is already at stage 2. Reapply with finish_hall_reference.py, not the forest-only entry point.')
E=u.EditorAssetLibrary;AT=u.AssetToolsHelpers.get_asset_tools();ML=u.MaterialEditingLibrary
A=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert L.load_level(MAP)
u.SystemLibrary.execute_console_command(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(),'Interchange.FeatureFlags.Import.FBX 0')
meshes={}
for row in load_current_json((OUT/'assets.json').read_text()):
    path=D+'/Meshes/'+row['mesh']
    if not E.does_asset_exist(path) or row['kind']=='water':
        opts=u.FbxImportUI();opts.automated_import_should_detect_type=False;opts.import_mesh=True;opts.import_as_skeletal=False;opts.import_materials=False;opts.import_textures=False;opts.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
        opts.static_mesh_import_data.combine_meshes=True;opts.static_mesh_import_data.auto_generate_collision=False;opts.static_mesh_import_data.convert_scene_unit=True;opts.static_mesh_import_data.normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
        t=u.AssetImportTask();t.filename=str(OUT/(row['mesh']+'.fbx'));t.destination_path=D+'/Meshes';t.automated=True;t.save=True;t.replace_existing=True;t.options=opts;t.factory=u.FbxFactory();AT.import_asset_tasks([t])
    mesh=E.load_asset(path);assert mesh
    if row['kind'].startswith('chip'):mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    E.save_loaded_asset(mesh);meshes[row['kind']]=mesh
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
baseline=OUT/'baseline.json'
if not baseline.exists():
    data={}
    for n,a in actors.items():
        if n.startswith(('OH_FULL_','OH_STRUCTURE_','OH_Tripo_Tree_')):
            p=a.get_actor_location();s=a.get_actor_scale3d();r=a.get_actor_rotation();data[n]=dict(position=[p.x,p.y,p.z],scale=[s.x,s.y,s.z],rotation=[r.pitch,r.yaw,r.roll],mesh=a.static_mesh_component.static_mesh.get_path_name())
    baseline.write_text(json.dumps(data,indent=2))
base=load_current_json(baseline.read_text())
for n,a in list(actors.items()):
    if n.startswith('OH_Refine_'):A.destroy_actor(a)
source=(ROOT/'Content/Python/apply_hall_growth_water.py').read_text();exec(source[source.index('class Graph:'):source.index('\nmoss_keys=')])
def material(name):
    dest=D+'/ReferenceMaterials';m=E.load_asset(dest+'/'+name) if E.does_asset_exist(dest+'/'+name) else AT.create_asset(name,dest,u.Material,u.MaterialFactoryNew());m.modify();ML.delete_all_material_expressions(m);return m
def pigment(name,low,high,emission):
    m=material(name);m.set_editor_property('two_sided',True);g=Graph(m)
    t=g.n(u.MaterialExpressionTextureSample);t.texture=E.load_asset('/Game/Constellation/Environments/OvergrownHall/TripoReplacement/Textures/T_Tree_basecolor');t.sampler_type=u.MaterialSamplerType.SAMPLERTYPE_COLOR
    t.set_editor_property('mip_value_mode',u.TextureMipValueMode.TMVM_MIP_BIAS);t.set_editor_property('const_mip_value',3)
    gray=g.n(u.MaterialExpressionDesaturation);g.wire(t,gray);g.wire(g.c(1),gray,'Fraction')
    c=g.lerp(g.color(low),g.color(high),g.clamp(g.add(g.c(.18),g.mul(gray,g.c(.9)))))
    g.prop(c,u.MaterialProperty.MP_BASE_COLOR);g.prop(g.mul(c,g.c(emission)),u.MaterialProperty.MP_EMISSIVE_COLOR);g.prop(g.c(.95),u.MaterialProperty.MP_ROUGHNESS);g.prop(g.c(.08),u.MaterialProperty.MP_SPECULAR)
    ML.recompile_material(m);E.save_loaded_asset(m);return m
near=pigment('M_OH_CrownNear',(.065,.20,.085),(.40,.58,.15),1.5)
far=pigment('M_OH_CrownFar',(.24,.42,.20),(.65,.80,.32),8)
placements=[]
def place(kind,mesh,mat,p,s,yaw=0):
    n='OH_Refine_'+kind+'_%03d'%len(placements);a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*p),u.Rotator(pitch=0,yaw=yaw,roll=0));a.set_actor_label(n);a.set_actor_scale3d(u.Vector(*s));a.static_mesh_component.set_static_mesh(mesh);a.static_mesh_component.set_material(0,mat);a.static_mesh_component.set_collision_profile_name('NoCollision')
    placements.append(dict(label=n,kind=kind,position=p,scale=s,mesh=mesh.get_path_name()));return a
rng=random.Random(929)
# Layered crowns fill lower windows; their height varies rather than making a hedge line.
for row,y in enumerate([2520,3150,3900]):
    for i,x in enumerate(range(-1600,1800,400)):
        p=(x+rng.uniform(-130,130),y+rng.uniform(-130,150),rng.uniform(380,520))
        s=(rng.uniform(.9,1.4),rng.uniform(.85,1.25),rng.uniform(1.4,2.1))
        place('Forest',meshes['crown'],far if row else near,p,s,rng.uniform(0,360))
for side in [-1,1]:
    for y in [480,1000,1580,2100]:
        place('Forest',meshes['crown'],near,(side*rng.uniform(1050,1350),y,230+rng.uniform(-50,70)),(1.0,1.2,1.3),rng.uniform(0,360))
# Additional crown volumes mask the very exposed bonsai-like forks without changing trunks.
for n,b in base.items():
    if n.startswith('OH_Tripo_Tree_'):
        p=b['position'];s=b['scale'];place('Canopy',meshes['crown'],near,(p[0]+rng.uniform(-90,90),p[1],p[2]+310*s[2]),(.7*s[0],.8*s[1],1.1*s[2]),rng.uniform(0,360))
# Existing shrubs join low, broad clusters; keep foreground center clear for walking.
for n,b in base.items():
    if n.startswith('OH_FULL_17_'):
        a=actors[n];p=b['position'][:];s=b['scale'][:]
        s=[s[0]*1.18,s[1]*1.12,s[2]*.68]
        a.set_actor_scale3d(u.Vector(*s))
        if p[1]<1400 and abs(p[0])<290:p[0]+=190 if p[0]>0 else -190
        a.set_actor_location(u.Vector(*p),False,False)
report=dict(stage=STAGE,added=placements,playtest=False)
if STAGE>=2:
    # 2. Light: soften hard window shadows and add warm transmission through rear foliage.
    actors['OH_Sun'].set_actor_rotation(u.Rotator(pitch=-32,yaw=-55,roll=0),False)
    c=actors['OH_Sun'].get_component_by_class(u.DirectionalLightComponent);c.set_editor_property('light_source_angle',12);c.set_editor_property('intensity',19000)
    c=actors['OH_WindowFill'].get_component_by_class(u.RectLightComponent);c.set_editor_property('intensity',260000);c.set_editor_property('source_width',850);c.set_editor_property('source_height',800)
    fog=actors['OH_ReferenceFog'].get_component_by_class(u.ExponentialHeightFogComponent);fog.set_editor_property('fog_density',.023);fog.set_editor_property('volumetric_fog_scattering_distribution',.65)
    # 3. Water: preserve the proven reflective shader, change actual shoreline geometry.
    water=actors['OH_SM_OH_Blockout_21'];water.static_mesh_component.set_static_mesh(meshes['water']);water.set_actor_location(u.Vector(),False,False);water.set_actor_scale3d(u.Vector(1,1,1));water.static_mesh_component.set_collision_profile_name('NoCollision')
    lowered=[]
    for n,b in base.items():
        if n.startswith('OH_FULL_13_'):
            p=b['position'][:];x,y=p[:2]
            pond=(x/625)**2+((y-700)/860)**2<.88
            island=((x-120)/150)**2+((y-1040)/150)**2<1 or ((x+300)/90)**2+((y-770)/140)**2<1
            if pond and not island:p[2]-=1.0;lowered.append(n)
            actors[n].set_actor_location(u.Vector(*p),False,False)
    report['submerged_floor_tiles']=lowered
    # Slight animated roughness gives soft changing reflection, no explicit normal (v006 constraint).
    watermat=material('M_OH_QuietWater');g=Graph(watermat);g.prop(g.color((.62,.80,.70)),u.MaterialProperty.MP_BASE_COLOR);g.prop(g.c(1),u.MaterialProperty.MP_METALLIC)
    g.prop(g.color((3,9,8)),u.MaterialProperty.MP_EMISSIVE_COLOR)
    t=g.n(u.MaterialExpressionTime);sine=g.n(u.MaterialExpressionSine);g.wire(g.mul(t,g.c(.035)),sine);g.prop(g.add(g.c(.035),g.mul(sine,g.c(.008))),u.MaterialProperty.MP_ROUGHNESS);ML.recompile_material(watermat);E.save_loaded_asset(watermat);water.static_mesh_component.set_material(0,watermat)
    # 4. Localized damage: selected outer edges only, retain other sound modules.
    chipped=[]
    for key in ['04','05']:
        candidates=sorted(n for n in base if n.startswith('OH_FULL_'+key+'_'))
        for n in candidates[1::4]:
            actors[n].static_mesh_component.set_static_mesh(meshes['chip'+key]);chipped.append(n)
    report['chipped']=chipped
    # Carry existing Tripo ivy onto broken edges / moist rear ledge, with actual attachment.
    vine=E.load_asset(D+'/Meshes/SM_OH_Soft_18_Vine');vm=E.load_asset(D+'/IllustratedMaterials/M_OH_Illustrated_18')
    for x,z in [(-490,155),(-430,185),(-325,175),(245,220),(295,110),(460,210)]:
        place('SillIvy',vine,vm,(x,1920,z),(.9,.65,.65+rng.random()*.45))
    # 5. Slight upper window compression about its spring line, not a global scene rescale.
    for n,b in base.items():
        if n.startswith('OH_FULL_07_'):
            s=b['scale'][:];s[2]*=.83;actors[n].set_actor_scale3d(u.Vector(*s))
    # Create the established fully rigged/animated flock with smaller, deeper, varied birds.
    flock=(ROOT/'Content/Python/build_overgrown_flock.py').read_text()
    flock=flock.replace('range(12)','range(28)').replace('i/12','i*.38196601125').replace('y=970+ry*math.sin(angle); z=360+25*i','y=1450+ry*.65*math.sin(angle); z=380+17*((i*11)%28)')
    flock=flock.replace('yaw,1,1,1]','yaw,.48+.20*(i%4)/3,.48+.20*(i%4)/3,.48+.20*(i%4)/3]').replace('assert minimum>80','assert minimum>15')
    flock=flock.replace("    actor.set_actor_location(u.Vector(*samples[0]['position_cm']),False,False)","    actor.set_actor_scale3d(u.Vector(*([.48+.20*(i%4)/3]*3)))\n    actor.set_actor_location(u.Vector(*samples[0]['position_cm']),False,False)")
    # Save other changes before the flock builder reloads the level.
    assert L.save_current_level()
    exec(compile(flock,'build_reference_flock','exec'),dict(FLOCK_DEST=D,FLOCK_MAP='L_OvergrownHall_TripoFull',FLOCK_OUT=OUT/'Flock'))
    report['birds']=28
    pp=next(a for a in A.get_all_level_actors() if a.get_actor_label()=='OH_Exposure');pp.modify();settings=pp.get_editor_property('settings')
    for field,value in [('color_gamma',u.Vector4(1.10,1.09,1.08,1)),('color_gain',u.Vector4(1.01,1.04,1.03,1))]:
        settings.set_editor_property('override_'+field,True);settings.set_editor_property(field,value)
    pp.set_editor_property('settings',settings)
assert L.save_current_level()
report['added']=placements;(OUT/'applied.json').write_text(json.dumps(report,indent=2))
runpy.run_path(str(ROOT/'Content/Python/capture_hall_reference.py'))
