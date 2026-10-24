import unreal as u,time
from pathlib import Path
O=Path(u.Paths.project_dir())/'Saved/LockerPhotoUpdate';A=u.get_editor_subsystem(u.EditorActorSubsystem)
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
a=next(a for a in A.get_all_level_actors() if a.get_actor_label()=='S0_MemoryPhoto')
assert any(m and m.get_name()=='M_MemoryPhoto_Draft' for c in a.get_components_by_class(u.StaticMeshComponent) for m in c.get_materials())
cam=A.spawn_actor_from_class(u.CameraActor,u.Vector(3190,-48,229),u.Rotator(yaw=180),transient=True);cam.camera_component.set_field_of_view(65)
u.EditorLevelLibrary.pilot_level_actor(cam);u.EditorLevelLibrary.editor_set_game_view(True)
u.EditorPythonScripting.set_keep_python_script_alive(True);start=time.monotonic();sent=False
def tick(dt):
 global sent
 if not sent and time.monotonic()-start>15:
  u.AutomationLibrary.take_high_res_screenshot(1536,864,str(O/'applied.png'),camera=cam,delay=1);sent=True
 if sent and (O/'applied.png').exists():
  u.unregister_slate_post_tick_callback(handle);u.log('LOCKER_PHOTO_CAPTURE_DONE')
handle=u.register_slate_post_tick_callback(tick)
