"""Real-map playback; no screenshot calls in the continuity trace."""
import unreal as u,time,json,traceback
from pathlib import Path
P=lambda o,k:o.get_editor_property(k)
O=Path(u.Paths.project_dir())/'Saved/S0Feedback1015/VideoV2';O.mkdir(exist_ok=True)
frames=[]
CAPTURE=False
FAST='S0PolishFastReview' in u.SystemLibrary.get_command_line()
shots=set()
E=u.get_editor_subsystem(u.UnrealEditorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert 'SceneReleaseValidation' in u.Paths.project_saved_dir()
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
import runpy
revision=runpy.run_path(str(Path(u.Paths.project_dir())/'tools/revise-s0-feedback1015.py'))
revision['revise'](u.load_asset('/Game/SceneDirector/School/DA_S0_Opening'),camera_draft=True)
S=dict(start=time.monotonic(),started=False,choices=0,samples=[],dialogues=[],phases={},finished=None,lasttext='',text_at=0,fall=None,ui=[])
u.EditorPythonScripting.set_keep_python_script_alive(True)
def v(x):return [x.x,x.y,x.z]
def shot(w,name):
 if not CAPTURE or name in shots:return
 shots.add(name);u.SystemLibrary.execute_console_command(w,'Shot '+('SHOWUI ' if name.startswith(('07','08','09')) else '')+'-nosuffix filename="'+str(O/(name+'.png'))+'"')
def finish(ok,error=''):
 (O/'frames.json').write_text(json.dumps(frames),encoding='utf8')
 (O/('visual-runtime.json' if CAPTURE else 'runtime.json')).write_text(json.dumps(dict(success=ok,error=error,state=S),ensure_ascii=False,indent=2),encoding='utf8')
 u.log('S0_POLISH_RUNTIME '+str(ok)+' '+error);L.editor_request_end_play();u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
def tick(dt):
 try:
  assert time.monotonic()-S['start']<900,'Timeout'
  w=E.get_game_world()
  if not w:return
  ev=next((e for e in u.ObjectIterator(u.SceneEventSubsystem) if e.get_outer()==w),None)
  if not ev:return
  r=P(ev,'active_player');stage=u.GameplayStatics.get_actor_of_class(w,u.SchoolOpeningSceneActor)
  if not stage:return
  pc=u.GameplayStatics.get_player_controller(w,0);pawn=u.GameplayStatics.get_player_character(w,0);cm=pc.player_camera_manager;t=u.GameplayStatics.get_time_seconds(w)
  phase=str(P(stage,'locker_phase'));S['phases'].setdefault(phase,t)
  if FAST:u.GameplayStatics.set_global_time_dilation(w,1. if phase!='None' or frames else 3.)
  if phase=='Falling' and S['fall'] is None:S['fall']=t
  if frames or (r and '인간이다' in str(P(r,'current_dialogue'))):
   u.GameplayStatics.set_global_time_dilation(w,1.)
   u.SystemLibrary.execute_console_command(w,'Shot -nosuffix filename="'+str(O/('frame-%05d.png'%len(frames)))+'"')
   frames.append(t)
  if S['fall'] is not None:
   cp=cm.get_camera_location();cr=cm.get_camera_rotation();target=pc.get_view_target()
   S['samples'].append(dict(t=t,dt=dt,phase=phase,pos=v(cp),rot=[cr.roll,cr.pitch,cr.yaw],target=target.get_name(),actor=v(target.get_actor_location()),pawn=v(pawn.get_actor_location()),hand=v(pawn.mesh.get_socket_location('hand_r')),shoulder=v(pawn.mesh.get_socket_location('upperarm_r')),head=v(pawn.mesh.get_socket_location('head')),mesh=str(pawn.mesh.get_socket_transform('root')),hidden=P(pawn,'hidden'),montage=str(P(stage,'locker_montage'))))
   S['samples'][-1].update(fov=cm.get_fov_angle(),bounds=str(u.SystemLibrary.get_component_bounds(pawn.mesh)),mesh_flags={k:str(P(pawn.mesh,k)) for k in ['visible','hidden_in_game','owner_no_see','only_owner_see','bounds_scale']})
   if 'S0ProbeArms' in u.SystemLibrary.get_command_line() and t-S['fall']>1.2:finish(True);return
   if .15<t-S['fall']<.3:shot(w,'01-fall-arms')
   if .55<t-S['fall']<.7:shot(w,'01b-fall-arms')
   if .85<t-S['fall']<1:shot(w,'01c-fall-arms')
   if 2.5<t-S['fall']<3:shot(w,'02-ground-hold')
   if 6.5<t-S['fall']<6.9:shot(w,'03-rear-overhead-draft')
   if phase=='Recovering' and t-S['phases'][phase]>2:shot(w,'03b-getup-blend-draft')
   if phase=='Recovering' and t-S['phases'][phase]>4:shot(w,'03c-standing-blend-draft')
  if r:
   yaw=cm.get_camera_rotation().yaw
   if abs(yaw-120)<1:shot(w,'00-left-wall-draft')
   if abs(yaw+120)<1:shot(w,'00-right-wall-draft')
   S['started']=True;text=str(P(r,'current_dialogue'))
   if text in ('......','이, 이, 이...','인간이다아!!'):
    assert abs(P(stage,'girl').get_actor_rotation().yaw)<1,'Girl rotated away during locker dialogue'
   if text!=S['lasttext']:
    S['lasttext']=text;S['text_at']=t;girl=P(stage,'girl')
    S['dialogues'].append(dict(t=t,text=text,girl=v(girl.get_actor_location()),yaw=girl.get_actor_rotation().yaw,camera=v(cm.get_camera_location())))
   if t-S['text_at']>.4:
    if text in ('어?','어...?'):shot(w,'04-girl-facing')
    if '이, 이' in text:shot(w,'05-girl-look-up')
    if '인간이다' in text:shot(w,'06-scream-zoom')
    if r.is_waiting_for_choice():shot(w,'07-choice-prompt')
   if r.is_waiting_for_choice() and 'S0ChoiceProbe' in u.SystemLibrary.get_command_line():
    for delay,name in [(.7,'choice-early'),(1.1,'choice-settled'),(1.5,'choice-held')]:
     if t-S['text_at']>delay:shot(w,'07-'+name)
    if t-S['text_at']>2.:finish(True);return
   if r.is_waiting_for_choice() and t-S['text_at']>2.2:
    assert text=='무엇을 할까요?',text
    assert r.select_dialogue_choice(['Slit','Inside'][S['choices']]);S['choices']+=1
   elif r.is_waiting_for_dialogue() and t-S['text_at']>max(.5,len(text)*.1):r.advance_dialogue()
   return
  if not S['started']:return
  if S['finished'] is None:
   S['finished']=t
   assert P(stage,'completed') and phase=='Complete'
   assert not pc.is_move_input_ignored() and not pc.is_look_input_ignored()
   assert pc.get_view_target()==pawn
   assert abs(P(pawn.mesh,'bounds_scale')-1.)<.001,'Locker bounds override not restored'
  if t-S['finished']>1:shot(w,'08-region-title')
  if t-S['finished']>5:shot(w,'09-movement-toast')
  widgets=[x.get_class().get_name() for x in u.WidgetLibrary.get_all_widgets_of_class(w,u.UserWidget,False) if x.is_in_viewport()]
  S['ui'].append(dict(t=t,widgets=widgets,titles=[str(x.get_region_subtitle_text()) for x in u.WidgetLibrary.get_all_widgets_of_class(w,u.RegionTitleWidget,False) if x.is_in_viewport()]))
  if t-S['finished']>2.:finish(True);return
  if t-S['finished']>12.:
   assert any(any('RegionTitle' in n for n in x['widgets']) for x in S['ui']),'No region title'
   assert any(any('Tutorial' in n for n in x['widgets']) for x in S['ui']),'No tutorial'
   assert not any('지하 동굴' in title for x in S['ui'] for title in x['titles']),'Duplicate cave title'
   assert S['phases']['Settling']-S['phases']['Recovering']>5.7
   finish(True)
 except Exception:finish(False,traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick);L.editor_request_begin_play()
