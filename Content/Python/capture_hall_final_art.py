"""v013 saved-scene checks and reference-camera capture; gameplay testing belongs to the user."""
import unreal as u,json
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v013';D='/Game/Environment/OvergrownHall/TripoFull'
report=json.loads((OUT/'applied.json').read_text());assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level(report['map'])
actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
for row in report['architecture']:
    c=actors[row['label']].static_mesh_component;assert c.static_mesh.get_name()==row['mesh'];assert c.static_mesh.get_editor_property('body_setup').get_editor_property('collision_trace_flag')==u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
for row in report['added']:
    c=actors[row['label']].static_mesh_component;assert c.static_mesh.get_name()==row['mesh'];assert c.get_collision_profile_name()=='NoCollision'
assert len([n for n in actors if n.startswith('OH_Finish_')])==len(report['added'])+1
for row in json.loads((OUT.parent/'v010/applied.json').read_text())['changes']:
    c=actors[row['label']].static_mesh_component;assert c.static_mesh.get_name()=='SM_OH_Painted'+row['kind'];assert c.get_material(0).get_name()==('M_OH_LeafFar' if row['far'] else 'M_OH_LeafNear')
for row in json.loads((OUT.parent/'v011/applied.json').read_text())['changes']:assert actors[row['label']].static_mesh_component.static_mesh.get_name()==row['mesh']
water=actors['OH_SM_OH_Blockout_21'].static_mesh_component;assert water.get_material(0).get_name()=='M_OH_ShallowTransmission';assert water.get_collision_profile_name()=='NoCollision';assert water.get_material(0).get_editor_property('blend_mode')==u.BlendMode.BLEND_TRANSLUCENT
for row in json.loads((OUT.parent/'v012/applied.json').read_text())['floor_changes']:
    p=actors[row['label']].get_actor_location();assert max(abs(a-b) for a,b in zip([p.x,p.y,p.z],row['position']))<.01
assert len([n for n in actors if n.startswith('OH_Flock_Bird_')])==28
sun=actors['OH_Sun'];assert abs(sun.get_actor_rotation().yaw+55)<.01;assert sun.get_component_by_class(u.DirectionalLightComponent).get_editor_property('intensity')==17500
(OUT/'verification.json').write_text(json.dumps(dict(saved_map=True,architecture_count=len(report['architecture']),closed_architecture_collision=True,added_count=len(report['added']),nonblocking_details=True,foliage_v010_preserved=True,arches_v011_preserved=True,water_and_floor_v012_preserved=True,birds=28,playtest='user',performance_test=False),indent=2));u.log('HALL_FINAL_ART_VERIFIED')
script=(ROOT/'Content/Python/capture_hall_exposure.py').read_text().replace('ArtSource/OvergrownHall/Scene/v001','ArtSource/OvergrownHall/TripoReplacement/v013').replace('/Game/Environment/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout',report['map']).replace('unreal_exposure_fixed.png','unreal_final_art.png')
script=script.replace('pp=next',"u.EditorLevelLibrary.set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation())\nu.EditorLevelLibrary.pilot_level_actor(cam)\npp=next").replace("'r.ScreenPercentage 100'","'ShowFlag.ReflectionEnvironment 1'")
# Editor-only fixed-camera performance sample; excludes startup and high-res screenshot work.
script=script.replace('started=time.time(); requested=False','started=time.time(); requested=False; profile_started=False; profile_stopped=False')
script=script.replace('global requested','global requested,profile_started,profile_stopped')
script=script.replace('    if elapsed>45',"    if 10<elapsed<36:\n        u.get_editor_subsystem(u.LevelEditorSubsystem).editor_invalidate_viewports()\n    if elapsed>15 and not profile_started:\n        profile_started=True\n        u.SystemLibrary.execute_console_command(world,'CsvProfile STARTFILE=Hall_v013.csv')\n        u.SystemLibrary.execute_console_command(world,'CsvProfile START')\n    if elapsed>35 and not profile_stopped:\n        profile_stopped=True\n        u.SystemLibrary.execute_console_command(world,'CsvProfile STOP')\n    if elapsed>45")
exec(compile(script,'capture_final_art','exec'),globals())
