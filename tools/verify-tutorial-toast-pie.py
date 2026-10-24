"""Isolated transient PIE toast validation; no gameplay/map data is saved."""
import unreal as u
import time,json,traceback
from pathlib import Path
root=Path(u.Paths.project_dir());out=root/'Saved/TutorialToast';out.mkdir(parents=True,exist_ok=True)
assert 'TutorialToast/PIE' in Path(u.Paths.project_saved_dir()).as_posix()
level=u.get_editor_subsystem(u.LevelEditorSubsystem);editor=u.get_editor_subsystem(u.UnrealEditorSubsystem)
state={'phase':0,'start':time.monotonic()}
def finish(ok,error=''):
 (out/'pie-result.json').write_text(json.dumps({'success':ok,'error':error},ensure_ascii=False,indent=2),encoding='utf8')
 u.log('TOAST_PIE_RESULT '+str(ok)+' '+error);u.unregister_slate_post_tick_callback(handle);level.editor_request_end_play();u.SystemLibrary.quit_editor()
def tick(dt):
 try:
  if time.monotonic()-state['start']>75:raise RuntimeError('Toast PIE timeout')
  w=editor.get_game_world()
  if not w:return
  now=time.monotonic()
  if state['phase']==0:
   pc=u.GameplayStatics.get_player_controller(w,0);assert pc
   state['cursor']=pc.get_editor_property('show_mouse_cursor');state['pc']=pc
   state['widgets']=[u.TutorialToastEditorLibrary.create_toast_review(w,i,6) for i in range(4)]
   assert all(state['widgets']);state.update(phase=1,at=now);return
  widgets=state['widgets']
  assert not u.GameplayStatics.is_game_paused(w)
  assert state['pc'].get_editor_property('show_mouse_cursor')==state['cursor']
  if state['phase']==1 and now-state['at']>1:
   assert all(x.is_in_viewport() and x.get_render_opacity()>.95 for x in widgets)
   u.SystemLibrary.execute_console_command(w,'Shot showui nosuffix filename='+(out/'toast-stack.png').as_posix())
   state.update(phase=2,at=now);return
  if state['phase']==2 and now-state['at']>1:
   widgets[1].notify_tutorial_action_completed(u.TutorialPromptAction.JUMP)
   state.update(phase=3,at=now);return
  if state['phase']==3 and now-state['at']>.65:
   assert not widgets[1].is_in_viewport()
   assert all(widgets[i].is_in_viewport() for i in [0,2,3])
   state.update(phase=4,at=now);return
  if state['phase']==4 and not any(x.is_in_viewport() for x in widgets):finish(True)
 except Exception:finish(False,traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick)
level.editor_request_begin_play()
