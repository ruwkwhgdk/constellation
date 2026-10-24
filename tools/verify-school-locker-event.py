import unreal as u,time,json,traceback
from pathlib import Path
P=Path(u.Paths.project_saved_dir())/'SchoolLockerIntegration';F=P/'frames';F.mkdir(parents=True,exist_ok=True)
assert 'SceneReleaseValidation' in u.Paths.project_saved_dir()
u.EditorPythonScripting.set_keep_python_script_alive(True)
E=u.get_editor_subsystem(u.UnrealEditorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
S={'start':time.monotonic(),'phase':'boot','case':0,'results':[],'samples':[],'captures':[]};orders=[['Slit','Inside'],['Inside','Slit'],['Slit','Inside']]
def vec(v):return [v.x,v.y,v.z]
def finish(ok,error=''):
 (P/'result.json').write_text(json.dumps({'success':ok,'error':error,'results':S['results'],'samples':S['samples'],'captures':S['captures']},indent=2),encoding='utf8')
 L.editor_request_end_play();S.update(phase='finish',finish=time.monotonic())
def tick(dt):
 try:
  if S['phase']=='finish':
   if time.monotonic()-S['finish']>3:u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
   return
  assert time.monotonic()-S['start']<600,'Timeout '+S['phase']
  if S['phase']=='restart':
   if not L.is_in_play_in_editor():L.editor_request_begin_play();S['phase']='boot'
   return
  w=E.get_game_world()
  if not w:return
  ev=next((e for e in u.ObjectIterator(u.SceneEventSubsystem) if e.get_outer()==w),None)
  if not ev:return
  r=ev.get_editor_property('active_player');pc=u.GameplayStatics.get_player_controller(w,0);pawn=u.GameplayStatics.get_player_character(w,0)
  if S['phase']=='boot':
   if not r:return
   stage=u.GameplayStatics.get_actor_of_class(w,u.SchoolOpeningSceneActor)
   S.update(phase='playing',stage=stage,selections=[],transitions={},previous='None',hold_start=None,hold_drift=0,last_sample=-1,last_capture=-1,game_start=u.GameplayStatics.get_time_seconds(w))
  t=u.GameplayStatics.get_time_seconds(w);stage=S['stage'];phase=str(stage.get_editor_property('locker_phase'));mesh=pawn.mesh
  if phase!=S['previous']:
   S['transitions'][phase]=t;S['previous']=phase;u.log('LOCKER_PHASE '+str(S['case'])+' '+phase+' '+str(t))
  if phase in ['Falling','ProneHold','Recovering','Settling','Ready','Complete']:
   assert pawn.get_actor_location().distance(u.Vector(3060,0,90.15))<200, ('Root motion outside expected 91cm range',str(pawn.get_actor_location()))
   assert pawn.get_actor_location().z>80, 'Player sank through floor'
   if t-S['last_sample']>.03:
    S['last_sample']=t;S['samples'].append({'case':S['case'],'time':t,'phase':phase,'pawn':vec(pawn.get_actor_location()),'camera':vec(pc.player_camera_manager.get_camera_location()),'sockets':{n:vec(mesh.get_socket_location(n)) for n in ['root','pelvis','head','hand_l','hand_r','foot_l','foot_r']},'locked':pc.is_move_input_ignored(),'hidden':pawn.get_editor_property('hidden')})
   if S['case']==0 and t-S['last_capture']>=.1:
    S['last_capture']=t;fn=F/('%05d.png'%len(S['captures']));u.CarryEditorLibrary.capture_carry_review(str(fn),False);S['captures'].append({'file':str(fn),'time':t,'phase':phase})
   if phase not in ['Complete']:assert pc.is_move_input_ignored() and pc.is_look_input_ignored(),'Premature control return'
   assert not pawn.get_editor_property('hidden'),'Animated player hidden'
  if phase=='ProneHold':
   now=mesh.get_socket_location('pelvis')
   if S['hold_start'] is None:S['hold_start']=now
   S['hold_drift']=max(S['hold_drift'],now.distance(S['hold_start']))
   assert S['hold_drift']<.2,('Prone pose drift',S['hold_drift'])
   if S['case']==2 and t-S['transitions']['ProneHold']>1:
    ev.cancel_active();assert not pc.is_move_input_ignored() and not pc.is_look_input_ignored();assert str(stage.get_editor_property('locker_phase'))=='Cancelled';assert not pawn.get_editor_property('hidden')
    assert pawn.character_movement.get_editor_property('movement_mode')==u.MovementMode.MOVE_WALKING
    S['results'].append({'case':'cancel_during_prone','success':True});finish(True);return
  if S['phase']=='move':
   elapsed=t-S['move_start']
   if elapsed<.7:
    assert u.CarryEditorLibrary.inject_carry_review_input('/Game/Constellation/Input/IA_Move',u.Vector(0,1,0));return
   distance=pawn.get_actor_location().distance(S['position_before_move']);assert distance>10,('Gameplay movement did not resume',distance)
   S['results'].append({'case':S['case'],'success':True,'transitions':S['transitions'],'hold_drift_cm':S['hold_drift'],'movement_cm':distance,'end_position':vec(pawn.get_actor_location())})
   S['case']+=1;L.editor_request_end_play();S['phase']='restart';return
  if r:
   if r.is_waiting_for_choice():
    assert not r.select_dialogue_choice('Force');key=orders[S['case']][len(S['selections'])];assert r.select_dialogue_choice(key);S['selections'].append(key)
   elif r.is_waiting_for_dialogue():r.advance_dialogue()
   return
  assert stage.get_editor_property('completed'),'Event aborted: '+phase
  assert phase=='Complete',phase
  assert stage.is_gameplay_input_available() and not pc.is_move_input_ignored() and not pc.is_look_input_ignored()
  # S0 now overlaps the girl's escape with the fall; the old >4s hold was redundant.
  assert S['transitions']['Recovering']>S['transitions']['ProneHold'],'Recovery started before prone hold'
  assert S['transitions']['Settling']-S['transitions']['Recovering']>5.7,'GetUp truncated'
  assert pawn.character_movement.get_editor_property('movement_mode')==u.MovementMode.MOVE_WALKING
  assert pc.get_view_target()==pawn,'Camera did not return to player'
  S.update(phase='move',move_start=t,position_before_move=pawn.get_actor_location())
 except Exception:finish(False,traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick);L.editor_request_begin_play()


