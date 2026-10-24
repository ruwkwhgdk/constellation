import unreal as u,time,json,traceback
from pathlib import Path
O=Path(u.Paths.project_dir())/'Saved/S0NotionDialogue';E=u.get_editor_subsystem(u.UnrealEditorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert 'SceneReleaseValidation' in u.Paths.project_saved_dir()
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
intro=['눈을 뜨자, 낯선 풍경이 보입니다.','아마도…당신은 굉장히 좁은 곳 안에 갇혀 있는 것 같습니다.']
slit=['고개를 들어서 좁은 틈 너머로 바깥을 살펴봅니다.','칠판과 책상, 그리고 의자들이 보입니다.','버려진 지 오랜 시간이 지난 교실인 것 같습니다.']
inside=['포스트잇, 스티커, 별자리 사진, 키링…','그다지 특별한 건 보이지 않습니다.','우측 벽 한 쪽에 사진이 하나 걸려 있는 것을 발견합니다.','사진에는 당신이 찍혀 있습니다.','옆에 서 있는 건…누구일까요?','잠시 기억을 되짚어보지만, 그녀에 대한 것은 전혀 떠오르지 않습니다.']
approach=['처음 보는 소녀가 당신이 갇혀 있는 곳 앞으로 달려옵니다.'];narration=set(intro+slit+inside+approach)
orders=[['Slit','Inside'],['Inside','Slit']];S=dict(start=time.monotonic(),case=0,phase='play',seen=[],last='',choices=[],results=[],started=False)
u.EditorPythonScripting.set_keep_python_script_alive(True)
def finish(ok,error=''):
 (O/'pie.json').write_text(json.dumps(dict(success=ok,error=error,results=S['results'],current_seen=S['seen']),ensure_ascii=False,indent=2),encoding='utf8')
 L.editor_request_end_play();u.unregister_slate_post_tick_callback(handle);u.log('S0_NOTION_VERIFIED '+str(ok)+' '+error)
def tick(dt):
 try:
  assert time.monotonic()-S['start']<420,'Timeout'
  if S['phase']=='restart':
   if not L.is_in_play_in_editor():S.update(phase='play',seen=[],last='',choices=[],started=False);L.editor_request_begin_play()
   return
  w=E.get_game_world()
  if not w:return
  ev=next((e for e in u.ObjectIterator(u.SceneEventSubsystem) if e.get_outer()==w),None)
  if not ev:return
  r=ev.get_editor_property('active_player')
  if r:
   S['started']=True;text=str(r.get_editor_property('current_dialogue'))
   if text!=S['last']:
    if text in narration:S['seen'].append(text)
    S['last']=text
   if r.is_waiting_for_choice():
    assert S['seen'][:2]==intro,'Intro missing before choices'
    assert not r.select_dialogue_choice('Force')
    key=orders[S['case']][len(S['choices'])];assert r.select_dialogue_choice(key);S['choices'].append(key)
   elif r.is_waiting_for_dialogue():r.advance_dialogue()
   return
  if not S['started']:return
  stage=u.GameplayStatics.get_actor_of_class(w,u.SchoolOpeningSceneActor);assert stage.get_editor_property('completed')
  expected=intro+(slit+inside if S['case']==0 else inside+slit)+approach
  assert S['seen']==expected,('Dialogue order/content mismatch',S['seen'],expected)
  pc=u.GameplayStatics.get_player_controller(w,0);assert not pc.is_move_input_ignored() and not pc.is_look_input_ignored()
  S['results'].append(dict(order=orders[S['case']],narration=S['seen'],success=True));u.log('S0_NOTION_CASE_PASSED '+str(S['case']))
  S['case']+=1
  if S['case']==2:finish(True)
  else:L.editor_request_end_play();S['phase']='restart'
 except Exception:finish(False,traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick);L.editor_request_begin_play()
