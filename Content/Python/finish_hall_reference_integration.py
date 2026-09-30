"""v025: integrated spandrel geometry, rooted shrub silhouettes and soft rear masonry."""
import unreal as u,json,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir())
# Apply the maintained v024 recipe without scheduling its capture/quit callback.
source=(ROOT/'Content/Python/refine_hall_reference_proportions.py').read_text();exec(compile(source.rsplit('\nrunpy.run_path',1)[0],'maintained_v024','exec'),{})
OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v025';OUT.mkdir(parents=True,exist_ok=True);D='/Game/Constellation/Environments/OvergrownHall/TripoFull';MAP='/Game/Constellation/Worlds/OvergrownHall/Maps/L_OvergrownHall_TripoFull'
E=u.EditorAssetLibrary;ML=u.MaterialEditingLibrary;A=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem);assert L.load_level(MAP);actors={a.get_actor_label():a for a in A.get_all_level_actors()}
if not (OUT/'baseline.json').exists():
    rows={}
    for n,a in actors.items():
        p=a.get_actor_location();s=a.get_actor_scale3d();r=a.get_actor_rotation();rows[n]=dict(position=[p.x,p.y,p.z],scale=[s.x,s.y,s.z],rotation=[r.pitch,r.yaw,r.roll])
        if isinstance(a,u.StaticMeshActor):rows[n].update(mesh=a.static_mesh_component.static_mesh.get_path_name() if a.static_mesh_component.static_mesh else None,materials=[a.static_mesh_component.get_material(i).get_path_name() if a.static_mesh_component.get_material(i) else None for i in range(a.static_mesh_component.get_num_materials())])
    (OUT/'baseline.json').write_text(json.dumps(rows,indent=2))
for n,a in actors.items():
    if n.startswith('OH_ReferenceIntegration_'):A.destroy_actor(a)
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
source=(ROOT/'Content/Python/apply_hall_growth_water.py').read_text();exec(source[source.index('class Graph:'):source.index('\nmoss_keys=')])
mesh=E.load_asset(D+'/FoliageRuntime/SM_OH_PaintedShrub_Runtime');leaf=E.load_asset(D+'/AtmosphereFinish/M_OH_LeafColorMass');size=mesh.get_bounding_box();size=size.max-size.min;changed=[]
def fit(a,center,dimensions):
    a.modify();c=a.static_mesh_component;c.set_static_mesh(mesh);c.set_material(0,leaf);c.set_material(1,mesh.get_material(1));a.set_actor_scale3d(u.Vector(dimensions[0]/size.x,dimensions[1]/size.y,dimensions[2]/size.z));actual,_=a.get_actor_bounds(False);a.set_actor_location(a.get_actor_location()+center-actual,False,False);c.set_collision_profile_name('NoCollision');c.set_cast_shadow(False)
for i,(x,width,height,depth) in enumerate([(-465,270,125,150),(-295,300,195,165),(210,310,145,160),(470,225,170,135)]):
    n='OH_FinalWallGrowth_%02d'%i;a=actors[n];fit(a,u.Vector(x,1960-depth/2,height/2+3),(width,depth,height));changed.append(n)
added=[]
for i,(x,width,height) in enumerate([(410,115,90),(65,175,70),(-365,80,115)]):
    a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(x,1928,665),u.Rotator());a.set_actor_label('OH_ReferenceIntegration_LintelLeaves_%02d'%i);fit(a,u.Vector(x,1928,665),(width,65,height));added.append(a.get_actor_label())
path=D+'/AtmosphereFinish/M_OH_RearWallIntegrated';m=E.load_asset(path) if E.does_asset_exist(path) else E.duplicate_asset(D+'/FinishMaterials/M_OH_Weathered_05',path);m.modify();g=Graph(m);pos=g.n(u.MaterialExpressionWorldPosition);n=g.noise(pos,.007)
stone=g.lerp(g.color((.11,.18,.20)),g.color((.28,.34,.32)),n);low=g.clamp(g.sub(g.c(1),g.mul(g.mask(pos,2),g.c(1/360))));patch=g.mul(low,g.clamp(g.mul(g.sub(g.c(.60),g.noise(pos,.012)),g.c(3))))
color=g.lerp(stone,g.color((.19,.32,.065)),g.mul(patch,g.c(.65)));g.prop(color,u.MaterialProperty.MP_BASE_COLOR);g.prop(g.mul(color,g.c(130)),u.MaterialProperty.MP_EMISSIVE_COLOR);ML.recompile_material(m);assert E.save_loaded_asset(m,only_if_is_dirty=False)
walls=[]
for n,a in actors.items():
    if n.startswith('OH_FULL_05_') and a.get_actor_location().y>1900 and a.get_actor_location().z<50:a.modify();a.static_mesh_component.set_material(0,m);walls.append(n)
assert L.save_current_level();(OUT/'applied.json').write_text(json.dumps(dict(map=MAP,changed_shrubs=changed,added=added,rear_walls=walls,playtest=False),indent=2))
runpy.run_path(str(ROOT/'Content/Python/capture_hall_reference_integration.py'))
