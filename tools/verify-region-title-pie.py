import unreal as u
import time,json,traceback
from pathlib import Path
root=Path(u.Paths.project_dir());out=root/'Saved/RegionTitle';out.mkdir(parents=True,exist_ok=True)
assert 'RegionTitle/PIE' in Path(u.Paths.project_saved_dir()).as_posix()
level=u.get_editor_subsystem(u.LevelEditorSubsystem);editor=u.get_editor_subsystem(u.UnrealEditorSubsystem)
state={'phase':0,'start':time.monotonic(),'case':0,'checks':[]}
cases=[('normal','폐교','텅 빈 교실'),('long','오래된 별들의 기억이 잠든 폐교','돌아오지 않는 학생들의 이야기가 남아 있는 교실'),('no-subtitle','지하 동굴','')]
def finish(ok,error=''):
 (out/'pie-result.json').write_text(json.dumps({'success':ok,'error':error,'checks':state['checks']},ensure_ascii=False,indent=2),encoding='utf8')
 u.log('REGION_PIE_RESULT '+str(ok)+' '+error);u.unregister_slate_post_tick_callback(handle);level.editor_request_end_play();u.SystemLibrary.quit_editor()
def tick(dt):
 try:
  if time.monotonic()-state['start']>180:raise RuntimeError('PIE title timeout')
  w=editor.get_game_world()
  if not w:return
  now=u.GameplayStatics.get_time_seconds(w)
  if state['phase']==0:
   pc=u.GameplayStatics.get_player_controller(w,0);assert pc
   state.update(pc=pc,cursor=pc.get_editor_property('show_mouse_cursor'),move=pc.is_move_input_ignored(),look=pc.is_look_input_ignored())
   state['toast']=u.TutorialToastEditorLibrary.create_toast_review(w,1,40)
   state['phase']=1
  if state['phase']==1:
   case=cases[state['case']];widget=u.RegionTitleEditorLibrary.create_region_review(w,u.Text(case[1]),u.Text(case[2]));assert widget
   assert str(widget.get_region_title_text())==case[1]
   state.update(widget=widget,at=now,phase=2);return
  widget=state['widget'];pc=state['pc']
  assert not u.GameplayStatics.is_game_paused(w)
  assert pc.get_editor_property('show_mouse_cursor')==state['cursor']
  assert pc.is_move_input_ignored()==state['move'] and pc.is_look_input_ignored()==state['look']
  if state['phase']==2 and now-state['at']>1.2:
   assert widget.is_in_viewport() and widget.get_text_opacity()>.95
   u.SystemLibrary.execute_console_command(w,'Shot showui nosuffix filename='+(out/('region-'+cases[state['case']][0]+'.png')).as_posix())
   state['phase']=3;return
  if state['phase']==3 and now-state['at']>4.3:
   assert widget.is_presentation_finished() and not widget.is_in_viewport()
   state['checks'].append(cases[state['case']][0]+' text/display/timeout/input-preserved')
   state['case']+=1
   if state['case']<len(cases):state['phase']=1;return
   a=u.RegionTitleEditorLibrary.create_region_review(w,u.Text('첫 지역'),u.Text('교실'))
   b=u.RegionTitleEditorLibrary.create_region_review(w,u.Text('다음 지역'),u.Text('복도'))
   assert not a.is_in_viewport() and b.is_in_viewport()
   state.update(widget=b,phase=4,at=now);return
  if state['phase']==4 and now-state['at']>.6:
   assert widget.is_in_viewport();widget.remove_from_parent();assert widget.is_presentation_finished()
   state['checks'].append('replacement/external-removal cleanup')
   state['toast'].remove_from_parent()
   triggers=u.GameplayStatics.get_all_actors_of_class(w,trigger_class);assert triggers
   triggers[0].call_method('Show Region Title')
   state.update(phase=5,at=now);return
  if state['phase']==5 and now-state['at']>.15:
   titles=[o for o in u.ObjectIterator(u.RegionTitleWidget) if o.is_in_viewport()]
   assert len(titles)==1,'Real trigger did not display one title'
   title=titles[0];assert str(title.get_region_subtitle_text())=='텅 빈 교실',str(title.get_region_subtitle_text())
   assert not title.get_region_title_text().is_empty()
   state.update(widget=title,phase=6,at=now);return
  if state['phase']==6 and now-state['at']>4.3:
   assert not widget.is_in_viewport();state['checks'].append('saved BP_RegionTrigger/data-table/display/removal');finish(True)
 except Exception:finish(False,traceback.format_exc())
# Verify the saved widget class, without applying any transient migration.
cls=u.load_class(None,'/Game/Constellation/UI/Widgets/WBP_RegionTitle.WBP_RegionTitle_C')
assert isinstance(u.get_default_object(cls),u.RegionTitleWidget)
trigger_class=u.load_class(None,'/Game/Constellation/Gameplay/Interaction/Actors/BP_RegionTrigger.BP_RegionTrigger_C')
trigger=u.get_editor_subsystem(u.EditorActorSubsystem).spawn_actor_from_class(trigger_class,u.Vector(10000,10000,0))
trigger.set_editor_property('IsActive',False)
trigger.set_editor_property('RegionStringKey',u.Text('Region_AbandonedSchool_Classroom_Start'))
handle=u.register_slate_post_tick_callback(tick);level.editor_request_begin_play()
