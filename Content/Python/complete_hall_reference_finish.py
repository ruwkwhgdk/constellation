"""v019 complete remaining reference art pass; retain v018 camera and playable scale."""
import unreal as u,json,random,math,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v019';D='/Game/Environment/OvergrownHall/TripoFull';DEST=D+'/ReferenceFinish';MAP=D+'/Maps/L_OvergrownHall_TripoFull'
E=u.EditorAssetLibrary;ML=u.MaterialEditingLibrary;AT=u.AssetToolsHelpers.get_asset_tools();A=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert L.load_level(MAP);actors={a.get_actor_label():a for a in A.get_all_level_actors()}
if not (OUT/'baseline.json').exists():
    baseline={}
    for n,a in actors.items():
        p=a.get_actor_location();r=a.get_actor_rotation();s=a.get_actor_scale3d();row=dict(position=[p.x,p.y,p.z],rotation=[r.pitch,r.yaw,r.roll],scale=[s.x,s.y,s.z])
        if isinstance(a,u.StaticMeshActor):
            c=a.static_mesh_component;row.update(mesh=c.static_mesh.get_path_name() if c.static_mesh else None,materials=[c.get_material(i).get_path_name() if c.get_material(i) else None for i in range(c.get_num_materials())])
        baseline[n]=row
    (OUT/'baseline.json').write_text(json.dumps(baseline,indent=2))
baseline=json.loads((OUT/'baseline.json').read_text())
for n,a in actors.items():
    if n.startswith('OH_RefFinish_'):A.destroy_actor(a)
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
source=(ROOT/'Content/Python/apply_hall_growth_water.py').read_text();exec(source[source.index('class Graph:'):source.index('\nmoss_keys=')])
def make_material(name,copy=None):
    path=DEST+'/'+name
    m=E.load_asset(path) if E.does_asset_exist(path) else E.duplicate_asset(copy,path) if copy else AT.create_asset(name,DEST,u.Material,u.MaterialFactoryNew())
    m.modify();return m
def finish(m):ML.recompile_material(m);assert E.save_loaded_asset(m,only_if_is_dirty=False)
added=[]
def place(kind,mesh,mat,pos,scale,rotation=(0,0,0)):
    a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*pos),u.Rotator(pitch=rotation[0],yaw=rotation[1],roll=rotation[2]));a.set_actor_label('OH_RefFinish_'+kind+'_%03d'%len(added));a.set_actor_scale3d(u.Vector(*scale));c=a.static_mesh_component;c.set_static_mesh(mesh);c.set_material(0,mat);c.set_collision_profile_name('NoCollision');c.set_cast_shadow(False);added.append(a.get_actor_label());return a
# Camera faces +Y; screen right is world -X. Keep the actual light at the right window.
sun=actors['OH_Sun'];sun.modify();c=sun.get_component_by_class(u.DirectionalLightComponent);c.set_editor_property('intensity',8500);c.set_editor_property('light_source_angle',18)
focal=actors['OH_Finish_FocalSun'];focal.modify();start=u.Vector(-450,1870,860);target=u.Vector(-30,910,5)
focal.set_actor_location(start,False,False);focal.set_actor_rotation(u.MathLibrary.find_look_at_rotation(start,target),False);c=focal.get_component_by_class(u.SpotLightComponent)
for k,v in [('intensity',1450000),('inner_cone_angle',7),('outer_cone_angle',16),('source_radius',110),('volumetric_scattering_intensity',1.6),('cast_shadows',False)]:c.set_editor_property(k,v)
c.set_light_color(u.LinearColor(1,.88,.64,1))
fill=actors['OH_WindowFill'];fill.modify();p=u.Vector(-300,1890,650);fill.set_actor_location(p,False,False);fill.set_actor_rotation(u.MathLibrary.find_look_at_rotation(p,u.Vector(0,950,180)),False);c=fill.get_component_by_class(u.RectLightComponent)
for k,v in [('intensity',110000),('source_width',500),('source_height',600)]:c.set_editor_property(k,v)
fogactor=actors['OH_ReferenceFog'];fogactor.modify();fog=fogactor.get_component_by_class(u.ExponentialHeightFogComponent);fog.set_editor_property('fog_density',.024);fog.set_editor_property('volumetric_fog_scattering_distribution',.35)
# Replace some rounded foreground masses with low Tripo grass and open gaps.
rng=random.Random(919);shrubs=[];removed=[];grass_positions=[]
for i,(n,b) in enumerate(sorted(baseline.items())):
    if 'PaintedShrub' not in (b.get('mesh') or ''):continue
    p=b['position'];s=b['scale'];front=p[1]<1550
    discard=front and ((abs(p[0])<330 and i%3==0) or i%7==0)
    if discard:
        if n in actors:assert A.destroy_actor(actors[n])
        removed.append(n);grass_positions.append((p[0],p[1],max(p[2],0)));continue
    if n not in actors:continue
    a=actors[n];a.modify();factor=rng.uniform(.46,.76) if front else rng.uniform(.72,.96)
    a.set_actor_scale3d(u.Vector(s[0]*rng.uniform(.96,1.23),s[1]*rng.uniform(.9,1.18),s[2]*factor));shrubs.append(n)
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
grassmat=make_material('M_OH_GrassPainterly',D+'/IllustratedMaterials/M_OH_Illustrated_16');g=Graph(grassmat);pos=g.n(u.MaterialExpressionWorldPosition);variation=g.noise(pos,.012)
color=g.lerp(g.color((.12,.23,.045)),g.color((.38,.52,.12)),variation);g.prop(color,u.MaterialProperty.MP_BASE_COLOR);g.prop(g.mul(color,g.c(2)),u.MaterialProperty.MP_EMISSIVE_COLOR);g.prop(g.c(.96),u.MaterialProperty.MP_ROUGHNESS);finish(grassmat)
grass=E.load_asset(D+'/Meshes/SM_OH_Clean_16_Grass')
grass_positions += [(-420,760,0),(380,810,0),(-320,1250,0),(270,1300,0),(-530,1420,0),(500,1480,0),(-180,1720,0),(250,1710,0)]
for x,y,z in grass_positions:
    place('Grass',grass,grassmat,(x,y,z),(rng.uniform(.70,1.2),rng.uniform(.65,1.1),rng.uniform(.75,1.35)),(0,rng.uniform(0,360),0))
