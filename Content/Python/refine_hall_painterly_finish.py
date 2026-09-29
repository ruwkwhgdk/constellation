"""v016 reference finish: distant atmosphere, softer light, clustered growth and water."""
import unreal as u,json,random,math,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v016';OUT.mkdir(exist_ok=True)
D='/Game/Environment/OvergrownHall/TripoFull';MAP=D+'/Maps/L_OvergrownHall_TripoFull';DEST=D+'/PainterlyFinish'
E=u.EditorAssetLibrary;ML=u.MaterialEditingLibrary;AT=u.AssetToolsHelpers.get_asset_tools();A=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert L.load_level(MAP)
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
basepath=OUT/'baseline.json'
if not basepath.exists():
    base={}
    for n,a in actors.items():
        if not isinstance(a,u.StaticMeshActor):continue
        c=a.static_mesh_component
        if not c.static_mesh:continue
        p=a.get_actor_location();s=a.get_actor_scale3d();r=a.get_actor_rotation()
        base[n]=dict(position=[p.x,p.y,p.z],scale=[s.x,s.y,s.z],rotation=[r.pitch,r.yaw,r.roll],mesh=c.static_mesh.get_path_name(),materials=[c.get_material(i).get_path_name() if c.get_material(i) else None for i in range(c.get_num_materials())])
    basepath.write_text(json.dumps(base,indent=2))
base=json.loads(basepath.read_text())
for n,a in actors.items():
    if n.startswith('OH_Painterly_'):A.destroy_actor(a)
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
source=(ROOT/'Content/Python/apply_hall_growth_water.py').read_text();exec(source[source.index('class Graph:'):source.index('\nmoss_keys=')])
def make_material(name,copy=None):
    path=DEST+'/'+name
    if E.does_asset_exist(path):m=E.load_asset(path)
    elif copy:m=E.duplicate_asset(copy,path)
    else:m=AT.create_asset(name,DEST,u.Material,u.MaterialFactoryNew())
    m.modify();return m
def finish(m):ML.recompile_material(m);assert E.save_loaded_asset(m,only_if_is_dirty=False)
added=[]
def place(kind,mesh,material,pos,scale,rotation=(0,0,0),shadow=False):
    a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*pos),u.Rotator(pitch=rotation[0],yaw=rotation[1],roll=rotation[2]));a.set_actor_label('OH_Painterly_'+kind+'_%03d'%len(added));a.set_actor_scale3d(u.Vector(*scale));c=a.static_mesh_component;c.set_static_mesh(mesh);c.set_material(0,material);c.set_collision_profile_name('NoCollision');c.set_cast_shadow(shadow);added.append(a.get_actor_label());return a
# Distant color field, no trees. It sits well outside the playable hall.
m=make_material('M_OH_DistantHaze');ML.delete_all_material_expressions(m);m.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT);g=Graph(m);pos=g.n(u.MaterialExpressionWorldPosition)
# At Y=60m, camera rays through the rear windows reach much higher world Z.
height=g.clamp(g.mul(g.sub(g.mask(pos,2),g.c(900)),g.c(1/2600)))
noise=g.noise(pos,.0011);low=g.lerp(g.color((.015,.18,.04)),g.color((.20,.46,.15)),noise)
color=g.lerp(low,g.color((.94,.95,.76)),height);g.prop(g.mul(color,g.c(1100)),u.MaterialProperty.MP_EMISSIVE_COLOR);finish(m)
place('DistantHaze',E.load_asset('/Engine/BasicShapes/Cube'),m,(0,6000,1800),(120,.2,50))
# Dark, continuous ceiling read: keep boards and trusses, soften their pigment.
roof=make_material('M_OH_CeilingSoft');ML.delete_all_material_expressions(roof);g=Graph(roof);pos=g.n(u.MaterialExpressionWorldPosition);n=g.noise(pos,.004)
g.prop(g.lerp(g.color((.045,.080,.086)),g.color((.10,.15,.15)),n),u.MaterialProperty.MP_BASE_COLOR);g.prop(g.c(.97),u.MaterialProperty.MP_ROUGHNESS);g.prop(g.c(.08),u.MaterialProperty.MP_SPECULAR);finish(roof)
for n,a in actors.items():
    if n.startswith('OH_ClosedRoof_'):a.modify();a.static_mesh_component.set_material(0,roof)
