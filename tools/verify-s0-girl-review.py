import unreal as u,time,json,traceback
from pathlib import Path
P=lambda o,k:o.get_editor_property(k)
O=Path(u.Paths.project_dir())/'Saved/S0GirlReview';E=u.get_editor_subsystem(u.UnrealEditorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert 'SceneReleaseValidation' in u.Paths.project_saved_dir()
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
S=dict(start=time.monotonic(),song_at=None,visible_at=None,uh_at=None,shots=[],samples=[],choices=0,started=False)
u.EditorPythonScripting.set_keep_python_script_alive(True)
def shot(w,name):
 if name in S['shots']:return
 S['shots'].append(name);u.SystemLibrary.execute_console_command(w,'Shot -nosuffix filename="'+str(O/(name+'.png'))+'"')
def finish(ok,error=''):
 (O/'verified.json').write_text(json.dumps(dict(success=ok,error=error,state=S),ensure_ascii=False,indent=2),encoding='utf8');u.log('S0_GIRL_REVIEW_VERIFIED '+str(ok)+' '+error);L.editor_request_end_play();u.unregister_slate_post_tick_callback(handle)
def tick(dt):
 try:
  assert time.monotonic()-S['start']<240
  w=E.get_game_world()
  if not w:return
  ev=next((e for e in u.ObjectIterator(u.SceneEventSubsystem) if e.get_outer()==w),None)
  if not ev:return
  r=P(ev,'active_player')
  if not r:
   if S['started']:
    assert S['visible_at'] is not None and 2<=S['visible_at']<=3,S['visible_at']
    assert S['uh_at'] is not None and all((O/(n+'.png')).exists() for n in ['01-song-offscreen','02-first-appearance','03-walking','04-look-at-locker'])
    pc=u.GameplayStatics.get_player_controller(w,0);assert not pc.is_move_input_ignored()
    finish(True)
   return
  S['started']=True;stage=u.GameplayStatics.get_actor_of_class(w,u.SchoolOpeningSceneActor)
  girl=P(stage,'girl');now=u.GameplayStatics.get_time_seconds(w)
  song=next((c for c in u.ObjectIterator(u.AudioComponent) if P(c,'sound')==P(stage,'girl_song') and c.is_playing()),None)
  if song and S['song_at'] is None:S['song_at']=now
  text=str(P(r,'current_dialogue'));pos=girl.get_actor_location();rot=girl.get_actor_rotation();hidden=P(girl,'hidden')
  if S['song_at'] is None:
   if now>2:assert hidden,'Girl visible before song'
  else:
   elapsed=now-S['song_at']
   if not hidden and S['visible_at'] is None:S['visible_at']=elapsed
   if 1<elapsed<2:shot(w,'01-song-offscreen')
   if S['visible_at'] is not None and elapsed>S['visible_at']+.3:shot(w,'02-first-appearance')
   if 8<elapsed<10:shot(w,'03-walking')
   if elapsed<14:S['samples'].append(dict(t=round(elapsed,3),pos=[pos.x,pos.y,pos.z],yaw=rot.yaw,hidden=hidden))
  if text in ('어?','어...?'):
   if S['uh_at'] is None:S['uh_at']=now
   if now-S['uh_at']>.71:
    assert pos.distance(u.Vector(2770,0,67))<2
    assert abs(u.MathLibrary.normalized_delta_rotator(rot,u.Rotator(yaw=0)).yaw)<3,rot
    shot(w,'04-look-at-locker')
  if r.is_waiting_for_choice():
   assert r.select_dialogue_choice(['Slit','Inside'][S['choices']]);S['choices']+=1
  elif r.is_waiting_for_dialogue():r.advance_dialogue()
 except Exception:finish(False,traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick);L.editor_request_begin_play()
