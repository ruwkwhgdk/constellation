import unreal as u,time
from pathlib import Path
O=Path(u.Paths.project_dir())/'Saved/S0Opening';A=u.get_editor_subsystem(u.EditorActorSubsystem)
u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
actors=A.get_all_level_actors()
for a in actors:
 if a.get_actor_label()=='S0_InteriorFill':a.point_light_component.set_intensity(.2)
 if a.get_actor_label()=='S0_LittleGirl_Blocking':a.set_actor_location(u.Vector(3010,0,67),False,True)
cam=A.spawn_actor_from_class(u.CameraActor,u.Vector(3192,0,165),u.Rotator(yaw=180),transient=True);cam.camera_component.set_field_of_view(75)
u.EditorLevelLibrary.pilot_level_actor(cam)
u.EditorLevelLibrary.editor_set_game_view(True)
(O/'girl-bounds.txt').write_text(str(next(a for a in actors if a.get_actor_label()=='S0_LittleGirl_Blocking').get_actor_bounds(False)))
shots=[('inside-v2',(3192,0,165),u.Rotator(yaw=180)),('photo-v2',(3187,-5,170),u.Rotator(yaw=202,pitch=10)),('slit-v3',(3158,0,245),u.Rotator(yaw=180)),('girl-v2',(3192,0,165),u.Rotator(yaw=180,pitch=-13))]
u.EditorPythonScripting.set_keep_python_script_alive(True);S={'index':0,'sent':False,'last':time.monotonic(),'start':time.monotonic()}
def tick(dt):
 if time.monotonic()-S['start']>180:u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor();return
 if S['index']>=len(shots):u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor();return
 name,pos,rot=shots[S['index']];path=O/(name+'.png')
 if S['sent']:
  if path.exists():S['index']+=1;S['sent']=False;S['last']=time.monotonic()
  return
 cam.set_actor_location(u.Vector(*pos),False,True);cam.set_actor_rotation(rot,False)
 if name=='girl-v2':
  door=next(a for a in actors if a.get_actor_label()=='S0_LockerDoor');door.set_actor_rotation(u.Rotator(yaw=-15),False)
 if time.monotonic()-S['last']>6:
  u.AutomationLibrary.take_high_res_screenshot(1280,720,str(path),camera=cam,delay=1);S['sent']=True
handle=u.register_slate_post_tick_callback(tick)
