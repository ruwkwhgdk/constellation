"""v018: camera-only reference composition; no world or gameplay-camera edits."""
import unreal as u,json,runpy,hashlib
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v018';MAP='/Game/Environment/OvergrownHall/TripoFull/Maps/L_OvergrownHall_TripoFull'
L=u.get_editor_subsystem(u.LevelEditorSubsystem);A=u.get_editor_subsystem(u.EditorActorSubsystem);assert L.load_level(MAP)
actors={a.get_actor_label():a for a in A.get_all_level_actors()};cam=actors['OH_ReferenceCamera'];cc=cam.get_component_by_class(u.CameraComponent)
def scene_signature():
    rows={}
    for n,a in actors.items():
        if n=='OH_ReferenceCamera':continue
        p=a.get_actor_location();r=a.get_actor_rotation();s=a.get_actor_scale3d()
        rows[n]=[round(v,4) for v in [p.x,p.y,p.z,r.pitch,r.yaw,r.roll,s.x,s.y,s.z]]
        if isinstance(a,u.StaticMeshActor):rows[n].append(a.static_mesh_component.static_mesh.get_path_name() if a.static_mesh_component.static_mesh else None)
    return hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
signature=scene_signature();cam.modify();cc.modify();cam.set_actor_location(u.Vector(0,100,112),False,False);cam.set_actor_rotation(u.Rotator(pitch=9.276398658752443,yaw=90,roll=0),False);cc.set_field_of_view(72.7)
assert signature==scene_signature();assert L.save_current_level()
(OUT/'applied.json').write_text(json.dumps(dict(map=MAP,position=[0,100,112],pitch=9.276398658752443,yaw=90,fov=72.7,actor_count=len(actors),scene_signature=signature,geometry_changed=False,gameplay_camera_changed=False,playtest='user'),indent=2))
runpy.run_path(str(ROOT/'Content/Python/capture_hall_composition.py'))
