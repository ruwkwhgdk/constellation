"""V20 fixed-view shadow group isolation. Transient changes only; never save map."""
import unreal as u,time,json,traceback,hashlib
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/ShadowV20_20261019'
O.mkdir(parents=True,exist_ok=True)
mapfile=R/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
assert not (O/'session.json').exists(),'Use a fresh run directory'
before=hashlib.sha256(mapfile.read_bytes()).hexdigest()
(O/'session.json').write_text(json.dumps(dict(map_sha256=before)))
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
A=u.get_editor_subsystem(u.EditorActorSubsystem);world=u.EditorLevelLibrary.get_editor_world()
groups={
 'directional_off':['DirectionalLight'],
 'ceiling_off':['ART_SchoolCave_CeilingKey'],
 'bounce_off':['S0_WetPolish_CaveBounce','S0_Art_WallGrazing','S0_VentWarmLight'],
 'window_off':['S0_Ref_WindowBlue_0','S0_Ref_WindowBlue_1','S0_Ref_WindowBlue_2','S0_Ref_CaveBlue'],
 'contact_off':['S0_Contact_Warm_00','S0_Contact_Warm_01']}
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
targets={label:actors[label].get_component_by_class(u.LightComponent) for labels in groups.values() for label in labels}
assert all(c and c.get_editor_property('cast_shadows') for c in targets.values())
(O/'groups.json').write_text(json.dumps(groups,indent=2))
cam=A.spawn_actor_from_class(u.CameraActor,u.Vector(2900,900,700),u.Rotator(pitch=-20,yaw=-138),transient=True)
cam.camera_component.set_field_of_view(83);u.EditorLevelLibrary.pilot_level_actor(cam);u.EditorLevelLibrary.editor_set_game_view(True)
u.get_editor_subsystem(u.LevelEditorSubsystem).editor_set_viewport_realtime(True)
for cmd in ['t.MaxFPS 0','r.VSync 0','r.SSR.Quality 3','r.GPUCsvStatsEnabled 1']:u.SystemLibrary.execute_console_command(world,cmd)
phases=['baseline']+list(groups)+['baseline_repeat']
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
   for label,c in targets.items():c.set_cast_shadows(label not in groups.get(name,[]))
   u.SystemLibrary.execute_console_command(world,'csvprofile STARTFILE=S0V20Shadow_'+name+'.csv')
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
