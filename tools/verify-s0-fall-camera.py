import unreal as u,time,json,traceback
from pathlib import Path
P=lambda o,k:o.get_editor_property(k)
O=Path(u.Paths.project_dir())/'Saved/S0FallCameraReview';E=u.get_editor_subsystem(u.UnrealEditorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert 'SceneReleaseValidation' in u.Paths.project_saved_dir()
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
u.EditorPythonScripting.set_keep_python_script_alive(True)
S=dict(start=time.monotonic(),choices=0,started=False,fall_at=None,transitions={},last_phase='',samples=[],shots=[],last_sample=-1,finished_at=None)
def v(x):return [x.x,x.y,x.z]
def shot(w,n):
 if n not in S['shots']:
  S['shots'].append(n);u.SystemLibrary.execute_console_command(w,'Shot -nosuffix filename="'+str(O/(n+'.png'))+'"')
def finish(ok,error=''):
 (O/'verified.json').write_text(json.dumps(dict(success=ok,error=error,state=S),ensure_ascii=False,indent=2),encoding='utf8');u.log('S0_FALL_CAMERA_VERIFIED '+str(ok)+' '+error);L.editor_request_end_play();u.unregister_slate_post_tick_callback(handle)
def tick(dt):
 try:
  assert time.monotonic()-S['start']<240,'Timeout'
  w=E.get_game_world()
  if not w:return
  ev=next((e for e in u.ObjectIterator(u.SceneEventSubsystem) if e.get_outer()==w),None)
  if not ev:return
  r=P(ev,'active_player');stage=u.GameplayStatics.get_actor_of_class(w,u.SchoolOpeningSceneActor)
  if not stage:return
  pc=u.GameplayStatics.get_player_controller(w,0);pawn=u.GameplayStatics.get_player_character(w,0);cm=pc.player_camera_manager;t=u.GameplayStatics.get_time_seconds(w)
  phase=str(P(stage,'locker_phase'))
  if phase!=S['last_phase']:S['last_phase']=phase;S['transitions'][phase]=t
  if phase=='Falling' and S['fall_at'] is None:S['fall_at']=t
  if S['fall_at'] is not None:
   elapsed=t-S['fall_at'];pos=cm.get_camera_location();rot=cm.get_camera_rotation()
   if t-S['last_sample']>.025:
    S['last_sample']=t;S['samples'].append(dict(t=elapsed,phase=phase,pos=v(pos),rot=[rot.roll,rot.pitch,rot.yaw],head=v(pawn.mesh.get_socket_location('head')),pawn=v(pawn.get_actor_location()),view=pc.get_view_target().get_name(),locked=pc.is_move_input_ignored()))
   if elapsed<2.1:
    assert abs(pos.y)<2,('Lateral camera during first-person fall',v(pos))
    assert abs(u.MathLibrary.normalized_delta_rotator(rot,u.Rotator(yaw=180)).yaw)<2,rot
   if .35<elapsed<.6:shot(w,'01-first-person-fall')
   if 2.05<elapsed<2.2:shot(w,'02-first-person-ground')
   if 3.8<elapsed<4:shot(w,'03-blending-to-gameplay')
   if phase=='Recovering' and t-S['transitions']['Recovering']>2:shot(w,'04-third-person-getup')
  if r:
   S['started']=True
   if r.is_waiting_for_choice():assert r.select_dialogue_choice(['Slit','Inside'][S['choices']]);S['choices']+=1
   elif r.is_waiting_for_dialogue():r.advance_dialogue()
   return
  if not S['started']:return
  assert P(stage,'completed') and phase=='Complete'
  assert not pc.is_move_input_ignored() and not pc.is_look_input_ignored()
  assert pc.get_view_target()==pawn
  assert S['transitions']['ProneHold']-S['fall_at']<=2.2,'Blend began before fall completed'
  assert S['transitions']['Settling']-S['transitions']['Recovering']>5.7
  shot(w,'05-gameplay-camera')
  if S['finished_at'] is None:S['finished_at']=t
  if t-S['finished_at']>1:
   assert all((O/(n+'.png')).exists() for n in ['01-first-person-fall','02-first-person-ground','03-blending-to-gameplay','04-third-person-getup','05-gameplay-camera'])
   finish(True)
 except Exception:finish(False,traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick);L.editor_request_begin_play()

