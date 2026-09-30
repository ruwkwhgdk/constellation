"""Fresh saved-map validation and real renderer capture for v011."""
from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u,json
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v011';D='/Game/Constellation/Environments/OvergrownHall/TripoFull'
report=load_current_json((OUT/'applied.json').read_text());assert u.get_editor_subsystem(u.LevelEditorSubsystem).load_level(report['map'])
actors={a.get_actor_label():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
previous=load_current_json((OUT.parent/'v010/applied.json').read_text())
for row in previous['changes']:
    c=actors[row['label']].static_mesh_component
    assert c.static_mesh.get_name()=='SM_OH_Painted'+row['kind']
    assert c.get_material(0).get_name()==('M_OH_LeafFar' if row['far'] else 'M_OH_LeafNear')
for row in report['changes']:
    c=actors[row['label']].static_mesh_component;assert c.static_mesh.get_name()==row['mesh']
    assert c.static_mesh.get_editor_property('body_setup').get_editor_property('collision_trace_flag')==u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
water=actors['OH_SM_OH_Blockout_21'];c=water.static_mesh_component
assert c.static_mesh.get_name()==report['water_mesh'] and c.get_material(0).get_name()==report['water_material']
assert c.get_collision_profile_name()=='NoCollision'
assert not c.get_material(0).get_editor_property('tangent_space_normal')
center,ext=water.get_actor_bounds(False);assert abs(center.y-700)<1 and 625<ext.x<645 and 870<ext.y<885
assert len([n for n in actors if n.startswith('OH_Flock_Bird_')])==28
assert abs(actors['OH_Sun'].get_actor_rotation().yaw+55)<.01
(OUT/'verification.json').write_text(json.dumps(dict(saved_map=True,foliage_preserved=previous['counts'],broken_arch_count=len(report['changes']),closed_arch_collision=True,nonblocking_water=True,water_center=[center.x,center.y,center.z],world_space_normals=True,birds=28,physical_transmission=False,playtest=False,performance_test=False),indent=2))
u.log('WATER_RUINS_VERIFIED')
script=(ROOT/'Content/Python/capture_hall_exposure.py').read_text().replace('ArtSource/OvergrownHall/Scene/v001','ArtSource/OvergrownHall/TripoReplacement/v011').replace('/Game/Constellation/Environments/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout',report['map']).replace('unreal_exposure_fixed.png','unreal_water_ruins.png')
script=script.replace('pp=next',"u.EditorLevelLibrary.set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation())\nu.EditorLevelLibrary.pilot_level_actor(cam)\npp=next");script=script.replace("'r.ScreenPercentage 100'","'ShowFlag.ReflectionEnvironment 1'")
# A second real-time frame exposes frozen shader-time or missing ripple animation.
script=script.replace('started=time.time(); requested=False','started=time.time(); requested=False; requested_second=False')
script=script.replace('global requested','global requested,requested_second')
script=script.replace("    shot=out/", "    if elapsed>55 and not requested_second:\n        requested_second=True\n        u.AutomationLibrary.take_high_res_screenshot(1200,640,str(out/'water_later.png'),camera=cam,delay=2)\n    shot=out/")
exec(compile(script,'capture_water_ruins','exec'),globals())
