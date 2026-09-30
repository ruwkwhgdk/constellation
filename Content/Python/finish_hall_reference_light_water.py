"""v026: localized lower-window shaft and clearer cyan water; keep v025 structure."""
import unreal as u,json,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v026';OUT.mkdir(parents=True,exist_ok=True);D='/Game/Constellation/Environments/OvergrownHall/TripoFull';MAP='/Game/Constellation/Worlds/OvergrownHall/Maps/L_OvergrownHall_TripoFull'
E=u.EditorAssetLibrary;ML=u.MaterialEditingLibrary;A=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem);assert L.load_level(MAP);actors={a.get_actor_label():a for a in A.get_all_level_actors()}
if not (OUT/'baseline.json').exists():
    rows={}
    for n,a in actors.items():
        p=a.get_actor_location();s=a.get_actor_scale3d();r=a.get_actor_rotation();rows[n]=dict(position=[p.x,p.y,p.z],scale=[s.x,s.y,s.z],rotation=[r.pitch,r.yaw,r.roll])
        if isinstance(a,u.StaticMeshActor):rows[n].update(mesh=a.static_mesh_component.static_mesh.get_path_name() if a.static_mesh_component.static_mesh else None,materials=[a.static_mesh_component.get_material(i).get_path_name() if a.static_mesh_component.get_material(i) else None for i in range(a.static_mesh_component.get_num_materials())])
    (OUT/'baseline.json').write_text(json.dumps(rows,indent=2))
source=(ROOT/'Content/Python/apply_hall_growth_water.py').read_text();exec(source[source.index('class Graph:'):source.index('\nmoss_keys=')])
def make(name,src):
    p=D+'/AtmosphereFinish/'+name;m=E.load_asset(p) if E.does_asset_exist(p) else E.duplicate_asset(src,p);assert m;m.modify();return m
def save(m):ML.recompile_material(m);assert E.save_loaded_asset(m,only_if_is_dirty=False)
water=make('M_OH_ReferenceCyanWater',D+'/AtmosphereFinish/M_OH_FinalReflection');g=Graph(water);pos=g.n(u.MaterialExpressionWorldPosition)
q=g.mul(g.sub(pos,g.color((-65,940,2))),g.color((1/430,1/140,0)));dot=g.n(u.MaterialExpressionDotProduct);g.wire(q,dot,'A');g.wire(q,dot,'B');region=g.clamp(g.mul(g.sub(g.c(1),dot),g.c(2)));n=g.noise(g.mul(pos,g.color((.5,.95,1))),.011);mask=g.mul(region,g.clamp(g.mul(g.sub(n,g.c(.53)),g.c(10))))
g.prop(g.add(g.mul(g.color((.045,.18,.24)),g.c(110)),g.mul(g.color((1,.88,.57)),g.mul(mask,g.c(850)))),u.MaterialProperty.MP_EMISSIVE_COLOR);g.prop(g.color((.18,.45,.52)),u.MaterialProperty.MP_BASE_COLOR);g.prop(g.c(.018),u.MaterialProperty.MP_ROUGHNESS);save(water)
actors['OH_SM_OH_Blockout_21'].modify();actors['OH_SM_OH_Blockout_21'].static_mesh_component.set_material(0,water);a=actors['OH_WaterPlanarReflection'];a.modify();c=a.get_component_by_class(u.PlanarReflectionComponent);c.set_editor_property('prefilter_roughness',.01);c.set_editor_property('screen_percentage',75)
# A real spotlight in participating fog, not a camera-facing ray card.
name='OH_Reference_LowerWindowShaft';p=u.Vector(-460,1900,680);a=actors.get(name) or A.spawn_actor_from_class(u.SpotLight,p);a.set_actor_label(name);a.modify();a.set_actor_location(p,False,False);a.set_actor_rotation(u.MathLibrary.find_look_at_rotation(p,u.Vector(-20,1000,20)),False);c=a.get_component_by_class(u.SpotLightComponent)
for k,v in [('intensity_units',u.LightUnits.CANDELAS),('intensity',900000),('attenuation_radius',1800),('inner_cone_angle',4),('outer_cone_angle',7),('source_radius',40),('volumetric_scattering_intensity',12),('cast_shadows',False)]:c.set_editor_property(k,v)
c.set_light_color(u.LinearColor(1,.90,.62,1))
# Localized pale daylight behind the lower right panes, retaining green elsewhere.
haze=make('M_OH_ReferenceWindowDaylight',D+'/AtmosphereFinish/M_OH_FinalBackdrop');ML.delete_all_material_expressions(haze);g=Graph(haze);pos=g.n(u.MaterialExpressionWorldPosition);x=g.mask(pos,0);z=g.mask(pos,2);right=g.clamp(g.mul(g.sub(g.c(1400),x),g.c(1/3400)));height=g.clamp(g.mul(g.sub(z,g.c(1850)),g.c(1/1100)))
mass=g.add(g.mul(g.noise(pos,.0012),g.c(.75)),g.mul(g.noise(pos,.004),g.c(.25)));low=g.lerp(g.color((.085,.30,.13)),g.color((.48,.66,.26)),mass)
q=g.mul(g.sub(pos,g.color((-900,6000,1450))),g.color((1/1500,0,1/1500)));dot=g.n(u.MaterialExpressionDotProduct);g.wire(q,dot,'A');g.wire(q,dot,'B');glow=g.clamp(g.sub(g.c(1),dot));low=g.lerp(low,g.color((.98,.95,.72)),g.mul(glow,g.c(.62)))
sky=g.lerp(g.color((.48,.66,.66)),g.color((1,.95,.76)),right);color=g.lerp(low,sky,height);g.prop(g.mul(color,g.lerp(g.c(950),g.c(1400),right)),u.MaterialProperty.MP_EMISSIVE_COLOR);save(haze)
actors['OH_Painterly_DistantHaze_000'].modify();actors['OH_Painterly_DistantHaze_000'].static_mesh_component.set_material(0,haze)
shadow_changes=[]
for n,a in actors.items():
    if n.startswith('OH_Tripo_Tree_'):a.modify();a.static_mesh_component.set_cast_shadow(False);shadow_changes.append(n)
assert L.save_current_level();(OUT/'applied.json').write_text(json.dumps(dict(map=MAP,new_light=name,water_material=water.get_path_name(),tree_shadows_disabled=shadow_changes,playtest=False),indent=2))
runpy.run_path(str(ROOT/'Content/Python/capture_hall_reference_light_water.py'))
