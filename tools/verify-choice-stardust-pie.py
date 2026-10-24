"""Transient PIE dialogue smoke test. No maps, scene assets or progression are saved."""
import unreal as u
import time,json,traceback
from pathlib import Path
assert 'ChoiceRestyle/PIE' in Path(u.Paths.project_saved_dir()).as_posix(), 'Use the isolated ChoiceRestyle/PIE UserDir; never run in the working editor'
out=Path(u.Paths.project_saved_dir())/'ChoiceRestyle';out.mkdir(parents=True,exist_ok=True)
level=u.get_editor_subsystem(u.LevelEditorSubsystem);editor=u.get_editor_subsystem(u.UnrealEditorSubsystem)
state={'phase':0,'start':time.monotonic()}
def finish(ok,error=''):
 (out/'pie-result.json').write_text(json.dumps({'success':ok,'error':error},ensure_ascii=False),encoding='utf8')
 u.log('CHOICE_PIE_RESULT '+str(ok)+' '+error);u.unregister_slate_post_tick_callback(handle);level.editor_request_end_play();u.SystemLibrary.quit_editor()
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
   assert r.is_waiting_for_choice();assert not str(r.get_editor_property('current_dialogue'))==''
   u.SystemLibrary.execute_console_command(w,'Shot showui nosuffix filename='+(out/'choice-game.png').as_posix())
   state.update(phase=2,at=time.monotonic());return
  if state['phase']==2 and time.monotonic()-state['at']>1:
   assert r.select_dialogue_choice('Together');state.update(phase=3,at=time.monotonic());return
  if state['phase']==3 and time.monotonic()-state['at']>1:
   assert not r.is_waiting_for_dialogue()
   cls=u.load_class(None,'/Game/Constellation/UI/Widgets/WBP_Choice.WBP_Choice_C')
   widget=u.DialogueStyleEditorLibrary.create_choice_review(w);assert widget
   widget.add_to_viewport(100);state['legacy']=widget
   labels=['함께 가자.','이곳에서 무슨 일이 있었는지 자세하게 이야기해 줄래?','다른 길을 찾아보자.']
   buttons=sorted([o for o in u.ObjectIterator(u.Button) if o.get_path_name().startswith(widget.get_path_name()) and o.get_name().startswith('Choice_Button_')],key=lambda o:o.get_name());assert len(buttons)==3
   state['buttons']=buttons
   for i,button in enumerate(buttons):
    text=next(o for o in u.ObjectIterator(u.RichTextBlock) if o.get_path_name().startswith(widget.get_path_name()) and o.get_name()=='Choice_Text_'+chr(65+i));text.set_text(u.Text(labels[i]));button.set_visibility(u.SlateVisibility.VISIBLE)
   widget.refresh_choice_visuals()
   state.update(phase=4,at=time.monotonic());return
  if state['phase']==4 and time.monotonic()-state['at']>1:
   state['buttons'][1].set_keyboard_focus()
   state.update(phase=5,at=time.monotonic());return
  if state['phase']==5 and time.monotonic()-state['at']>1:
   assert state['buttons'][1].has_keyboard_focus()
   images=[o for o in u.ObjectIterator(u.Image) if o.get_path_name().startswith(state['legacy'].get_path_name())]
   visible=[o for o in images if o.get_visibility()==u.SlateVisibility.HIT_TEST_INVISIBLE]
   assert len(visible)==5, 'Expected three backgrounds, one cursor and one star'
   stars=[o for o in visible if o.get_render_opacity()<.999];assert len(stars)==1, 'Exactly one pulsing star expected'
   state['star']=stars[0];state['star_opacity']=stars[0].get_render_opacity()
   u.SystemLibrary.execute_console_command(w,'Shot showui nosuffix filename='+(out/'legacy-choice-game.png').as_posix())
   state.update(phase=6,at=time.monotonic());return
  if state['phase']==6 and time.monotonic()-state['at']>1:
   assert abs(state['star'].get_render_opacity()-state['star_opacity'])>.01, 'Star animation is not ticking'
   finish(True)
 except Exception:finish(False,traceback.format_exc())
a=u.new_object(u.SceneDirectorAsset);steps=[u.SceneDirectorLibrary.make_director_step(t) for t in [u.DirectorNodeType.START,u.DirectorNodeType.CINEMATIC_MODE,u.DirectorNodeType.DIALOGUE,u.DirectorNodeType.GAMEPLAY_RETURN,u.DirectorNodeType.END]]
for i in range(4):steps[i].set_editor_property('next_nodes',[steps[i+1].get_editor_property('id')])
steps[2].set_editor_property('speaker_name',u.Text('이름'));steps[2].set_editor_property('dialogue_text',u.Text('세상에서 살아남기 위해선,\n그 세상에 맞는 모습으로 자신을 변화시킬 필요가 있다.'));steps[2].set_editor_property('dialogue_advance',u.DirectorDialogueAdvance.CLICK);steps[2].set_editor_property('duration',0.1)
choices=[]
for key,label in [('Together','함께 가자.'),('Explain','이곳에서 무슨 일이 있었는지 자세하게 이야기해 줄래?'),('Another','다른 길을 찾아보자.')]:
 c=u.DirectorChoice();c.set_editor_property('key',key);c.set_editor_property('text',u.Text(label));choices.append(c)
steps[2].set_editor_property('choices',choices)
a.set_editor_property('steps',steps);assert u.SceneDirectorLibrary.compile_director(a) is not None
actor=u.get_editor_subsystem(u.EditorActorSubsystem).spawn_actor_from_class(u.SceneDirectorPlayer,u.Vector(0,0,0))
actor.set_editor_property('auto_play',False);actor.set_editor_property('director',a)
state['asset']=a
handle=u.register_slate_post_tick_callback(tick)
level.editor_request_begin_play()