# Broad, matte mineral patches on columns; keep the established localized moss recipe.
source=(ROOT/'Content/Python/paint_hall_surfaces.py').read_text();exec(source[source.index('def sample('):source.index('\nfor row in rows:')])
tex=E.load_asset(D+'/IllustratedTextures/T_OH_PaintedMineral')
source=(ROOT/'Content/Python/refine_hall_atmosphere.py').read_text();block=source[source.index('# Large,'):source.index('\nu.SystemLibrary')]
block=block.replace("['01','02','03','04','05','09','11','12','13','26']","['01','02','03','04']").replace("D+'/WeatheredMaterials'","DEST").replace('else 330','else 520').replace('broad=g.noise(pos,.0035);detail=g.noise(pos,.010)','broad=g.noise(pos,.0018);detail=g.noise(pos,.004)')
block=block.replace('wet=g.c(0)',"peel=g.clamp(g.mul(g.sub(g.noise(pos,.003),g.c(.46)),g.c(4)))\n    base=g.lerp(base,g.color((.36,.42,.40)),g.mul(peel,g.c(.38)))\n    wet=g.c(0)")
column_scope=dict(globals());exec(compile(block,'broad_column_paint','exec'),column_scope);column_materials=column_scope['materials']
for n,a in actors.items():
    if n.startswith(('OH_FULL_01_','OH_FULL_02_','OH_FULL_03_','OH_FULL_04_')):a.modify();a.static_mesh_component.set_material(0,column_materials[n.split('_')[2]])
# Irregular low growth; deterministic and based on v015 transforms.
rng=random.Random(916);shrubs=[]
for n,b in base.items():
    if 'PaintedShrub' not in b['mesh']:continue
    a=actors[n];a.modify();s=b['scale'];p=b['position'];factor=rng.uniform(.62,1.18)
    a.set_actor_scale3d(u.Vector(s[0]*rng.uniform(.80,1.28),s[1]*rng.uniform(.78,1.18),s[2]*factor))
    dx=rng.uniform(-32,32);dy=rng.uniform(-45,45)
    if abs(p[0])<230 and p[1]<1500:dx=math.copysign(abs(dx)+25,p[0] or 1)
    a.set_actor_location(u.Vector(p[0]+dx,p[1]+dy,p[2]-rng.uniform(0,7)),False,False);shrubs.append(n)
crown=E.load_asset(D+'/FoliageRuntime/SM_OH_PaintedCrown_Runtime');leaf=E.load_asset(D+'/FoliageRuntime/M_OH_LeafWindNear')
for x,y,z,s in [(-605,1000,440,.18),(-606,1070,365,.11),(-605,1510,710,.20),(-590,1530,595,.13),(602,1130,630,.24),(600,1200,530,.15),(606,1740,840,.19),(605,1800,755,.13),(-480,1933,460,.16),(-420,1932,395,.11),(460,1932,660,.19),(510,1930,570,.12),(150,1934,330,.13)]:
    side=abs(x)>580
    place('WallLeaves',crown,leaf,(x,y,z),(.06 if side else s,s if side else .06,s*1.2),(0,rng.uniform(-15,15),rng.uniform(-12,12)))
# Lower contrast in the old fine vine silhouette, preserving its cutout texture.
vine=make_material('M_OH_VineSoft',D+'/IllustratedMaterials/M_OH_Illustrated_18');g=Graph(vine)
g.prop(g.color((.45,.80,.20)),u.MaterialProperty.MP_EMISSIVE_COLOR);finish(vine)
for n,a in actors.items():
    if isinstance(a,u.StaticMeshActor) and a.static_mesh_component.static_mesh and '18_Vine' in a.static_mesh_component.static_mesh.get_name():a.modify();a.static_mesh_component.set_material(0,vine)
