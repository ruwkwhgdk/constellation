"""Read-only loaded-world survey; never saves or modifies StartIsland."""
import unreal as u,json,hashlib
from pathlib import Path
root=Path(u.Paths.project_dir());out=root/'ArtSource/SubwayEntrance/Design';out.mkdir(parents=True,exist_ok=True)
package='/Game/Constellation/Worlds/StartIsland/Maps/L_StartIsland';file=root/'Content/Levels/L_StartIsland.umap';before=hashlib.sha256(file.read_bytes()).hexdigest()
L=u.get_editor_subsystem(u.LevelEditorSubsystem);assert L.load_level(package)
A=u.get_editor_subsystem(u.EditorActorSubsystem);rows=[]
for a in A.get_all_level_actors():
    p=a.get_actor_location();c,e=a.get_actor_bounds(False);r=a.get_actor_rotation()
    row=dict(label=a.get_actor_label(),class_name=a.get_class().get_name(),position=[p.x,p.y,p.z],rotation=[r.pitch,r.yaw,r.roll],bounds_center=[c.x,c.y,c.z],bounds_extent=[e.x,e.y,e.z])
    if isinstance(a,u.StaticMeshActor):
        m=a.static_mesh_component;row['mesh']=m.static_mesh.get_path_name() if m.static_mesh else None;row['collision']=str(m.get_collision_profile_name())
    rows.append(row)
after=hashlib.sha256(file.read_bytes()).hexdigest();assert before==after
(out/'site_survey.json').write_text(json.dumps(dict(map=package,saved=False,map_sha256=after,map_unchanged=True,scope='Loaded editor world only; unloaded streamed/partitioned actors may be absent. This is not a placement or gameplay approval.',actors=rows),indent=2),encoding='utf-8')
u.log('SUBWAY_SITE_SURVEY_OK '+str(len(rows)))
