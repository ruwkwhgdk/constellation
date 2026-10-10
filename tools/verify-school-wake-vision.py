"""S0 actual-map PIE: both investigation orders, disabled selection, cancellation.
Must run with isolated -UserDir containing SceneReleaseValidation. Saves no assets.
"""
import unreal as u,time,json,traceback
from pathlib import Path
outdir=Path(u.Paths.project_saved_dir()).resolve();assert 'SceneReleaseValidation' in str(outdir)
outdir.mkdir(parents=True,exist_ok=True)
E=u.get_editor_subsystem(u.UnrealEditorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
VISUAL='S0Visual' in u.SystemLibrary.get_command_line()
CAPTURED=set()
def shot(w,name):
 if VISUAL and name not in CAPTURED:
  CAPTURED.add(name);path=Path(u.Paths.project_dir())/'Saved/S0Opening'/(name+'.png');u.SystemLibrary.execute_console_command(w,'Shot SHOWUI -nosuffix filename="'+str(path)+'"')
S={'start':time.monotonic(),'case':(2 if 'WakeCancelOnly' in u.SystemLibrary.get_command_line() else 0),'phase':'boot','results':[],'selections':[],'dialogues':[],'wait_start':0,'last_choice':''}
assert u.SceneDirectorLibrary.configure_school_tutorial_focus(E.get_editor_world(),False)==0,'Legacy tutorial focus overrides remain'
orders=[['Slit','Inside'],['Inside','Slit'],['cancel']]
def finish(ok,error=''):
 data={k:v for k,v in S.items() if k not in ('world','runner','stage','binding')};data.update(success=ok,error=error)
 (Path(u.Paths.project_dir())/('Saved/S0Opening/s0-wake-cancel-result.json' if 'WakeCancelOnly' in u.SystemLibrary.get_command_line() else 'Saved/S0Opening/s0-wake-pie-result.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8');u.log('S0_PIE_RESULT '+str(ok)+' '+error)
 u.unregister_slate_post_tick_callback(handle);L.editor_request_end_play();u.SystemLibrary.quit_editor()
def tick(dt):
 try:
  if time.monotonic()-S['start']>540:raise RuntimeError('S0 overall timeout '+S['phase'])
  if S['phase']=='cancel_capture':
   elapsed=time.monotonic()-S['cancel_capture']
   if elapsed>2.5:shot(S['world'],'S0_Wake_Cancel')
   if elapsed>4:finish(True)
   return
  if S['phase']=='restart':
   if not L.is_in_play_in_editor():L.editor_request_begin_play();S['phase']='boot'
   return
  w=E.get_game_world()
  if not w:return
  events=next((e for e in u.ObjectIterator(u.SceneEventSubsystem) if e.get_outer()==w),None)
  if not events:return
  if S['phase']=='boot':
   r=events.get_editor_property('active_player')
   if not r:return
   bindings=[b for b in u.GameplayStatics.get_all_actors_of_class(w,u.SceneEventBinding) if b.get_editor_property('director') and b.get_editor_property('director').get_name()=='DA_S0_Opening'];assert len(bindings)==1
   stage=u.GameplayStatics.get_actor_of_class(w,u.SchoolOpeningSceneActor);assert stage
   S.update(eye_samples=[],eye_crossings=0,eye_prev=0,eye_peak=0,eye_blur_max=0,world=w,runner=r,stage=stage,binding=bindings[0],flee_samples=0,vent_checked=False,turn_checked=False,flee_started=False,phase='playing',selections=[],dialogues=[],last_choice='',wait_start=0)
   u.log('S0_PIE_CASE '+str(S['case']));return
  r=S['runner'];pc=u.GameplayStatics.get_player_controller(w,0)
  if events.get_editor_property('active_player'):
   eye=r.get_eye_open();blur=r.get_vision_blur();haze=r.get_vision_haze()
   if not r.has_started_eye_effect():
    eye=0 # Bootstrap still owns the closed screen before the first eyelid cue.
    if S['case']==0:shot(w,'S0_Wake_Boot')
   S['eye_blur_max']=max(S['eye_blur_max'],blur)
   if len(S['eye_samples'])<600:S['eye_samples'].append([time.monotonic(),eye,blur,haze])
   if eye>S['eye_peak']:S['eye_peak']=eye
   if eye<.02 and S['eye_prev']>=.02 and S['eye_peak']>.1:S['eye_crossings']+=1;S['eye_peak']=0
   S['eye_prev']=eye
   if S['case']==0:
    if .20<eye<.4 and blur>.6:shot(w,'S0_Wake_FirstBlink')
    if .5<eye<.7 and .35<blur<.65:shot(w,'S0_Wake_SecondBlink')
    if eye>.99 and .01<blur<.1:shot(w,'S0_Wake_Recovery')
   if S['case']==2 and blur>.5 and eye>.15:
    assert r.has_vision_overlay();events.cancel_active()
    assert not events.get_editor_property('active_player'),'Cancel left an active director'
    # SceneEventSubsystem destroys the runner on stop; reflected calls on a destroyed actor return default outputs.
    alive=u.SystemLibrary.is_valid(r)
    if alive:assert not r.has_vision_overlay() and r.get_eye_open()==1 and r.get_vision_blur()==0 and r.get_vision_haze()==0,'Cancel left a vision effect'
    assert not S['stage'].get_editor_property('pending'),'Cancel left bootstrap ownership'
    assert not S['stage'].get_editor_property('completed'),'Cancel marked success'
    assert not pc.is_move_input_ignored() and not pc.is_look_input_ignored(),'Cancel left input locked'
    S['results'].append({'case':'cancel_during_wake','restored':True,'runner_destroyed':not alive,'samples':len(S['eye_samples'])});shot(w,'S0_Wake_CancelImmediate');S['phase']='cancel_capture';S['cancel_capture']=time.monotonic();return
   current=str(r.get_editor_property('current_dialogue'))
   assert not S['stage'].get_editor_property('region_title_class'),'Duplicate S0 title still enabled'
   girl=S['binding'].get_editor_property('objects')['Girl'];gp=girl.get_actor_location();gy=girl.get_actor_rotation().yaw
   if current=='좁은 틈 너머로 칠판이 보입니다.':
    cp=pc.player_camera_manager.get_camera_location()
    assert cp.distance(u.Vector(3165,0,214.6))<3,('Wrong vent camera',str(cp))
    S['vent_checked']=True
    if S['case']==0:shot(w,'S0_Feedback_Vent')
   if abs(gp.x-3010)<3 and -70<gy<70:S['turn_checked']=True
   if 700<gp.x<2600 and abs(gp.y)<60 and abs(gy-90)<3:
    S['flee_started']=True;S['flee_samples']+=1
    assert gp.z>60,'Flee path sinks into floor'
    if S['case']==0 and 1900<gp.x<2200:shot(w,'S0_Feedback_Flee')
   if S['flee_started'] and not girl.get_editor_property('hidden'):
    assert abs(gy-90)<3 and -55<=gp.y<=3,('Wrong flee facing/path',str(gp),gy)
   if current=='인간이다아!!':
    girl=S['binding'].get_editor_property('objects')['Girl'];assert not girl.get_editor_property('hidden'),'Girl hidden during reveal';assert girl.get_actor_location().z>50,'Girl below floor'
    if S['case']==0:shot(w,'S0_Play_Girl')
   if r.is_waiting_for_choice():
    assert S['eye_crossings']==2,('Blink count',S['eye_crossings'])
    assert S['eye_blur_max']>.7 and eye==1 and blur==0 and haze==0,'Vision failed to recover before choice'
    assert pc.is_move_input_ignored() and pc.is_look_input_ignored(),'Gameplay is unlocked during choice'
    assert not r.select_dialogue_choice('Force'),'Disabled Force accepted via API'
    choices=r.get_editor_property('current_choices');keys=[str(c.get_editor_property('key')) for c in choices if c.get_editor_property('enabled')]
    signature='|'.join(keys)
    if S['last_choice']!=signature:
     S['last_choice']=signature;S['wait_start']=time.monotonic()
     if S['case']==0:shot(w,'S0_Play_Choice')
     return
    if time.monotonic()-S['wait_start']<2:return
    if S['case']==2:
     events.cancel_active();assert not pc.is_move_input_ignored() and not pc.is_look_input_ignored(),'Cancel left input locked'
     assert not S['stage'].get_editor_property('pending') and not S['stage'].get_editor_property('completed'),'Cancel marked completion'
     assert '완료' not in str(S['binding'].get_editor_property('status')),'Cancel recorded success'
     S['results'].append({'case':'cancel','restored':True});finish(True);return
    expected=orders[S['case']][len(S['selections'])];assert expected in keys,(expected,keys)
    if len(S['selections'])==1:assert len(keys)==1 and S['selections'][0] not in keys
    assert r.select_dialogue_choice(expected);S['selections'].append(expected)
   elif r.is_waiting_for_dialogue():
    text=str(r.get_editor_property('current_dialogue'))
    if S['case']==0 and '사진에는' in text:shot(w,'S0_Play_Photo')
    if not S['dialogues'] or S['dialogues'][-1]!=text:S['dialogues'].append(text)
    r.advance_dialogue()
   return
  assert not r.has_vision_overlay() and r.get_vision_blur()==0,'Completion left overlay'
  assert S['selections']==orders[S['case']],S['selections']
  assert S['vent_checked'] and S['turn_checked'] and S['flee_samples']>5,('Feedback observations missing',S['vent_checked'],S['turn_checked'],S['flee_samples'])
  assert S['stage'].get_editor_property('completed'),'Stage not completed'
  assert not S['stage'].get_editor_property('pending'),'Opening remains pending'
  assert not pc.is_move_input_ignored() and not pc.is_look_input_ignored(),'Input not restored'
  assert S['stage'].is_gameplay_input_available(),'Viewport still blocks gameplay input'
  if VISUAL and S['case']==0 and 'S0_Play_Return' not in CAPTURED:shot(w,'S0_Play_Return');S['return_capture']=time.monotonic();return
  if VISUAL and S['case']==0 and time.monotonic()-S.get('return_capture',0)<1.5:return
  pawn=u.GameplayStatics.get_player_pawn(w,0);assert not pawn.get_editor_property('hidden'),'Player remains hidden'
  assert pawn.get_actor_location().distance(u.Vector(2780,0,100))<130,'Unexpected player handoff position'
  girl=S['binding'].get_editor_property('objects')['Girl'];assert girl.get_editor_property('hidden'),'Girl reappeared after exit'
  assert any('전혀 떠오르지' in t for t in S['dialogues']),'Photo dialogue missing'
  S['results'].append({'case':orders[S['case']],'vent_checked':S['vent_checked'],'turn_checked':S['turn_checked'],'flee_samples':S['flee_samples'],'blink_cycles':S['eye_crossings'],'blur_max':S['eye_blur_max'],'dialogues':S['dialogues'],'position':str(pawn.get_actor_location()),'status':str(S['binding'].get_editor_property('status'))})
  S['case']+=1;L.editor_request_end_play();S['phase']='restart'
 except Exception:finish(False,traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick)
L.editor_request_begin_play()
