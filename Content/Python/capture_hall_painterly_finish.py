import unreal as u,json
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v016';report=json.loads((OUT/'applied.json').read_text())
assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level(report['map'])
actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
for n in report['added']:assert n in actors and actors[n].static_mesh_component.get_collision_profile_name()=='NoCollision'
for n in json.loads((OUT.parent/'v015/applied.json').read_text())['removed']:assert n not in actors
assert len([n for n in actors if n.startswith('OH_ClosedRoof_')])==50
for n,a in actors.items():
    if n.startswith('OH_ClosedRoof_'):assert a.static_mesh_component.get_material(0).get_path_name()==report['roof_material'];assert a.static_mesh_component.get_collision_profile_name()=='BlockAll'
    if n.startswith(('OH_FULL_01_','OH_FULL_02_','OH_FULL_03_','OH_FULL_04_')):assert '/PainterlyFinish/' in a.static_mesh_component.get_material(0).get_path_name()
for n in report['shrubs']:
    c=actors[n].static_mesh_component;assert c.static_mesh.get_name()=='SM_OH_PaintedShrub_Runtime';assert c.get_collision_profile_name()=='NoCollision'
assert actors['OH_SM_OH_Blockout_21'].static_mesh_component.get_material(0).get_path_name()==report['water_material']
birds=[a for n,a in actors.items() if n.startswith('OH_Flock_Bird_')];assert len(birds)==28
for a in birds:assert a.skeletal_mesh_component.get_material(0).get_path_name()==report['bird_material']
routes=json.loads((OUT/'Flock/routes.json').read_text());assert routes['minimum_center_distance_cm']>15
for bird in routes['birds']:
    p=actors[bird['name']].get_actor_location();assert max(abs(v-w) for v,w in zip([p.x,p.y,p.z],bird['samples'][0]['position_cm']))<.1
(OUT/'verification.json').write_text(json.dumps(dict(saved_map=True,added=len(report['added']),shrubs=len(report['shrubs']),closed_roof=50,birds=28,minimum_bird_spacing_cm=routes['minimum_center_distance_cm'],rear_trees_absent=True,playtest='user'),indent=2));u.log('HALL_PAINTERLY_FINISH_VERIFIED')
script=(ROOT/'Content/Python/capture_hall_exposure.py').read_text().replace('ArtSource/OvergrownHall/Scene/v001','ArtSource/OvergrownHall/TripoReplacement/v016').replace('/Game/Environment/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout',report['map']).replace('unreal_exposure_fixed.png','unreal_finish.png').replace('pp=next',"u.EditorLevelLibrary.set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation())\nu.EditorLevelLibrary.pilot_level_actor(cam)\npp=next").replace("'r.ScreenPercentage 100'","'ShowFlag.ReflectionEnvironment 1'")
exec(compile(script,'capture_painterly_finish','exec'),globals())
