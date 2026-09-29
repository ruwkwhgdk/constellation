"""v020: scoped light, vegetation spacing and calmer water pass over v019."""
import unreal as u, json, math, runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir()); OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v020'; OUT.mkdir(parents=True,exist_ok=True)
D='/Game/Environment/OvergrownHall/TripoFull'; MAP=D+'/Maps/L_OvergrownHall_TripoFull'; DEST=D+'/AtmosphereFinish'
E=u.EditorAssetLibrary; ML=u.MaterialEditingLibrary; AT=u.AssetToolsHelpers.get_asset_tools(); A=u.get_editor_subsystem(u.EditorActorSubsystem); L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert L.load_level(MAP)
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
if not (OUT/'baseline.json').exists():
    data={}
    for n,a in actors.items():
        p=a.get_actor_location();s=a.get_actor_scale3d();r=a.get_actor_rotation()
        data[n]=dict(position=[p.x,p.y,p.z],scale=[s.x,s.y,s.z],rotation=[r.pitch,r.yaw,r.roll])
        if isinstance(a,u.StaticMeshActor):
            c=a.static_mesh_component;data[n].update(mesh=c.static_mesh.get_path_name() if c.static_mesh else None,materials=[c.get_material(i).get_path_name() if c.get_material(i) else None for i in range(c.get_num_materials())])
    (OUT/'baseline.json').write_text(json.dumps(data,indent=2))
base=json.loads((OUT/'baseline.json').read_text())
source=(ROOT/'Content/Python/apply_hall_growth_water.py').read_text();exec(source[source.index('class Graph:'):source.index('\nmoss_keys=')])
def material(name,src):
    path=DEST+'/'+name;m=E.load_asset(path) if E.does_asset_exist(path) else E.duplicate_asset(src,path);assert m;m.modify();return m
def save(m):
    ML.recompile_material(m);assert E.save_loaded_asset(m,only_if_is_dirty=False)
# Reduce competing directional light; narrow warm source across the right window.
sun=actors['OH_Sun'];sun.modify();sun.get_component_by_class(u.DirectionalLightComponent).set_editor_property('intensity',5000)
actors['OH_Sky'].modify();actors['OH_Sky'].get_component_by_class(u.SkyLightComponent).set_editor_property('intensity',1.65)
focal=actors['OH_Finish_FocalSun'];focal.modify();p=u.Vector(-490,1820,1000);focal.set_actor_location(p,False,False);focal.set_actor_rotation(u.MathLibrary.find_look_at_rotation(p,u.Vector(50,850,0)),False)
c=focal.get_component_by_class(u.SpotLightComponent)
for k,v in [('intensity',2200000),('attenuation_radius',2400),('inner_cone_angle',8),('outer_cone_angle',14),('volumetric_scattering_intensity',2.8)]:c.set_editor_property(k,v)
c.set_light_color(u.LinearColor(1,.84,.55,1))
actors['OH_WindowFill'].modify();actors['OH_WindowFill'].get_component_by_class(u.RectLightComponent).set_editor_property('intensity',75000)
name='OH_Atmosphere_BenchFill';fill=actors.get(name) or A.spawn_actor_from_class(u.RectLight,u.Vector(140,550,260));fill.set_actor_label(name);fill.modify();fill.set_actor_location(u.Vector(140,550,260),False,False);fill.set_actor_rotation(u.MathLibrary.find_look_at_rotation(fill.get_actor_location(),u.Vector(120,1020,65)),False)
c=fill.get_component_by_class(u.RectLightComponent)
for k,v in [('intensity',28000),('source_width',320),('source_height',160),('attenuation_radius',750),('cast_shadows',False),('volumetric_scattering_intensity',0)]:c.set_editor_property(k,v)
c.set_light_color(u.LinearColor(.82,.91,.86,1))
# Remove selected clusters in contiguous gaps rather than evenly thinning every nth plant.
removed=[];reshaped=[]
for n,b in sorted(base.items()):
    if not n.startswith('OH_FULL_17_'):continue
    x,y,z=b['position'];s=b['scale']
    gap=(y>1600 and ((-240<x<-85) or (190<x<330))) or (y<1500 and 330<x<470)
    if gap:
        if n in actors:assert A.destroy_actor(actors[n])
        removed.append(n);continue
    if n not in actors:continue
    a=actors[n];a.modify();idx=int(n.rsplit('_',1)[1]);height=[.72,1.15,.85,1.32,.94][idx%5]
    a.set_actor_scale3d(u.Vector(s[0]*[.82,1.07,.93][idx%3],s[1]*[1.08,.84,.97][idx%3],s[2]*height));reshaped.append(n)
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
# Broaden selected existing wall clusters asymmetrically without adding new rows of leaves.
wall=[]
for i,(n,b) in enumerate(sorted(base.items())):
    if not n.startswith('OH_Painterly_WallLeaves_'):continue
    a=actors[n];a.modify();center=a.get_actor_bounds(False)[0];s=b['scale'];side=abs(center.x)>580
    a.set_actor_scale3d(u.Vector(s[0]*(1 if side else 1.65),s[1]*(1.65 if side else 1),s[2]*([.82,1.2,.95][i%3])))
    actual=a.get_actor_bounds(False)[0];a.set_actor_location(a.get_actor_location()+center-actual,False,False);wall.append(n)
