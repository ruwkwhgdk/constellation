import unreal as u,time,json,traceback
from pathlib import Path
O=Path(u.Paths.project_dir())/'Saved/S0ExitRevision';E=u.get_editor_subsystem(u.UnrealEditorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert 'SceneReleaseValidation' in u.Paths.project_saved_dir()
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
u.EditorPythonScripting.set_keep_python_script_alive(True)
S={'start':time.monotonic(),'samples':[],'selections':[],'transitions':{},'last_phase':'','done':False}
def finish(ok,error=''):
 S['done']=True
 (O/'pie.json').write_text(json.dumps(dict(success=ok,error=error,samples=S['samples'],transitions=S['transitions']),indent=2))
 L.editor_request_end_play();u.unregister_slate_post_tick_callback(handle);u.log('S0_EXIT_VERIFIED '+str(ok)+' '+error)
def tick(dt):
 try:
  assert time.monotonic()-S['start']<240,'timeout'
  w=E.get_game_world()
  if not w:return
  stage=u.GameplayStatics.get_actor_of_class(w,u.SchoolOpeningSceneActor)
  if not stage:return
  ev=next((e for e in u.ObjectIterator(u.SceneEventSubsystem) if e.get_outer()==w),None)
  if not ev:return
  r=ev.get_editor_property('active_player');phase=str(stage.get_editor_property('locker_phase'));t=u.GameplayStatics.get_time_seconds(w)
  if phase!=S['last_phase']:S['transitions'][phase]=t;S['last_phase']=phase
  if r:
   if r.is_waiting_for_choice():
    key=['Slit','Inside'][len(S['selections'])];assert r.select_dialogue_choice(key);S['selections'].append(key)
   elif r.is_waiting_for_dialogue():r.advance_dialogue()
  girl=stage.get_editor_property('girl')
  if girl and phase in ['Falling','ProneHold']:
   p=girl.get_actor_location();hidden=girl.get_editor_property('hidden');S['samples'].append(dict(t=t,phase=phase,x=p.x,y=p.y,hidden=hidden))
   assert abs(p.y)<.2,('Not straight',str(p))
  if phase=='Complete':
   for name in ['Falling','ProneHold']:
    xs=[s['x'] for s in S['samples'] if s['phase']==name and not s['hidden']];assert len(xs)>2 and max(xs)-min(xs)>100,('Girl did not move during '+name,xs[:5])
   assert S['transitions']['Recovering']>S['transitions']['ProneHold']
   assert S['transitions']['Settling']-S['transitions']['Recovering']>5.7,'Get-up truncated'
   pc=u.GameplayStatics.get_player_controller(w,0);assert stage.is_gameplay_input_available() and not pc.is_move_input_ignored() and not pc.is_look_input_ignored()
   assert pc.get_view_target()==u.GameplayStatics.get_player_pawn(w,0)
   finish(True)
 except Exception:finish(False,traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick);L.editor_request_begin_play()
