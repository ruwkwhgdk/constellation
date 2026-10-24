import unreal as u,time
from pathlib import Path
O=Path(u.Paths.project_dir())/'Saved/SlimeKeyring';A=u.get_editor_subsystem(u.EditorActorSubsystem)
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
actors=A.get_all_level_actors();a=next(a for a in actors if a.get_actor_label()=='slime_keyring')
assert not any(a.get_actor_label().startswith('S0_Charm_') for a in actors)
assert a.get_attach_parent_actor().get_actor_label()=='S0_LockerDoor'
assert abs(a.get_actor_rotation().yaw+90)<.1
cam=A.spawn_actor_from_class(u.CameraActor,u.Vector(3200,-49,194),u.Rotator(yaw=180),transient=True);cam.camera_component.set_field_of_view(85)
u.EditorLevelLibrary.pilot_level_actor(cam);u.EditorLevelLibrary.editor_set_game_view(True)
u.EditorPythonScripting.set_keep_python_script_alive(True);start=time.monotonic();sent=False
def tick(dt):
 global sent
 if not sent and time.monotonic()-start>15:
  u.AutomationLibrary.take_high_res_screenshot(1536,864,str(O/'final-front.png'),camera=cam,delay=1);sent=True
 if (sent and (O/'final-front.png').exists()) or time.monotonic()-start>90:
  u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.execute_console_command(None,'QUIT')
handle=u.register_slate_post_tick_callback(tick)