# Keep shallow water and displacement; override normals and the old broad emissive blobs.
m=material('M_OH_CalmReferenceWater',D+'/ReferenceFinish/M_OH_ReferenceWater');g=Graph(m);pos=g.n(u.MaterialExpressionWorldPosition);time=g.n(u.MaterialExpressionTime);x=g.mask(pos,0);y=g.mask(pos,1)
phase=g.add(g.mul(y,g.c(1/180)),g.mul(time,g.c(.035)));cs=g.n(u.MaterialExpressionCosine);g.wire(phase,cs)
normal=g.op(u.MaterialExpressionAppendVector,g.op(u.MaterialExpressionAppendVector,g.mul(cs,g.c(.0015)),g.mul(cs,g.c(.004))),g.c(1));norm=g.n(u.MaterialExpressionNormalize);g.wire(normal,norm);g.prop(norm,u.MaterialProperty.MP_NORMAL)
q=g.mul(g.sub(pos,g.color((-80,870,2))),g.color((1/430,1/470,0)));dist=g.n(u.MaterialExpressionDotProduct);g.wire(q,dist,'A');g.wire(q,dist,'B');region=g.clamp(g.sub(g.c(1),dist))
warped=g.add(g.mul(y,g.c(1/72)),g.mul(g.noise(pos,.008),g.c(.65)));sine=g.n(u.MaterialExpressionSine);g.wire(warped,sine)
stripe=g.clamp(g.mul(g.sub(sine,g.c(.94)),g.c(16)))
breaks=g.clamp(g.mul(g.sub(g.noise(g.mul(pos,g.color((.35,1,1))),.016),g.c(.43)),g.c(5)))
mask=g.mul(region,g.mul(stripe,breaks));g.prop(g.mul(g.color((1,.89,.65)),g.mul(mask,g.c(230))),u.MaterialProperty.MP_EMISSIVE_COLOR)
g.prop(g.lerp(g.color((.17,.40,.38)),g.color((.34,.55,.48)),g.noise(pos,.002)),u.MaterialProperty.MP_BASE_COLOR);g.prop(g.c(.065),u.MaterialProperty.MP_ROUGHNESS);save(m)
actors['OH_SM_OH_Blockout_21'].modify();actors['OH_SM_OH_Blockout_21'].static_mesh_component.set_material(0,m)
a=actors['OH_WaterPlanarReflection'];a.modify();c=a.get_component_by_class(u.PlanarReflectionComponent);c.set_editor_property('normal_distortion_strength',.12);c.set_editor_property('prefilter_roughness',.04)
# Differentiate the window backdrop: cool dimmer left, warm bright upper-right.
m=material('M_OH_GradedHaze',D+'/ReferenceFinish/M_OH_ReferenceHaze');ML.delete_all_material_expressions(m);g=Graph(m);pos=g.n(u.MaterialExpressionWorldPosition);x=g.mask(pos,0);z=g.mask(pos,2)
right=g.clamp(g.mul(g.sub(g.c(1400),x),g.c(1/3400)));height=g.clamp(g.mul(g.sub(z,g.c(900)),g.c(1/2800)));noise=g.noise(pos,.002)
low=g.lerp(g.color((.045,.19,.12)),g.color((.19,.36,.16)),noise);sky=g.lerp(g.color((.42,.62,.62)),g.color((1,.94,.70)),right)
color=g.lerp(low,sky,height);g.prop(g.mul(color,g.lerp(g.c(700),g.c(1300),right)),u.MaterialProperty.MP_EMISSIVE_COLOR);save(m)
actors['OH_Painterly_DistantHaze_000'].modify();actors['OH_Painterly_DistantHaze_000'].static_mesh_component.set_material(0,m)
assert L.save_current_level()
(OUT/'applied.json').write_text(json.dumps(dict(map=MAP,removed=removed,reshaped=reshaped,wall_clusters=wall,water_material=DEST+'/M_OH_CalmReferenceWater.M_OH_CalmReferenceWater',new_light=name,playtest=False),indent=2))
runpy.run_path(str(ROOT/'Content/Python/capture_hall_atmosphere_finish.py'))
