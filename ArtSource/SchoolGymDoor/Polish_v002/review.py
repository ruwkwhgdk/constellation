import unreal as u,time,traceback,json
from pathlib import Path
P=Path(u.Paths.project_dir())/'ArtSource/SchoolGymDoor/Polish_v002'
A=u.get_editor_subsystem(u.EditorActorSubsystem)
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
target=next(a for a in A.get_all_level_actors() if a.get_actor_label()=='gate3')
loc=target.get_actor_location();pos=loc-target.get_actor_forward_vector()*1900+u.Vector(0,0,350);aim=loc+u.Vector(0,0,228)
cam=A.spawn_actor_from_class(u.CameraActor,pos,u.MathLibrary.find_look_at_rotation(pos,aim),transient=True);cam.camera_component.set_field_of_view(45)
u.EditorLevelLibrary.pilot_level_actor(cam);u.EditorLevelLibrary.editor_set_game_view(True)
state={'phase':'before_wait','start':time.monotonic(),'time':time.monotonic()-10}
u.EditorPythonScripting.set_keep_python_script_alive(True)
def phase(p):state['phase']=p;state['time']=time.monotonic()
def shot(name):u.AutomationLibrary.take_high_res_screenshot(1600,1000,str(P/'Reports'/name),camera=cam,delay=1)
def finish():
 u.unregister_slate_post_tick_callback(handle);u.EditorPythonScripting.set_keep_python_script_alive(False);u.SystemLibrary.quit_editor()
def tick(dt):
 try:
  age=time.monotonic()-state['time']
  if time.monotonic()-state['start']>240:raise RuntimeError('Review timeout')
  if state['phase']=='before' and age>20:
   phase('before_wait');shot('before.png')
  elif state['phase']=='before_wait' and age>5 and (P/'Reports/before.png').exists():
   phase('applying')
   exec(compile((P/'apply_surface.py').read_text(),str(P/'apply_surface.py'),'exec'),{'__file__':str(P/'apply_surface.py'),'PREVIEW_ONLY':False})
   phase('after')
  elif state['phase']=='after' and age>30:
   phase('after_wait');shot('after.png')
  elif state['phase']=='after_wait' and age>5 and (P/'Reports/after.png').exists():
   # Detail view, same real scene lighting, no light/material override.
   phase('detail_setup');p=loc-target.get_actor_forward_vector()*1100+u.Vector(0,0,135)
   cam.set_actor_location(p,False,False);cam.set_actor_rotation(u.MathLibrary.find_look_at_rotation(p,loc+u.Vector(0,0,60)),False)
   phase('detail')
  elif state['phase']=='detail' and age>5:
   phase('detail_wait');shot('detail.png')
  elif state['phase']=='detail_wait' and age>5 and (P/'Reports/detail.png').exists():finish()
 except Exception:
  (P/'Reports/error.txt').write_text(traceback.format_exc());finish()
handle=u.register_slate_post_tick_callback(tick)


