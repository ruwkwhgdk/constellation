"""Transient PIE dialogue smoke test. No maps, scene assets or progression are saved."""
import unreal as u
import time,json,traceback
from pathlib import Path
assert 'DialogueRestyle/PIE' in Path(u.Paths.project_saved_dir()).as_posix(), 'Use the isolated DialogueRestyle/PIE UserDir; never run in the working editor'
out=Path(u.Paths.project_saved_dir())/'DialogueRestyle';out.mkdir(parents=True,exist_ok=True)
level=u.get_editor_subsystem(u.LevelEditorSubsystem);editor=u.get_editor_subsystem(u.UnrealEditorSubsystem)
state={'phase':0,'start':time.monotonic()}
def finish(ok,error=''):
 (out/'pie-result.json').write_text(json.dumps({'success':ok,'error':error},ensure_ascii=False),encoding='utf8')
 u.log('DIALOGUE_PIE_RESULT '+str(ok)+' '+error);u.unregister_slate_post_tick_callback(handle);level.editor_request_end_play();u.SystemLibrary.quit_editor()
def tick(dt):
 try:
  if time.monotonic()-state['start']>90:raise RuntimeError('PIE dialogue timeout')
  w=editor.get_game_world()
  if not w:return
  if state['phase']==0:
   r=next(iter(u.GameplayStatics.get_all_actors_of_class(w,u.SceneDirectorPlayer)),None);assert r and r.play_director()
   state.update(phase=1,runner=r,at=time.monotonic());return
  r=state['runner']
  if state['phase']==1 and time.monotonic()-state['at']>2:
   assert r.is_waiting_for_dialogue();assert not str(r.get_editor_property('current_dialogue'))==''
   u.SystemLibrary.execute_console_command(w,'Shot showui nosuffix filename='+(out/'dialogue-game.png').as_posix())
   state.update(phase=2,at=time.monotonic());return
  if state['phase']==2 and time.monotonic()-state['at']>1:
   r.advance_dialogue();state.update(phase=3,at=time.monotonic());return
  if state['phase']==3 and time.monotonic()-state['at']>1:
   assert not r.is_waiting_for_dialogue();finish(True)
 except Exception:finish(False,traceback.format_exc())
a=u.new_object(u.SceneDirectorAsset);steps=[u.SceneDirectorLibrary.make_director_step(t) for t in [u.DirectorNodeType.START,u.DirectorNodeType.CINEMATIC_MODE,u.DirectorNodeType.DIALOGUE,u.DirectorNodeType.GAMEPLAY_RETURN,u.DirectorNodeType.END]]
for i in range(4):steps[i].set_editor_property('next_nodes',[steps[i+1].get_editor_property('id')])
steps[2].set_editor_property('speaker_name',u.Text('이름'));steps[2].set_editor_property('dialogue_text',u.Text('세상에서 살아남기 위해선,\n그 세상에 맞는 모습으로 자신을 변화시킬 필요가 있다.'));steps[2].set_editor_property('dialogue_advance',u.DirectorDialogueAdvance.CLICK);steps[2].set_editor_property('duration',0.1)
a.set_editor_property('steps',steps);assert u.SceneDirectorLibrary.compile_director(a) is not None
actor=u.get_editor_subsystem(u.EditorActorSubsystem).spawn_actor_from_class(u.SceneDirectorPlayer,u.Vector(0,0,0))
actor.set_editor_property('auto_play',False);actor.set_editor_property('director',a)
state['asset']=a
handle=u.register_slate_post_tick_callback(tick)
level.editor_request_begin_play()

