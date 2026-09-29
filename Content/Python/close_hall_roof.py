"""v015: close the roof with the maintained Tripo-derived module and clear rear trees."""
import unreal as u,json,math,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v015';OUT.mkdir(exist_ok=True)
D='/Game/Environment/OvergrownHall/TripoFull';MAP=D+'/Maps/L_OvergrownHall_TripoFull'
A=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem);E=u.EditorAssetLibrary
assert L.load_level(MAP)
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
def targeted(n):
    return n.startswith('OH_STRUCTURE_Roof_') or n.startswith('OH_FULL_26_') or (n.startswith('OH_Tripo_Tree_') and int(n.rsplit('_',1)[1])>=10) or (n.startswith('OH_Refine_Forest_') and int(n.rsplit('_',1)[1])<27) or (n.startswith('OH_Refine_Canopy_') and int(n.rsplit('_',1)[1])>=45)
def snapshot(a):
    c=a.static_mesh_component;p=a.get_actor_location();r=a.get_actor_rotation();s=a.get_actor_scale3d()
    return dict(mesh=c.static_mesh.get_path_name(),materials=[c.get_material(i).get_path_name() for i in range(c.get_num_materials())],position=[p.x,p.y,p.z],rotation=[r.pitch,r.yaw,r.roll],scale=[s.x,s.y,s.z])
if not (OUT/'baseline.json').exists():
    base={n:snapshot(a) for n,a in actors.items() if targeted(n)}
    (OUT/'baseline.json').write_text(json.dumps(base,indent=2))
base=json.loads((OUT/'baseline.json').read_text())
roof_material=E.load_asset(next(v['materials'][0] for n,v in base.items() if n.startswith('OH_STRUCTURE_Roof_')))
for n,a in actors.items():
    if targeted(n) or n.startswith('OH_ClosedRoof_'):assert A.destroy_actor(a)
mesh=E.load_asset(D+'/Meshes/SM_OH_Clean_26_RoofPanel');assert mesh
box=mesh.get_bounding_box();size=box.max-box.min
slope=.24;angle=math.degrees(math.atan(slope));rows=[]
# Four transverse strips, twelve longitudinal bays; overlap prevents slivers of sky.
for i,x in enumerate([-525,-175,175,525]):
    for j in range(12):
        y=-100+j*200;z=1280-abs(x)*slope
        a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(x,y,z),u.Rotator(pitch=angle if x<0 else -angle,yaw=0,roll=0))
        a.set_actor_label('OH_ClosedRoof_%02d_%02d'%(i,j));c=a.static_mesh_component;c.set_static_mesh(mesh);c.set_material(0,roof_material)
        a.set_actor_scale3d(u.Vector(354*math.sqrt(1+slope*slope)/size.x,204/size.y,1))
        center,extent=a.get_actor_bounds(False);p=a.get_actor_location();a.set_actor_location(p+u.Vector(x,y,z)-center,False,False)
        c.set_collision_profile_name('BlockAll');c.set_cast_shadow(True)
        rows.append(dict(label=a.get_actor_label(),center=[x,y,z],mesh=mesh.get_name()))
# The Tripo panel contains deliberate slat gaps. A continuous structural skin
# above the visible boards seals those gaps and overlaps the side wall tops.
cube=E.load_asset('/Engine/BasicShapes/Cube')
for side in [-1,1]:
    x=side*400;z=1290-400*slope
    a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(x,1000,z),u.Rotator(pitch=-side*angle,yaw=0,roll=0));a.set_actor_label('OH_ClosedRoof_Skin_'+str(side))
    c=a.static_mesh_component;c.set_static_mesh(cube);c.set_material(0,roof_material)
    a.set_actor_scale3d(u.Vector(8.06*math.sqrt(1+slope*slope),24.1,.18));c.set_collision_profile_name('BlockAll');c.set_cast_shadow(True)
    rows.append(dict(label=a.get_actor_label(),center=[x,1000,z],mesh=cube.get_name()))
assert L.save_current_level()
(OUT/'applied.json').write_text(json.dumps(dict(map=MAP,roof_panels=rows,removed=list(base),roof_material=roof_material.get_path_name(),lighting_changed=False,playtest='user'),indent=2))
runpy.run_path(str(ROOT/'Content/Python/capture_hall_roof.py'))
