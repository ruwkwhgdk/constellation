import unreal as u,time
from pathlib import Path
O=Path(u.Paths.project_dir())/'Saved/S0GirlReview';A=u.get_editor_subsystem(u.EditorActorSubsystem)
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
g=next(a for a in A.get_all_level_actors() if a.get_actor_label()=='S0_LittleGirl_Blocking');g.set_actor_location(u.Vector(2770,0,67),False,True);g.set_actor_rotation(u.Rotator(yaw=-90),False)
cam=A.spawn_actor_from_class(u.CameraActor,u.Vector(3165,0,213.6),u.Rotator(pitch=-10,yaw=180),transient=True);cam.camera_component.set_field_of_view(115)
u.EditorLevelLibrary.pilot_level_actor(cam);u.EditorLevelLibrary.editor_set_game_view(True);u.EditorPythonScripting.set_keep_python_script_alive(True)
start=time.monotonic();i=0;last=0
def tick(dt):
 global i,last
 if time.monotonic()-start<15 or time.monotonic()-last<5:return
 if i==3:u.unregister_slate_post_tick_callback(h);u.log('PROBE_DONE');return
 z=[213.6,212.6,214.6][i];cam.set_actor_location(u.Vector(3165,0,z),False,True)
 u.AutomationLibrary.take_high_res_screenshot(1536,864,str(O/('probe-'+str(i)+'.png')),camera=cam,delay=1);i+=1;last=time.monotonic()
h=u.register_slate_post_tick_callback(tick)
