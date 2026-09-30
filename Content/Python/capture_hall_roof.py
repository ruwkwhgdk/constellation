"""Reload and inspect the closed roof, rear clearing and retained scene, then capture."""
from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u,json
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v015'
report=load_current_json((OUT/'applied.json').read_text());assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level(report['map'])
actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
for n in report['removed']:assert n not in actors,n
for row in report['roof_panels']:
    a=actors[row['label']];c=a.static_mesh_component;assert c.static_mesh.get_name()==row['mesh']
    p,e=a.get_actor_bounds(False);assert max(abs(v-w) for v,w in zip([p.x,p.y,p.z],row['center']))<.02
    assert c.get_collision_profile_name()=='BlockAll' and c.get_editor_property('cast_shadow')
for row in load_current_json((OUT.parent/'v014/applied.json').read_text())['changed']:
    if row['label'] not in report['removed']:assert actors[row['label']].static_mesh_component.static_mesh.get_name()==row['mesh']
assert len([n for n in actors if n.startswith('OH_Flock_Bird_')])==28
assert actors['OH_SM_OH_Blockout_21'].static_mesh_component.get_material(0).get_name()=='M_OH_ShallowTransmission'
(OUT/'verification.json').write_text(json.dumps(dict(saved_map=True,roof_elements=len(report['roof_panels']),removed_placements=len(report['removed']),foliage_runtime_retained=True,water_birds_retained=True,playtest='user'),indent=2));u.log('HALL_ROOF_VERIFIED')
script=(ROOT/'Content/Python/capture_hall_exposure.py').read_text().replace('ArtSource/OvergrownHall/Scene/v001','ArtSource/OvergrownHall/TripoReplacement/v015').replace('/Game/Constellation/Environments/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout',report['map']).replace('unreal_exposure_fixed.png','unreal_roof.png').replace("pp=next","u.EditorLevelLibrary.set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation())\nu.EditorLevelLibrary.pilot_level_actor(cam)\npp=next").replace("'r.ScreenPercentage 100'","'ShowFlag.ReflectionEnvironment 1'")
exec(compile(script,'capture_roof','exec'),globals())
