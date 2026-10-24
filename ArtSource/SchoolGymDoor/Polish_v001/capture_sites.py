import unreal as u,time,traceback
from pathlib import Path
P=Path(u.Paths.project_dir())/'ArtSource/SchoolGymDoor/Polish_v001/Reports'
A=u.get_editor_subsystem(u.EditorActorSubsystem)
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
targets={a.get_actor_label():a for a in A.get_all_level_actors() if a.get_actor_label() in ['gate','gate2']}
cam=A.spawn_actor_from_class(u.CameraActor,u.Vector(),transient=True);cam.camera_component.set_field_of_view(45)
names=['gate','gate2'];state={'i':0,'time':time.monotonic(),'sent':False}
def aim():
 a=targets[names[state['i']]];loc=a.get_actor_location();scale=a.get_actor_scale3d();target=loc+u.Vector(0,0,76*scale.z)
 pos=loc-a.get_actor_forward_vector()*(550*scale.z)+u.Vector(0,0,105*scale.z)
 cam.set_actor_location(pos,False,False);cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(pos,target),False)
 u.EditorLevelLibrary.pilot_level_actor(cam);u.EditorLevelLibrary.editor_set_game_view(True)
aim();u.EditorPythonScripting.set_keep_python_script_alive(True)
def finish():
 u.unregister_slate_post_tick_callback(handle);u.EditorPythonScripting.set_keep_python_script_alive(False);u.SystemLibrary.quit_editor()
def tick(dt):
 try:
  age=time.monotonic()-state['time'];name=names[state['i']]
  if age>18 and not state['sent']:
   state['sent']=True;u.AutomationLibrary.take_high_res_screenshot(1280,960,str(P/(name+'-in-map.png')),camera=cam,delay=1)
  elif age>23 and (P/(name+'-in-map.png')).exists():
   state['i']+=1
   if state['i']==len(names):finish();return
   state['time']=time.monotonic();state['sent']=False;aim()
  elif age>65:raise RuntimeError('Capture timed out')
 except Exception:
  (P/'sites-error.txt').write_text(traceback.format_exc());finish()
handle=u.register_slate_post_tick_callback(tick)