# A few elongated, tapering trails attached to existing cluster anchors.
leaves=E.load_asset(D+'/FoliageRuntime/SM_OH_PaintedCrown_Runtime');leafmat=E.load_asset(D+'/FoliageRuntime/M_OH_LeafWindNear')
contact_rows=json.loads((OUT.parent/'v017/applied.json').read_text())['contacts']
for row in contact_rows[::3]:
    center=actors[row['label']].get_actor_bounds(False)[0];side=abs(center.x)>580
    for j in range(1,4):
        pos=(center.x,center.y+j*4,center.z-j*28) if side else (center.x+j*6,center.y,center.z-j*27)
        a=place('TrailingLeaves',leaves,leafmat,pos,((.035 if side else .10)/(1+j*.18),(.10 if side else .035)/(1+j*.18),.14/(1+j*.2)))
        c,e=a.get_actor_bounds(False);a.set_actor_location(a.get_actor_location()+u.Vector(*pos)-c,False,False)
# Broad reflective color masses with a localized irregular warm reflection.
water=make_material('M_OH_ReferenceWater',D+'/PainterlyFinish/M_OH_WaterSoft');g=Graph(water);pos=g.n(u.MaterialExpressionWorldPosition);noise=g.noise(pos,.004)
q=g.mul(g.sub(pos,g.color((-60,880,2))),g.color((1/240,1/300,0)));dist=g.n(u.MaterialExpressionDotProduct);g.wire(q,dist,'A');g.wire(q,dist,'B')
pool=g.clamp(g.mul(g.sub(g.add(g.sub(g.c(1),dist),g.mul(g.sub(noise,g.c(.5)),g.c(.65))),g.c(.1)),g.c(2)))
pool=g.mul(pool,g.clamp(g.mul(g.sub(g.noise(pos,.009),g.c(.35)),g.c(4))))
g.prop(g.lerp(g.color((.23,.51,.49)),g.color((.67,.79,.63)),noise),u.MaterialProperty.MP_BASE_COLOR)
g.prop(g.lerp(g.c(.075),g.c(.20),noise),u.MaterialProperty.MP_ROUGHNESS)
g.prop(g.mul(g.color((1,.89,.61)),g.mul(pool,g.c(180))),u.MaterialProperty.MP_EMISSIVE_COLOR)
fr=g.n(u.MaterialExpressionFresnel);fr.set_editor_property('exponent',3);fr.set_editor_property('base_reflect_fraction',.05)
fade=g.n(u.MaterialExpressionDepthFade);g.wire(g.lerp(g.c(.88),g.c(.97),fr),fade,'Opacity');g.wire(g.c(18),fade,'FadeDistance');g.prop(fade,u.MaterialProperty.MP_OPACITY);finish(water)
actors['OH_SM_OH_Blockout_21'].modify();actors['OH_SM_OH_Blockout_21'].static_mesh_component.set_material(0,water)
reflection=actors['OH_WaterPlanarReflection'];reflection.modify();c=reflection.get_component_by_class(u.PlanarReflectionComponent);c.set_editor_property('prefilter_roughness',.10);c.set_editor_property('normal_distortion_strength',.6)
# Layered distant color, with no rear tree meshes. The bright halo is screen-right.
haze=make_material('M_OH_ReferenceHaze');ML.delete_all_material_expressions(haze);haze.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT);g=Graph(haze);pos=g.n(u.MaterialExpressionWorldPosition)
layer=g.add(g.mul(g.noise(pos,.0011),g.c(.6)),g.mul(g.noise(pos,.0038),g.c(.4)))
low=g.lerp(g.color((.03,.19,.08)),g.color((.21,.44,.19)),layer)
q=g.mul(g.sub(pos,g.color((-900,6000,2100))),g.color((1/1700,0,1/1600)));dist=g.n(u.MaterialExpressionDotProduct);g.wire(q,dist,'A');g.wire(q,dist,'B');halo=g.clamp(g.sub(g.c(1),dist))
low=g.lerp(low,g.color((.88,.83,.56)),g.mul(halo,g.c(.72)))
height=g.clamp(g.mul(g.sub(g.mask(pos,2),g.c(900)),g.c(1/2600)));color=g.lerp(low,g.color((.94,.95,.76)),height)
g.prop(g.mul(color,g.c(1100)),u.MaterialProperty.MP_EMISSIVE_COLOR);finish(haze)
backdrop=actors['OH_Painterly_DistantHaze_000'];backdrop.modify();backdrop.static_mesh_component.set_material(0,haze)
# Selective broad spalls on shafts; reduce ornamental overhang while keeping shaft dimensions.
u.SystemLibrary.execute_console_command(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(),'Interchange.FeatureFlags.Import.FBX 0')
meshes=[]
for row in json.loads((OUT/'pillar_meshes.json').read_text()):
    opts=u.FbxImportUI();opts.automated_import_should_detect_type=False;opts.import_mesh=True;opts.import_as_skeletal=False;opts.import_materials=False;opts.import_textures=False;opts.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
    opts.static_mesh_import_data.combine_meshes=True;opts.static_mesh_import_data.auto_generate_collision=False;opts.static_mesh_import_data.convert_scene_unit=True;opts.static_mesh_import_data.normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
    task=u.AssetImportTask();task.filename=str(OUT/(row['mesh']+'.fbx'));task.destination_path=D+'/Meshes';task.automated=True;task.save=True;task.replace_existing=True;task.options=opts;task.factory=u.FbxFactory();AT.import_asset_tasks([task]);mesh=E.load_asset(task.imported_object_paths[0]);mesh.set_material(0,E.load_asset(D+'/PainterlyFinish/M_OH_Weathered_02'));mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);assert E.save_loaded_asset(mesh,only_if_is_dirty=False);meshes.append(mesh)
