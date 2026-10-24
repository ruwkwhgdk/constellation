"""Fixed-view paired GPU CSV; swap only seven fascia in memory, never save."""
import unreal as u,time,json,traceback
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/ClosedLedgePerf_20261018';O.mkdir(parents=True,exist_ok=True)
u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
A=u.get_editor_subsystem(u.EditorActorSubsystem);world=u.EditorLevelLibrary.get_editor_world()
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
changes=json.loads((R/'Saved/S0WetFloor/ClosedLedge_20261018/changes.json').read_text())
old={r['label']:r for r in json.loads((R/'Saved/S0WetFloor/LedgeDepth_20261018/before.json').read_text())}
new={r['label']:(actors[r['label']].get_actor_transform(),actors[r['label']].static_mesh_component.static_mesh) for r in changes}
cam=A.spawn_actor_from_class(u.CameraActor,u.Vector(2900,900,700),u.Rotator(pitch=-20,yaw=-138),transient=True);cam.camera_component.set_field_of_view(83)
u.EditorLevelLibrary.pilot_level_actor(cam);u.EditorLevelLibrary.editor_set_game_view(True)
u.get_editor_subsystem(u.LevelEditorSubsystem).editor_set_viewport_realtime(True)
for cmd in ['t.MaxFPS 0','r.VSync 0','r.SSR.Quality 3','r.GPUCsvStatsEnabled 1']:u.SystemLibrary.execute_console_command(world,cmd)
phases=['new','old','new_repeat'];S=dict(i=0,start=None,csv=False)
def tick(dt):
 try:
  u.EditorLevelLibrary.editor_invalidate_viewports()
  if S['i']==len(phases):
   (O/'completed.json').write_text(json.dumps({'phases':phases,'map_saved':False}));u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor();return
  name=phases[S['i']];now=time.monotonic()
  if S['start'] is None:
   for row in changes:
    label=row['label'];a=actors[label];c=a.static_mesh_component;materials=list(c.get_materials())
    if name=='old':
     c.set_static_mesh(u.load_asset(row['mesh']));a.set_actor_scale3d(u.Vector(*old[label]['scale']));a.set_actor_location(u.Vector(*old[label]['location']),False,True)
    else:
     c.set_static_mesh(new[label][1]);a.set_actor_transform(new[label][0],False,True)
    for i,m in enumerate(materials):c.set_material(i,m)
   u.SystemLibrary.execute_console_command(world,'csvprofile STARTFILE=S0ClosedLedge_'+name+'.csv');S.update(start=now,csv=False);return
  elapsed=now-S['start']
  if elapsed>15 and not S['csv']:u.SystemLibrary.execute_console_command(world,'csvprofile START');S['csv']=True
  if elapsed>35:
   u.SystemLibrary.execute_console_command(world,'csvprofile STOP');S.update(i=S['i']+1,start=None)
 except:
  (O/'error.txt').write_text(traceback.format_exc());u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
u.EditorPythonScripting.set_keep_python_script_alive(True);handle=u.register_slate_post_tick_callback(tick)
