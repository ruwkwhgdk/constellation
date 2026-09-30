from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u,json
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v027';r=load_current_json((OUT/'applied.json').read_text());assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level(r['map']);actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()};base=load_current_json((OUT/'baseline.json').read_text());assert len(actors)==len(base)==755
for n,b in base.items():
    a=actors[n];p=a.get_actor_location();s=a.get_actor_scale3d();rot=a.get_actor_rotation()
    for expected,actual in [(b['position'],[p.x,p.y,p.z]),(b['scale'],[s.x,s.y,s.z]),(b['rotation'],[rot.pitch,rot.yaw,rot.roll])]:assert all(abs(v-w)<.001 for v,w in zip(expected,actual)),n
    if b.get('mesh'):assert a.static_mesh_component.static_mesh.get_path_name()==b['mesh'],n
for n,props in r['lights'].items():
    cls=u.SkyLightComponent if n=='OH_Sky' else u.DirectionalLightComponent if n=='OH_Sun' else u.SpotLightComponent
    c=actors[n].get_component_by_class(cls)
    for k,v in props.items():assert abs(c.get_editor_property(k)-v)<.001,(n,k)
assert len([n for n in actors if n.startswith('OH_ClosedRoof_')])==50
assert len([n for n in actors if n.startswith('OH_Flock_Bird_')])==28
for n in load_current_json((OUT.parent/'v015/applied.json').read_text())['removed']:assert n not in actors
(OUT/'verification.json').write_text(json.dumps(dict(saved_map=True,actors=len(actors),existing_transforms_meshes_preserved=True,closed_roof=50,birds=28,light_settings_verified=True,playtest=False),indent=2));u.log('HALL_ACCEPTANCE_LIGHT_VERIFIED')
script=(ROOT/'Content/Python/capture_hall_exposure.py').read_text().replace('ArtSource/OvergrownHall/Scene/v001','ArtSource/OvergrownHall/TripoReplacement/v027').replace('/Game/Constellation/Environments/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout',r['map']).replace('unreal_exposure_fixed.png','unreal_acceptance.png').replace('pp=next',"u.EditorLevelLibrary.set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation())\nu.EditorLevelLibrary.pilot_level_actor(cam)\npp=next").replace("'r.ScreenPercentage 100'","'ShowFlag.ReflectionEnvironment 1'")
exec(compile(script,'capture_acceptance_light','exec'),globals())