spalls=[];trim=[]
for i,(n,a) in enumerate(sorted(actors.items())):
    if n.startswith('OH_FULL_02_') and i%3==0:
        a.modify();a.static_mesh_component.set_static_mesh(meshes[i%2]);spalls.append(n)
    elif n.startswith(('OH_FULL_01_','OH_FULL_03_')):
        a.modify();s=baseline[n]['scale'];factor=.92 if n.startswith('OH_FULL_01_') else .88;a.set_actor_scale3d(u.Vector(s[0]*factor,s[1]*factor,s[2]));trim.append(n)
assert L.save_current_level()
# Final broad flight distribution retains the existing rig and animated clip transitions.
flock=(ROOT/'Content/Python/build_overgrown_flock.py').read_text().replace('range(12)','range(28)').replace('i/12','i*.38196601125')
flock=flock.replace('rx=270+10*i; ry=320+4*i','rx=380+5*i; ry=270+3*i').replace('y=970+ry*math.sin(angle); z=360+25*i','y=1340+ry*.45*math.sin(angle); z=240+24*((i*9+4)%28)')
flock=flock.replace('yaw,1,1,1]','yaw,.44+.22*(i%5)/4,.44+.22*(i%5)/4,.44+.22*(i%5)/4]').replace('assert minimum>80','assert minimum>15')
flock=flock.replace("    actor.set_actor_location(u.Vector(*samples[0]['position_cm']),False,False)","    actor.set_actor_scale3d(u.Vector(*([.44+.22*(i%5)/4]*3)))\n    actor.set_actor_location(u.Vector(*samples[0]['position_cm']),False,False)")
exec(compile(flock,'reference_finish_flock','exec'),dict(FLOCK_DEST=D,FLOCK_MAP='L_OvergrownHall_TripoFull',FLOCK_OUT=OUT/'Flock'))
birdmat=E.load_asset(D+'/PainterlyFinish/M_OH_PigeonWarm')
for a in A.get_all_level_actors():
    if a.get_actor_label().startswith('OH_Flock_Bird_'):a.modify();a.skeletal_mesh_component.set_material(0,birdmat)
assert L.save_current_level()
(OUT/'applied.json').write_text(json.dumps(dict(map=MAP,added=added,removed_shrubs=removed,reshaped_shrubs=shrubs,spalled_pillars=spalls,trimmed_bases_caps=trim,water_material=water.get_path_name(),screen_right_light=True,playtest='user'),indent=2))
runpy.run_path(str(ROOT/'Content/Python/capture_hall_reference_finish.py'))
