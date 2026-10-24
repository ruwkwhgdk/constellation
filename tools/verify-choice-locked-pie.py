"""PIE lock/unlock verification in an isolated user directory; no production asset saves."""
import unreal as u
import time,json,traceback
from pathlib import Path
assert 'ChoiceLocked/PIE' in Path(u.Paths.project_saved_dir()).as_posix()
out=Path(u.Paths.project_saved_dir())/'ChoiceLocked';out.mkdir(parents=True,exist_ok=True)
level=u.get_editor_subsystem(u.LevelEditorSubsystem);editor=u.get_editor_subsystem(u.UnrealEditorSubsystem)
state={'phase':0,'start':time.monotonic()}
def finish(ok,error=''):
 (out/'pie-result.json').write_text(json.dumps({'success':ok,'error':error},ensure_ascii=False),encoding='utf8')
 u.log('LOCKED_CHOICE_PIE '+str(ok)+' '+error);u.unregister_slate_post_tick_callback(handle);level.editor_request_end_play();u.SystemLibrary.quit_editor()
def shot(w,name):u.SystemLibrary.execute_console_command(w,'Shot showui filename='+(out/(name+'.png')).as_posix())
def advance(p):state.update(phase=p,at=time.monotonic())
def tick(dt):
 try:
  if time.monotonic()-state['start']>90:raise RuntimeError('Locked choice PIE timeout')
  w=editor.get_game_world()
  if not w:return
  p=state['phase']
  if p==0:
   r=next(iter(u.GameplayStatics.get_all_actors_of_class(w,u.SceneDirectorPlayer)),None);assert r and r.play_director();state['runner']=r;advance(1);return
  r=state['runner'];t=time.monotonic()-state['at']
  if p==1 and t>2:
   assert r.is_waiting_for_choice();assert not r.select_dialogue_choice('Force');shot(w,'native-locked');advance(2)
  elif p==2 and t>.6:
   assert r.set_choice_availability('Force',True,u.Text(''));advance(3)
  elif p==3 and t>.38:shot(w,'native-opening');advance(4)
  elif p==4 and t>.7:shot(w,'native-open');advance(5)
  elif p==5 and t>.5:
   assert r.select_dialogue_choice('Force');advance(6)
  elif p==6 and t>.5:
   assert not r.is_waiting_for_choice()
   widget=u.DialogueStyleEditorLibrary.create_choice_review(w);assert widget;assert widget.set_choice_availability(2,False,u.Text('힘이 부족합니다.'));widget.add_to_viewport(100);state['legacy']=widget
   buttons=sorted([o for o in u.ObjectIterator(u.Button) if o.get_path_name().startswith(widget.get_path_name()) and o.get_name().startswith('Choice_Button_')],key=lambda o:o.get_name());assert len(buttons)==3
   labels=['틈으로 밖을 살펴본다.','락커 안을 둘러본다.','문을 연다. (필요 스탯 : 힘 1)']
   for i,b in enumerate(buttons):
    text=next(o for o in u.ObjectIterator(u.RichTextBlock) if o.get_path_name().startswith(widget.get_path_name()) and o.get_name()=='Choice_Text_'+chr(65+i));text.set_text(u.Text(labels[i]));b.set_visibility(u.SlateVisibility.VISIBLE)
   state['buttons']=buttons;assert not buttons[2].get_is_enabled();widget.refresh_choice_visuals();buttons[1].set_keyboard_focus();advance(7)
  elif p==7 and t>.6:
   assert not state['buttons'][2].get_is_enabled();assert state['buttons'][1].has_keyboard_focus();shot(w,'legacy-locked');advance(8)
  elif p==8 and t>.5:
   assert state['legacy'].set_choice_availability(2,True,u.Text(''));advance(9)
  elif p==9 and t>.38:shot(w,'legacy-opening');advance(10)
  elif p==10 and t>.7:
   assert state['buttons'][2].get_is_enabled();assert state['buttons'][1].has_keyboard_focus();shot(w,'legacy-open');advance(11)
  elif p==11 and t>.5:finish(True)
 except Exception:finish(False,traceback.format_exc())
a=u.new_object(u.SceneDirectorAsset);steps=[u.SceneDirectorLibrary.make_director_step(t) for t in [u.DirectorNodeType.START,u.DirectorNodeType.CINEMATIC_MODE,u.DirectorNodeType.DIALOGUE,u.DirectorNodeType.GAMEPLAY_RETURN,u.DirectorNodeType.END]]
for i in range(4):steps[i].set_editor_property('next_nodes',[steps[i+1].get_editor_property('id')])
steps[2].set_editor_property('speaker_name',u.Text('이름'));steps[2].set_editor_property('dialogue_text',u.Text('세상에서 살아남기 위해선,\n그 세상에 맞는 모습으로 자신을 변화시킬 필요가 있다.'));steps[2].set_editor_property('dialogue_advance',u.DirectorDialogueAdvance.CLICK);steps[2].set_editor_property('duration',0.1)
choices=[]
for key,label in [('Slit','틈으로 밖을 살펴본다.'),('Inside','락커 안을 둘러본다.'),('Force','문을 연다. (필요 스탯 : 힘 1)')]:
 c=u.DirectorChoice();c.set_editor_property('key',key);c.set_editor_property('text',u.Text(label));c.set_editor_property('enabled',key!='Force');c.set_editor_property('disabled_reason',u.Text('힘이 부족합니다.' if key=='Force' else ''));choices.append(c)
steps[2].set_editor_property('choices',choices)
a.set_editor_property('steps',steps);assert u.SceneDirectorLibrary.compile_director(a) is not None
actor=u.get_editor_subsystem(u.EditorActorSubsystem).spawn_actor_from_class(u.SceneDirectorPlayer,u.Vector(0,0,0))
actor.set_editor_property('auto_play',False);actor.set_editor_property('director',a)
state['asset']=a
handle=u.register_slate_post_tick_callback(tick)
level.editor_request_begin_play()

