"""v022 art-directed light/color masses; retains v021 geometry and animation."""
import unreal as u,json,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v022';OUT.mkdir(parents=True,exist_ok=True);D='/Game/Constellation/Environments/OvergrownHall/TripoFull';MAP='/Game/Constellation/Worlds/OvergrownHall/Maps/L_OvergrownHall_TripoFull'
E=u.EditorAssetLibrary;ML=u.MaterialEditingLibrary;A=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert L.load_level(MAP);actors={a.get_actor_label():a for a in A.get_all_level_actors()}
if not (OUT/'baseline.json').exists():
    rows={}
    for n,a in actors.items():
        p=a.get_actor_location();s=a.get_actor_scale3d();rot=a.get_actor_rotation();rows[n]=dict(position=[p.x,p.y,p.z],scale=[s.x,s.y,s.z],rotation=[rot.pitch,rot.yaw,rot.roll])
        if isinstance(a,u.StaticMeshActor):rows[n].update(mesh=a.static_mesh_component.static_mesh.get_path_name() if a.static_mesh_component.static_mesh else None,materials=[a.static_mesh_component.get_material(i).get_path_name() if a.static_mesh_component.get_material(i) else None for i in range(a.static_mesh_component.get_num_materials())])
    (OUT/'baseline.json').write_text(json.dumps(rows,indent=2))
source=(ROOT/'Content/Python/apply_hall_growth_water.py').read_text();exec(source[source.index('class Graph:'):source.index('\nmoss_keys=')])
def material(name,src):
    path=D+'/AtmosphereFinish/'+name;m=E.load_asset(path) if E.does_asset_exist(path) else E.duplicate_asset(src,path);assert m;m.modify();return m
def save(m):ML.recompile_material(m);assert E.save_loaded_asset(m,only_if_is_dirty=False)
# Keep the detailed leaf alpha and wind, simplify the internal color into larger painted masses.
leaf=material('M_OH_LeafColorMass',D+'/FoliageRuntime/M_OH_LeafWindNear');g=Graph(leaf);pos=g.n(u.MaterialExpressionWorldPosition);sample=g.n(u.MaterialExpressionTextureSample);sample.texture=E.load_asset(D+'/FoliagePaint/T_OH_PaintedLeaves');sample.sampler_type=u.MaterialSamplerType.SAMPLERTYPE_COLOR;sample.set_editor_property('mip_value_mode',u.TextureMipValueMode.TMVM_MIP_BIAS);sample.set_editor_property('const_mip_value',1)
n=g.noise(pos,.009);palette=g.lerp(g.color((.13,.29,.055)),g.color((.43,.61,.16)),n);color=g.lerp(sample,palette,g.c(.72));g.prop(color,u.MaterialProperty.MP_BASE_COLOR);g.prop(g.mul(color,g.c(65)),u.MaterialProperty.MP_EMISSIVE_COLOR);g.prop(g.mul(color,g.c(.55)),u.MaterialProperty.MP_SUBSURFACE_COLOR);save(leaf)
plants=[]
for n,a in actors.items():
    if not isinstance(a,u.StaticMeshActor):continue
    c=a.static_mesh_component
    if c.static_mesh and c.static_mesh.get_name().startswith('SM_OH_Painted'):
        a.modify();c.set_material(0,leaf);plants.append(n)
# Bright, broken horizontal reflection connects the warm source to the foreground.
water=material('M_OH_LuminousCalmWater',D+'/AtmosphereFinish/M_OH_CalmReferenceWater');g=Graph(water);pos=g.n(u.MaterialExpressionWorldPosition)
q=g.mul(g.sub(pos,g.color((-65,800,2))),g.color((1/530,1/200,0)));dot=g.n(u.MaterialExpressionDotProduct);g.wire(q,dot,'A');g.wire(q,dot,'B');region=g.clamp(g.mul(g.sub(g.c(1),dot),g.c(2.3)))
stretched=g.mul(pos,g.color((.30,1.6,1)));n=g.noise(stretched,.011);breaks=g.clamp(g.mul(g.sub(n,g.c(.46)),g.c(9)))
highlight=g.mul(region,breaks);cool=g.color((.045,.16,.16));warm=g.mul(g.color((1,.88,.57)),g.mul(highlight,g.c(950)));g.prop(g.add(g.mul(cool,g.c(110)),warm),u.MaterialProperty.MP_EMISSIVE_COLOR)
g.prop(g.color((.22,.50,.48)),u.MaterialProperty.MP_BASE_COLOR);g.prop(g.c(.98),u.MaterialProperty.MP_OPACITY);save(water)
actors['OH_SM_OH_Blockout_21'].modify();actors['OH_SM_OH_Blockout_21'].static_mesh_component.set_material(0,water)
# Stronger directional warmth in participating fog, without changing camera exposure.
focal=actors['OH_Finish_FocalSun'];focal.modify();c=focal.get_component_by_class(u.SpotLightComponent)
for k,v in [('intensity',2800000),('volumetric_scattering_intensity',6),('outer_cone_angle',18)]:c.set_editor_property(k,v)
c.set_light_color(u.LinearColor(1,.79,.48,1))
fog=actors['OH_ReferenceFog'];fog.modify();c=fog.get_component_by_class(u.ExponentialHeightFogComponent);c.set_editor_property('enable_volumetric_fog',True);c.set_editor_property('fog_density',.03);c.set_editor_property('volumetric_fog_scattering_distribution',.55)
# The original front shafts are cool and mottled rather than pale clean stone.
pillar=material('M_OH_CoolPillar',D+'/PainterlyFinish/M_OH_Weathered_02');g=Graph(pillar);pos=g.n(u.MaterialExpressionWorldPosition);n=g.noise(g.mul(pos,g.color((1,1,.5))),.005);stone=g.lerp(g.color((.07,.15,.19)),g.color((.26,.34,.34)),n);peel=g.clamp(g.mul(g.sub(g.noise(pos,.013),g.c(.59)),g.c(4)));g.prop(g.lerp(stone,g.color((.37,.41,.36)),g.mul(peel,g.c(.5))),u.MaterialProperty.MP_BASE_COLOR);save(pillar)
pillars=[]
for n,a in actors.items():
    if n.startswith('OH_FULL_02_'):a.modify();a.static_mesh_component.set_material(0,pillar);pillars.append(n)
assert L.save_current_level();(OUT/'applied.json').write_text(json.dumps(dict(map=MAP,plants=plants,pillars=pillars,water_material=water.get_path_name(),playtest=False),indent=2))
runpy.run_path(str(ROOT/'Content/Python/capture_hall_color_masses.py'))