# Shallow water keeps its original wave/normal graph; broad masks vary clarity.
water=make_material('M_OH_WaterSoft',D+'/ReferenceMaterials/M_OH_ShallowTransmission');g=Graph(water);pos=g.n(u.MaterialExpressionWorldPosition);patch=g.noise(pos,.003)
g.prop(g.lerp(g.c(.055),g.c(.16),patch),u.MaterialProperty.MP_ROUGHNESS)
fr=g.n(u.MaterialExpressionFresnel);fr.set_editor_property('exponent',3.0);fr.set_editor_property('base_reflect_fraction',.05)
opacity=g.lerp(g.lerp(g.c(.74),g.c(.88),patch),g.c(.95),fr);fade=g.n(u.MaterialExpressionDepthFade);g.wire(opacity,fade,'Opacity');g.wire(g.c(14),fade,'FadeDistance');g.prop(fade,u.MaterialProperty.MP_OPACITY);finish(water)
actors['OH_SM_OH_Blockout_21'].modify();actors['OH_SM_OH_Blockout_21'].static_mesh_component.set_material(0,water)
reflection=actors['OH_WaterPlanarReflection'];reflection.modify();pc=reflection.get_component_by_class(u.PlanarReflectionComponent);pc.set_editor_property('prefilter_roughness',.075);pc.set_editor_property('normal_distortion_strength',.45)
slab=E.load_asset(D+'/Meshes/SM_OH_ShoreSlab');stone=E.load_asset(D+'/WeatheredMaterials/M_OH_Weathered_13')
for x,y,z in [(-285,835,-1.5),(-190,935,-2.2),(235,1090,-2.8),(300,1120,-1.6),(-350,635,-2.3),(360,720,-2.8)]:place('Shore',slab,stone,(x,y,z),(.13,.11,.18),(0,rng.uniform(0,360),0))
# Warm directional focus and softer existing cast shadows, no exposure lift.
sun=actors['OH_Sun'];sun.modify();c=sun.get_component_by_class(u.DirectionalLightComponent);c.set_editor_property('light_source_angle',18);c.set_editor_property('intensity',15500)
focal=actors['OH_Finish_FocalSun'];focal.modify();c=focal.get_component_by_class(u.SpotLightComponent)
for k,v in [('intensity',850000),('inner_cone_angle',10),('outer_cone_angle',23),('source_radius',95),('volumetric_scattering_intensity',1.1)]:c.set_editor_property(k,v)
c.set_light_color(u.LinearColor(1,.88,.64,1))
assert L.save_current_level()
# Preserve rig/clip transitions while spreading the flight paths higher and wider.
flock=(ROOT/'Content/Python/build_overgrown_flock.py').read_text().replace('range(12)','range(28)').replace('i/12','i*.38196601125')
flock=flock.replace('rx=270+10*i; ry=320+4*i','rx=410+4*i; ry=270+3*i').replace('y=970+ry*math.sin(angle); z=360+25*i','y=1290+ry*.65*math.sin(angle); z=350+20*((i*11)%28)')
flock=flock.replace('yaw,1,1,1]','yaw,.50+.16*(i%4)/3,.50+.16*(i%4)/3,.50+.16*(i%4)/3]').replace('assert minimum>80','assert minimum>15')
flock=flock.replace("    actor.set_actor_location(u.Vector(*samples[0]['position_cm']),False,False)","    actor.set_actor_scale3d(u.Vector(*([.50+.16*(i%4)/3]*3)))\n    actor.set_actor_location(u.Vector(*samples[0]['position_cm']),False,False)")
exec(compile(flock,'painterly_flock','exec'),dict(FLOCK_DEST=D,FLOCK_MAP='L_OvergrownHall_TripoFull',FLOCK_OUT=OUT/'Flock'))
bird=make_material('M_OH_PigeonWarm');ML.delete_all_material_expressions(bird);g=Graph(bird);sample=g.n(u.MaterialExpressionTextureSample);sample.texture=E.load_asset('/Game/Environment/OvergrownHall/Bird/Tripo/Textures/OH_Pigeon_Tripo_v001_basecolor');sample.sampler_type=u.MaterialSamplerType.SAMPLERTYPE_COLOR
color=g.lerp(sample,g.color((.92,.84,.66)),g.c(.40));g.prop(color,u.MaterialProperty.MP_BASE_COLOR);g.prop(g.mul(color,g.c(250)),u.MaterialProperty.MP_EMISSIVE_COLOR);g.prop(g.c(.9),u.MaterialProperty.MP_ROUGHNESS);finish(bird)
for a in A.get_all_level_actors():
    if a.get_actor_label().startswith('OH_Flock_Bird_'):a.modify();a.skeletal_mesh_component.set_material(0,bird)
assert L.save_current_level()
(OUT/'applied.json').write_text(json.dumps(dict(map=MAP,added=added,shrubs=shrubs,roof_material=roof.get_path_name(),water_material=water.get_path_name(),bird_material=bird.get_path_name(),rear_trees_restored=False,playtest='user'),indent=2))
runpy.run_path(str(ROOT/'Content/Python/capture_hall_painterly_finish.py'))
