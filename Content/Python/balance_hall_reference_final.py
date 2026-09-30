"""v023: final balance of v022 light/reflection plus layered rear-wall foliage."""
from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u,json,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v023';OUT.mkdir(parents=True,exist_ok=True);D='/Game/Constellation/Environments/OvergrownHall/TripoFull';MAP='/Game/Constellation/Worlds/OvergrownHall/Maps/L_OvergrownHall_TripoFull'
E=u.EditorAssetLibrary;ML=u.MaterialEditingLibrary;A=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert L.load_level(MAP);actors={a.get_actor_label():a for a in A.get_all_level_actors()}
if not (OUT/'baseline.json').exists():
    rows={}
    for n,a in actors.items():
        p=a.get_actor_location();s=a.get_actor_scale3d();rot=a.get_actor_rotation();rows[n]=dict(position=[p.x,p.y,p.z],scale=[s.x,s.y,s.z],rotation=[rot.pitch,rot.yaw,rot.roll])
        if isinstance(a,u.StaticMeshActor):rows[n].update(mesh=a.static_mesh_component.static_mesh.get_path_name() if a.static_mesh_component.static_mesh else None,materials=[a.static_mesh_component.get_material(i).get_path_name() if a.static_mesh_component.get_material(i) else None for i in range(a.static_mesh_component.get_num_materials())])
    (OUT/'baseline.json').write_text(json.dumps(rows,indent=2))
for n,a in actors.items():
    if n.startswith('OH_FinalWallGrowth_'):A.destroy_actor(a)
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
source=(ROOT/'Content/Python/apply_hall_growth_water.py').read_text();exec(source[source.index('class Graph:'):source.index('\nmoss_keys=')])
path=D+'/AtmosphereFinish/M_OH_FinalReflection';water=E.load_asset(path) if E.does_asset_exist(path) else E.duplicate_asset(D+'/AtmosphereFinish/M_OH_LuminousCalmWater',path);water.modify();g=Graph(water);pos=g.n(u.MaterialExpressionWorldPosition)
q=g.mul(g.sub(pos,g.color((-65,940,2))),g.color((1/430,1/140,0)));dot=g.n(u.MaterialExpressionDotProduct);g.wire(q,dot,'A');g.wire(q,dot,'B');region=g.clamp(g.mul(g.sub(g.c(1),dot),g.c(2)))
n=g.noise(g.mul(pos,g.color((.50,.95,1))),.011);breaks=g.clamp(g.mul(g.sub(n,g.c(.53)),g.c(10)));highlight=g.mul(region,breaks)
g.prop(g.add(g.mul(g.color((.045,.16,.16)),g.c(110)),g.mul(g.color((1,.88,.57)),g.mul(highlight,g.c(850)))),u.MaterialProperty.MP_EMISSIVE_COLOR)
ML.recompile_material(water);assert E.save_loaded_asset(water,only_if_is_dirty=False);actors['OH_SM_OH_Blockout_21'].modify();actors['OH_SM_OH_Blockout_21'].static_mesh_component.set_material(0,water)
light=actors['OH_Finish_FocalSun'];light.modify();c=light.get_component_by_class(u.SpotLightComponent);c.set_editor_property('intensity',2200000);c.set_editor_property('volumetric_scattering_intensity',4.3)
# Pale backlit green behind the lower panes, with a higher transition to the bright sky.
path=D+'/AtmosphereFinish/M_OH_FinalBackdrop';haze=E.load_asset(path) if E.does_asset_exist(path) else E.duplicate_asset(D+'/AtmosphereFinish/M_OH_GradedHaze',path);haze.modify();ML.delete_all_material_expressions(haze);g=Graph(haze);pos=g.n(u.MaterialExpressionWorldPosition);x=g.mask(pos,0);z=g.mask(pos,2)
right=g.clamp(g.mul(g.sub(g.c(1400),x),g.c(1/3400)));height=g.clamp(g.mul(g.sub(z,g.c(1850)),g.c(1/1100)))
mass=g.add(g.mul(g.noise(pos,.0012),g.c(.75)),g.mul(g.noise(pos,.004),g.c(.25)));low=g.lerp(g.color((.085,.30,.13)),g.color((.48,.66,.26)),mass);sky=g.lerp(g.color((.48,.66,.66)),g.color((1,.95,.76)),right)
color=g.lerp(low,sky,height);g.prop(g.mul(color,g.lerp(g.c(950),g.c(1400),right)),u.MaterialProperty.MP_EMISSIVE_COLOR);ML.recompile_material(haze);assert E.save_loaded_asset(haze,only_if_is_dirty=False);actors['OH_Painterly_DistantHaze_000'].modify();actors['OH_Painterly_DistantHaze_000'].static_mesh_component.set_material(0,haze)
# Wall-rooted clusters, not trees behind the front elevation.
mesh=E.load_asset(D+'/FoliageRuntime/SM_OH_PaintedCrown_Runtime');mat=E.load_asset(D+'/AtmosphereFinish/M_OH_LeafColorMass');box=mesh.get_bounding_box();size=box.max-box.min;added=[]
for i,(x,z,width,height,depth) in enumerate([(-465,120,235,210,140),(-295,135,210,260,125),(210,135,240,240,130),(470,100,185,185,120)]):
    center=u.Vector(x,1960-depth*.5,z);a=A.spawn_actor_from_class(u.StaticMeshActor,center,u.Rotator());a.set_actor_label('OH_FinalWallGrowth_%02d'%i);c=a.static_mesh_component;c.set_static_mesh(mesh);c.set_material(0,mat);a.set_actor_scale3d(u.Vector(width/size.x,depth/size.y,height/size.z));actual,_=a.get_actor_bounds(False);a.set_actor_location(a.get_actor_location()+center-actual,False,False);c.set_collision_profile_name('NoCollision');c.set_cast_shadow(False);added.append(a.get_actor_label())
moved=[]
baseline=load_current_json((OUT/'baseline.json').read_text())
for n,a in actors.items():
    if n.startswith('OH_Tripo_Tree_'):
        p=baseline[n]['position'];a.modify();a.set_actor_location(u.Vector(1600 if p[0]>0 else -1600,p[1],p[2]),False,False);moved.append(n)
assert L.save_current_level();(OUT/'applied.json').write_text(json.dumps(dict(map=MAP,added=added,moved_side_trees=moved,water_material=water.get_path_name(),playtest=False),indent=2))
runpy.run_path(str(ROOT/'Content/Python/capture_hall_reference_final.py'))
