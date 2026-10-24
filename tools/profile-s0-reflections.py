import unreal as u,time,json,traceback,statistics
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/PerfPass_20261018';O.mkdir(parents=True,exist_ok=True)
u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
A=u.get_editor_subsystem(u.EditorActorSubsystem);world=u.EditorLevelLibrary.get_editor_world()
actors=A.get_all_level_actors();p=next(a for a in actors if a.get_actor_label()=='S0_WetFloor_PlanarReflection');c=p.get_component_by_class(u.PlanarReflectionComponent)
cam=A.spawn_actor_from_class(u.CameraActor,u.Vector(2900,900,700),u.Rotator(pitch=-20,yaw=-138),transient=True);cam.camera_component.set_field_of_view(83);u.EditorLevelLibrary.pilot_level_actor(cam);u.EditorLevelLibrary.editor_set_game_view(True)
u.EditorPythonScripting.set_keep_python_script_alive(True)
for cmd in ['t.MaxFPS 0','r.VSync 0','r.SSR.Quality 3']:u.SystemLibrary.execute_console_command(world,cmd)
phases=['baseline','planar_off','all_reflections_off','planar_40','baseline_repeat'];S=dict(i=0,t=time.perf_counter(),last=time.perf_counter(),samples=[],started=False);results=[]
def tick(dt):
 try:
  now=time.perf_counter()
  if S['i']>=len(phases):
   (O/'timings.json').write_text(json.dumps(results,indent=2));u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor();return
  name=phases[S['i']]
  if not S['started']:
   c.set_visibility(name not in ['planar_off','all_reflections_off']);c.set_editor_property('screen_percentage',40 if name=='planar_40' else 75)
   u.SystemLibrary.execute_console_command(world,'r.SSR.Quality '+('0' if name=='all_reflections_off' else '3'))
   S.update(t=now,last=now,samples=[],started=True);return
  if now-S['t']>15:S['samples'].append((now-S['last'])*1000)
  S['last']=now
  if now-S['t']>35:
   xs=sorted(S['samples']);results.append(dict(phase=name,n=len(xs),median_ms=statistics.median(xs),p95_ms=xs[int(len(xs)*.95)],mean_ms=statistics.mean(xs)))
   (O/'timings-progress.json').write_text(json.dumps(results,indent=2));S.update(i=S['i']+1,started=False)
 except:
  (O/'error.txt').write_text(traceback.format_exc());u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(tick)
