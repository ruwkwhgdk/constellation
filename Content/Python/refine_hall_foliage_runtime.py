"""v014: preserve approved near shapes, add foliage LODs and restrained leaf-only wind."""
import unreal as u,json,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v014';OUT.mkdir(exist_ok=True)
D='/Game/Environment/OvergrownHall/TripoFull';MAP=D+'/Maps/L_OvergrownHall_TripoFull'
E=u.EditorAssetLibrary;ML=u.MaterialEditingLibrary;SM=u.get_editor_subsystem(u.StaticMeshEditorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem);A=u.get_editor_subsystem(u.EditorActorSubsystem)
assert L.load_level(MAP)
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
basepath=OUT/'baseline.json'
if not basepath.exists():
    snapshot={}
    for n,a in actors.items():
        if not isinstance(a,u.StaticMeshActor):continue
        c=a.static_mesh_component
        if not c.static_mesh or c.static_mesh.get_name() not in ['SM_OH_PaintedTree','SM_OH_PaintedShrub','SM_OH_PaintedCrown','SM_OH_Soft_18_Vine']:continue
        p=a.get_actor_location();snapshot[n]=dict(mesh=c.static_mesh.get_path_name(),shadow=c.get_editor_property('cast_shadow'),material=c.get_material(0).get_path_name(),position=[p.x,p.y,p.z])
    basepath.write_text(json.dumps(snapshot,indent=2))
base=json.loads(basepath.read_text());source=(ROOT/'Content/Python/apply_hall_growth_water.py').read_text();exec(source[source.index('class Graph:'):source.index('\nmoss_keys=')])
wind={}
for far in [False,True]:
    suffix='Far' if far else 'Near';src=D+'/FoliagePaint/M_OH_Leaf'+suffix;dst=D+'/FoliageRuntime/M_OH_LeafWind'+suffix
    new_material=not E.does_asset_exist(dst)
    m=E.duplicate_asset(src,dst) if new_material else E.load_asset(dst);assert m
    # Rebuild from the approved material copy once. Repeated runs reuse this graph unchanged.
    if new_material or not (OUT/'wind_graphs_created.json').exists():
        g=Graph(m);pos=g.n(u.MaterialExpressionWorldPosition);time=g.n(u.MaterialExpressionTime)
        phase=g.add(g.mul(time,g.c(.105)),g.add(g.mul(g.mask(pos,0),g.c(.0017)),g.mul(g.mask(pos,1),g.c(.0011))))
        wave=g.n(u.MaterialExpressionSine);g.wire(phase,wave)
        detail=g.n(u.MaterialExpressionSine);g.wire(g.add(g.mul(phase,g.c(1.83)),g.c(.31)),detail)
        amount=g.add(g.mul(wave,g.c(.36 if far else .72)),g.mul(detail,g.c(.10 if far else .20)))
        g.prop(g.mul(g.color((.65,1,.07)),amount),u.MaterialProperty.MP_WORLD_POSITION_OFFSET)
        ML.recompile_material(m);assert E.save_loaded_asset(m,only_if_is_dirty=False)
    wind[suffix]=m
(OUT/'wind_graphs_created.json').write_text(json.dumps(dict(near_max_cm=.92,far_max_cm=.46,leaf_slots_only=True,base_texture_preserved=True),indent=2))
meshes={};lod_report=[]
for kind in ['Tree','Shrub','Crown']:
    original=E.load_asset(D+'/Meshes/SM_OH_Painted'+kind);dst=D+'/FoliageRuntime/SM_OH_Painted'+kind+'_Runtime'
    mesh=E.load_asset(dst) if E.does_asset_exist(dst) else E.duplicate_asset(original.get_path_name().split('.')[0],dst);assert mesh
    options=u.StaticMeshReductionOptions();options.auto_compute_lod_screen_size=False
    screens=[1,.08,.025] if kind=='Shrub' else [1,.24,.10]
    settings=[]
    for ratio,screen in zip([1,.60,.30],screens):
        setting=u.StaticMeshReductionSettings();setting.percent_triangles=ratio;setting.screen_size=screen;settings.append(setting)
    options.reduction_settings=settings;assert SM.set_lods(mesh,options)==3
    triangles=[mesh.get_num_triangles(i) for i in range(3)];assert triangles[0]==original.get_num_triangles(0) and triangles[2]<triangles[1]<triangles[0]
    mesh.set_editor_property('positive_bounds_extension',u.Vector(2,2,2));mesh.set_editor_property('negative_bounds_extension',u.Vector(2,2,2));mesh.set_material(0,wind['Near']);assert E.save_loaded_asset(mesh,only_if_is_dirty=False)
    meshes[kind]=mesh;lod_report.append(dict(kind=kind,mesh=mesh.get_name(),triangles=triangles,screen_sizes=screens))
changed=[];shadow_changes=[]
for name,b in base.items():
    actor=actors[name];c=actor.static_mesh_component;actor.modify()
    kind=next((k for k in meshes if b['mesh'].split('.')[-1]=='SM_OH_Painted'+k),None)
    if kind:
        far=b['material'].split('.')[-1]=='M_OH_LeafFar';c.set_static_mesh(meshes[kind]);c.set_material(0,wind['Far' if far else 'Near'])
        changed.append(dict(label=name,kind=kind,far=far,mesh=meshes[kind].get_name()))
    # Retain foreground/tree shadows. Remove tiny seam shadows and distant backdrop crown shadows.
    disable=(name.startswith('OH_Finish_AttachedVine_') or name.startswith('OH_Finish_SeamLeaves_') or (kind=='Crown' and b['position'][1]>2900))
    c.set_cast_shadow(False if disable else b['shadow'])
    if disable and b['shadow']:shadow_changes.append(name)
# The focal spot is an artistic fill, overlapping the preserved sun's shadows.
# Keep the sun and structural cast shadows; avoid a second full foliage shadow pass.
focal=actors['OH_Finish_FocalSun'];focal.modify();focal.get_component_by_class(u.SpotLightComponent).set_editor_property('cast_shadows',False)
reflection=actors['OH_WaterPlanarReflection'];reflection.modify();reflection.get_component_by_class(u.PlanarReflectionComponent).set_editor_property('screen_percentage',60)
assert L.save_current_level()
(OUT/'applied.json').write_text(json.dumps(dict(map=MAP,lods=lod_report,changed=changed,shadow_disabled=shadow_changes,focal_fill_shadows=False,reflection_screen_percentage=60,actor_count=len(actors),playtest='user'),indent=2))
runpy.run_path(str(ROOT/'Content/Python/capture_hall_runtime.py'))
