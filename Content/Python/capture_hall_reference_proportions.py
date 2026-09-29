import unreal as u,json
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v024';r=json.loads((OUT/'applied.json').read_text());assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level(r['map'])
actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()};base=json.loads((OUT/'baseline.json').read_text());assert len(actors)==len(base)+len(r['added'])
for n,b in base.items():
    a=actors[n]
    if n not in r['changed']:
        p=a.get_actor_location();s=a.get_actor_scale3d();rot=a.get_actor_rotation()
        for expected,actual in [(b['position'],[p.x,p.y,p.z]),(b['scale'],[s.x,s.y,s.z]),(b['rotation'],[rot.pitch,rot.yaw,rot.roll])]:assert all(abs(v-w)<.001 for v,w in zip(expected,actual)),n
    if b.get('mesh'):assert a.static_mesh_component.static_mesh.get_path_name()==b['mesh'],n
for row in r['windows']:
    a=actors[row['label']];assert abs(a.get_actor_location().x-row['center_x'])<.01
    size=a.static_mesh_component.static_mesh.get_bounding_box();assert abs((size.max.x-size.min.x)*a.get_actor_scale3d().x-row['width_cm'])<.1
for n in r['side_members']:
    center,extent=actors[n].get_actor_bounds(False);assert center.z-extent.z>300
for n in r['added']:assert actors[n].static_mesh_component.get_collision_profile_name()==('BlockAll' if 'UpperWall' in n else 'NoCollision')
assert len([n for n in actors if n.startswith('OH_ClosedRoof_')])==50
assert len([n for n in actors if n.startswith('OH_Flock_Bird_')])==28
for n in json.loads((OUT.parent/'v015/applied.json').read_text())['removed']:assert n not in actors
(OUT/'verification.json').write_text(json.dumps(dict(saved_map=True,actors=len(actors),changed_transforms=len(r['changed']),unrelated_transforms_preserved=True,all_existing_meshes_preserved=True,window_configuration='three broad bays and one narrow partial bay',closed_roof=50,birds=28,playtest=False),indent=2));u.log('HALL_REFERENCE_PROPORTIONS_VERIFIED')
script=(ROOT/'Content/Python/capture_hall_exposure.py').read_text().replace('ArtSource/OvergrownHall/Scene/v001','ArtSource/OvergrownHall/TripoReplacement/v024').replace('/Game/Environment/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout',r['map']).replace('unreal_exposure_fixed.png','unreal_reference_proportions.png').replace('pp=next',"u.EditorLevelLibrary.set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation())\nu.EditorLevelLibrary.pilot_level_actor(cam)\npp=next").replace("'r.ScreenPercentage 100'","'ShowFlag.ReflectionEnvironment 1'")
exec(compile(script,'capture_reference_proportions','exec'),globals())
