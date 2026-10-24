"""Saved-map GPU sample from main and upper views; no scene changes."""
import unreal as u,time,json,traceback,hashlib
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/SavedViews_20261019'
O.mkdir(parents=True,exist_ok=True)
mapfile=R/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
assert not (O/'session.json').exists(),'Use a fresh run directory'
before=hashlib.sha256(mapfile.read_bytes()).hexdigest()
(O/'session.json').write_text(json.dumps(dict(map_sha256=before)))
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
A=u.get_editor_subsystem(u.EditorActorSubsystem);world=u.EditorLevelLibrary.get_editor_world()
cam=A.spawn_actor_from_class(u.CameraActor,u.Vector(2900,900,700),u.Rotator(pitch=-20,yaw=-138),transient=True)
cam.camera_component.set_field_of_view(83);u.EditorLevelLibrary.pilot_level_actor(cam);u.EditorLevelLibrary.editor_set_game_view(True)
u.get_editor_subsystem(u.LevelEditorSubsystem).editor_set_viewport_realtime(True)
for cmd in ['t.MaxFPS 0','r.VSync 0','r.SSR.Quality 3','r.GPUCsvStatsEnabled 1']:u.SystemLibrary.execute_console_command(world,cmd)
phases=['main','upper','main_repeat']
S=dict(i=0,start=None,csv=False)
def tick(dt):
 try:
  u.EditorLevelLibrary.editor_invalidate_viewports()
  if time.monotonic()<S.get('cooldown',0):return
  if S['i']==len(phases):
   assert hashlib.sha256(mapfile.read_bytes()).hexdigest()==before,'Map changed externally'
   (O/'completed.json').write_text(json.dumps(dict(phases=phases,map_saved=False,map_unchanged=True)))
   u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor();return
  name=phases[S['i']];now=time.monotonic()
  if S['start'] is None:
   pos,rot=((1450,1500,1500),(-30,105)) if name=='upper' else ((2900,900,700),(-20,-138))
   cam.set_actor_location(u.Vector(*pos),False,True);cam.set_actor_rotation(u.Rotator(pitch=rot[0],yaw=rot[1]),False)
   u.SystemLibrary.execute_console_command(world,'csvprofile STARTFILE=S0SavedViews_'+name+'.csv')
   (O/'phase.json').write_text(json.dumps(dict(phase=name)))
   S.update(start=now,csv=False,shot=False);return
  elapsed=now-S['start']
  if elapsed>10 and not S['shot']:
   u.AutomationLibrary.take_high_res_screenshot(1600,900,str(O/(name+'.png')),camera=cam,delay=1);S['shot']=True
  if elapsed>18 and not S['csv']:u.SystemLibrary.execute_console_command(world,'csvprofile START');S['csv']=True
  if elapsed>38:
   u.SystemLibrary.execute_console_command(world,'csvprofile STOP');S.update(i=S['i']+1,start=None,cooldown=time.monotonic()+10)
 except:
  (O/'error.txt').write_text(traceback.format_exc());u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
u.EditorPythonScripting.set_keep_python_script_alive(True);handle=u.register_slate_post_tick_callback(tick)
