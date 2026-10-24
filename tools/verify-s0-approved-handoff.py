"""Final reverse-order and cancellation checks for the approved S0 camera handoff."""
import unreal as u,time,json,traceback
from pathlib import Path
P=lambda o,k:o.get_editor_property(k)
O=Path(u.Paths.project_dir())/'Saved/S0FallCameraReview';E=u.get_editor_subsystem(u.UnrealEditorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert 'SceneReleaseValidation' in u.Paths.project_saved_dir()
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
S=dict(start=time.monotonic(),case=0,restart=False,started=False,choices=0,fall_at=None,results=[])
u.EditorPythonScripting.set_keep_python_script_alive(True)
def finish(ok,error=''):
 (O/'approved-handoff.json').write_text(json.dumps(dict(success=ok,error=error,results=S['results']),ensure_ascii=False,indent=2),encoding='utf8');u.log('S0_APPROVED_HANDOFF '+str(ok)+' '+error);L.editor_request_end_play();u.unregister_slate_post_tick_callback(handle)
def tick(dt):
 try:
  assert time.monotonic()-S['start']<360,'Timeout'
  if S['restart']:
   if not L.is_in_play_in_editor():S.update(restart=False,started=False,choices=0,fall_at=None);L.editor_request_begin_play()
   return
  w=E.get_game_world()
  if not w:return
  ev=next((e for e in u.ObjectIterator(u.SceneEventSubsystem) if e.get_outer()==w),None)
  if not ev:return
  r=P(ev,'active_player');pc=u.GameplayStatics.get_player_controller(w,0);pawn=u.GameplayStatics.get_player_character(w,0);stage=u.GameplayStatics.get_actor_of_class(w,u.SchoolOpeningSceneActor)
  if not stage or not pawn:return
  t=u.GameplayStatics.get_time_seconds(w);phase=str(P(stage,'locker_phase'))
  if phase=='Falling' and S['fall_at'] is None:S['fall_at']=t
  if S['case']==1 and r and S['fall_at'] is not None and t-S['fall_at']>3.5:
   assert phase=='ProneHold',phase
   assert pc.is_move_input_ignored() and pc.is_look_input_ignored()
   ev.cancel_active()
   assert str(P(stage,'locker_phase'))=='Cancelled'
   assert not pc.is_move_input_ignored() and not pc.is_look_input_ignored()
   assert pc.get_view_target()==pawn and not P(pawn,'hidden')
   assert P(pawn.character_movement,'movement_mode')==u.MovementMode.MOVE_WALKING
   S['results'].append(dict(case='cancel_during_camera_blend',success=True));finish(True);return
  if r:
   S['started']=True
   if r.is_waiting_for_choice():assert not r.select_dialogue_choice('Force');assert r.select_dialogue_choice(['Inside','Slit'][S['choices']]);S['choices']+=1
   elif r.is_waiting_for_dialogue():r.advance_dialogue()
   return
  if not S['started']:return
  assert P(stage,'completed') and phase=='Complete'
  assert not pc.is_move_input_ignored() and not pc.is_look_input_ignored() and stage.is_gameplay_input_available()
  assert pc.get_view_target()==pawn and not P(pawn,'hidden')
  assert P(pawn.character_movement,'movement_mode')==u.MovementMode.MOVE_WALKING
  S['results'].append(dict(case='Inside_then_Slit',success=True));u.log('S0_APPROVED_REVERSE_ORDER_PASSED');S.update(case=1,restart=True);L.editor_request_end_play()
 except Exception:finish(False,traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick);L.editor_request_begin_play()
