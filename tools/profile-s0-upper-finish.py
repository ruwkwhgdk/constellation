"""Fixed-view paired GPU CSV; swap only fourteen rock meshes in memory, never save."""
import unreal as u,time,json,traceback
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/UpperFinishPerf_20261018';O.mkdir(parents=True,exist_ok=True)
u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
A=u.get_editor_subsystem(u.EditorActorSubsystem);world=u.EditorLevelLibrary.get_editor_world()
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
changes=json.loads((R/'Saved/S0WetFloor/UpperFinish_20261018/changes.json').read_text())
lightchange=json.loads((R/'Saved/S0WetFloor/UpperFinish_20261018/light-change.json').read_text())
cam=A.spawn_actor_from_class(u.CameraActor,u.Vector(2900,900,700),u.Rotator(pitch=-20,yaw=-138),transient=True);cam.camera_component.set_field_of_view(83)
u.EditorLevelLibrary.pilot_level_actor(cam);u.EditorLevelLibrary.editor_set_game_view(True)
u.get_editor_subsystem(u.LevelEditorSubsystem).editor_set_viewport_realtime(True)
for cmd in ['t.MaxFPS 0','r.VSync 0','r.SSR.Quality 3','r.GPUCsvStatsEnabled 1']:u.SystemLibrary.execute_console_command(world,cmd)
phases=['new','old','new_repeat'];S=dict(i=0,start=None,csv=False)
def tick(dt):
 try:
  u.EditorLevelLibrary.editor_invalidate_viewports()
  if time.monotonic()<S.get('cooldown',0):return
  if S['i']==len(phases):
   (O/'completed.json').write_text(json.dumps({'phases':phases,'map_saved':False}));u.unregister_slate_post_tick_callback(handle);exec((R/'tools/review-s0-window-finish.py').read_text(encoding='utf-8-sig'),globals());return
  name=phases[S['i']];now=time.monotonic()
  if S['start'] is None:
   for row in changes:
    actors[row['label']].static_mesh_component.set_material(row['slot'],u.load_asset(row['old'] if name=='old' else row['new']))
   light=actors[lightchange['label']];settings=lightchange['before' if name=='old' else 'after']
   light.set_actor_location(u.Vector(*settings['position']),False,True)
   light.get_component_by_class(u.LightComponent).set_intensity(settings['intensity'])
   u.SystemLibrary.execute_console_command(world,'csvprofile STARTFILE=S0UpperFinish_'+name+'.csv');S.update(start=now,csv=False);return
  elapsed=now-S['start']
  if elapsed>15 and not S['csv']:u.SystemLibrary.execute_console_command(world,'csvprofile START');S['csv']=True
  if elapsed>35:
   u.SystemLibrary.execute_console_command(world,'csvprofile STOP');S.update(i=S['i']+1,start=None,cooldown=time.monotonic()+10)
 except:
  (O/'error.txt').write_text(traceback.format_exc());u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
u.EditorPythonScripting.set_keep_python_script_alive(True);handle=u.register_slate_post_tick_callback(tick)
