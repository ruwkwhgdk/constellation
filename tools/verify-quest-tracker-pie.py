"""Actual school HUD, isolated save directory; transient quest fixtures never save assets."""
import unreal as u,time,json,traceback,uuid
from pathlib import Path
root=Path(u.Paths.project_dir());out=root/'Saved/QuestTracker'
assert 'QuestTracker/PIE' in Path(u.Paths.project_saved_dir()).as_posix(), 'Refuse to touch player saves'
editor=u.get_editor_subsystem(u.UnrealEditorSubsystem);level=u.get_editor_subsystem(u.LevelEditorSubsystem)
play=u.get_default_object(u.load_class(None,'/Script/UnrealEd.LevelEditorPlaySettings'))
play.set_editor_property('NewWindowWidth',1920);play.set_editor_property('NewWindowHeight',1080)
s={'phase':0,'started':time.monotonic(),'checks':[],'shots':[]}
def subsystem(outer,cls):return next((o for o in u.ObjectIterator(cls) if o.get_outer()==outer),None)
def shot(w,name):
 u.SystemLibrary.execute_console_command(w,'Shot showui nosuffix filename='+(out/(name+'.png')).as_posix());s['shots'].append(name)
def finish(ok,error=''):
 (out/'pie-result.json').write_text(json.dumps({'success':ok,'error':error,'checks':s['checks'],'shots':s['shots']},ensure_ascii=False,indent=2),encoding='utf8')
 u.log('QUEST_TRACKER_PIE_RESULT '+str(ok)+' '+error)
 u.unregister_slate_post_tick_callback(handle);level.editor_request_end_play();u.SystemLibrary.quit_editor()
def tick(dt):
 try:
  if time.monotonic()-s['started']>240:raise RuntimeError('Tracker review timeout: '+str(s['phase']))
  w=editor.get_game_world()
  if not w:return
  now=u.GameplayStatics.get_time_seconds(w)
  if s['phase']==0:
   pc=u.GameplayStatics.get_player_controller(w,0)
   widget=next((o for o in u.ObjectIterator(u.QuestTrackerWidget) if o.is_in_viewport()),None)
   if now>5 and not s.get('wait_logged'):
    s['wait_logged']=True;u.log('TRACKER_REVIEW_WAIT pc='+str(pc)+' widget='+str(widget))
   if not pc or not widget or now<2:return
   # SkipCinematics intentionally bypasses S0; release its native bootstrap eye
   # mask via the existing abort cleanup, without completing/saving that scene.
   for opening in u.GameplayStatics.get_all_actors_of_class(w,u.SchoolOpeningSceneActor):opening.call_method('DirectorStopped',(False,))
   # The skipped intro owns the startup black overlay. Clear it only for this review.
   visible_widgets=[]
   for o in u.ObjectIterator(u.UserWidget):
    if o.is_in_viewport():visible_widgets.append(o.get_class().get_name())
    if o.get_class().get_name() in ('WBP_Fade_C','WBP_Tutorial_C') and o.is_in_viewport():o.remove_from_parent()
   pc.player_camera_manager.stop_camera_fade()
   u.log('TRACKER_REVIEW_PAWN '+str(pc.get_controlled_pawn().get_actor_location()))
   minimap=subsystem(w,u.MinimapWorldSubsystem)
   u.log('TRACKER_REVIEW_CONTEXT '+str(visible_widgets)+' floor='+str(minimap.get_current_floor_id()))
   for m in u.ObjectIterator(u.MinimapWidget):
    if m.is_in_viewport():u.log('MAP_REVIEW '+str(m.get_visibility())+' opacity='+str(m.get_render_opacity())+' size='+str(m.get_desired_size()))
   q=subsystem(u.GameplayStatics.get_game_instance(w),u.QuestSubsystem)
   q.try_unlock_quest('MQ1_ExitSchool');q.accept_quest('MQ1_ExitSchool');assert q.set_tracked_quest('MQ1_ExitSchool')
   s.update(q=q,widget=widget,pc=pc,at=now,phase=1,move=pc.is_move_input_ignored(),look=pc.is_look_input_ignored(),cursor=pc.get_editor_property('show_mouse_cursor'))
   return
  widget=s['widget'];q=s['q'];pc=s['pc']
  assert not u.GameplayStatics.is_game_paused(w)
  assert pc.is_move_input_ignored()==s['move'] and pc.is_look_input_ignored()==s['look']
  assert pc.get_editor_property('show_mouse_cursor')==s['cursor']
  if now-s['at']<.6:return
  if s['phase']==1:
   expected=q.get_tracked_quest_display_info();actual=widget.get_tracker_snapshot()
   assert str(actual.title)==str(expected.title) and str(actual.current_objective_text)==str(expected.current_objective_text)
   assert not str(widget.get_quantity_label()),'Legacy sequential objective became a quantity'
   assert widget.is_tracker_presented()
   s['checks'].append('actual school quest title/objective, no implicit quantity, existing HUD instance')
   shot(w,'tracker-school');s['base_origin']=widget.get_tracker_origin();s.update(phase=2,at=now);return
  if s['phase']==2:
   # Fixtures are transient data, not production strings or gameplay asset edits.
   # Unsaved factory assets allow EditDefaultsOnly authoring; never call save_asset.
   folder='/Game/__QuestTrackerReview_'+uuid.uuid4().hex
   factory=u.DataAssetFactory();factory.set_editor_property('data_asset_class',u.QuestDefinition)
   quest=u.AssetToolsHelpers.get_asset_tools().create_asset('Quest',folder,u.QuestDefinition,factory)
   quest.set_editor_property('quest_id','TrackerReview');quest.set_editor_property('type',u.QuestType.SUB)
   quest.set_editor_property('title',u.Text('사라진 소녀의 흔적'))
   quest.set_editor_property('objective',[u.Text('무너진 복도를 지나 소녀가 남긴 흔적을 따라 다음 교실로 이동하세요.'),u.Text('장치를 작동시키세요.')])
   first=u.QuestProgressStepDef();first.set_editor_property('inner_progress_count',3)
   second=u.QuestProgressStepDef();second.set_editor_property('inner_progress_count',3);second.set_editor_property('show_objective_quantity',True)
   quest.set_editor_property('progress_steps',[first,second])
   factory.set_editor_property('data_asset_class',u.QuestDatabase)
   db=u.AssetToolsHelpers.get_asset_tools().create_asset('Database',folder,u.QuestDatabase,factory)
   db.set_editor_property('quests',[quest]);q.register_quest_database(db);assert q.accept_quest('TrackerReview');assert q.set_tracked_quest('TrackerReview')
   s.update(quest=quest,db=db,fixture_folder=folder,phase=3,at=now);return
  if s['phase']==3:
   assert widget.is_tracker_presented() and not str(widget.get_quantity_label())
   s['long_size']=[widget.get_tracker_content_size().x,widget.get_tracker_content_size().y]
   shot(w,'tracker-long');s['checks'].append('transient long Korean objective wraps; sequential inner progress remains hidden')
   s.update(phase=32,at=now);return
  if s['phase']==32:
   assert q.advance_quest_progress('TrackerReview');assert q.advance_inner_quest_progress('TrackerReview')
   s.update(phase=4,at=now);return
  if s['phase']==4:
   assert str(widget.get_quantity_label())=='1/3',str(widget.get_quantity_label())
   assert widget.get_tracker_content_size().y<s['long_size'][1],'Long objective did not expand layout'
   shot(w,'tracker-quantity');s['checks'].append('objective change updates same widget, explicit count 1/3, height shrinks')
   s['count_size']=widget.get_tracker_content_size();s['opacity']=widget.get_render_opacity()
   for _ in range(5):widget.refresh_tracker()
   s.update(phase=5,at=now);return
  if s['phase']==5:
   assert widget.get_render_opacity()==s['opacity'] and str(widget.get_quantity_label())=='1/3'
   assert widget.get_tracker_content_size()==s['count_size']
   s['checks'].append('repeated refresh keeps opacity, contents and layout stable')
   # Complete the fixture and the real isolated-save quest: auto selection then no tracked quest.
   assert q.complete_quest('TrackerReview',u.Name(''))
   assert str(q.get_tracked_quest_id())=='MQ1_ExitSchool','Auto selection changed'
   assert q.complete_quest('MQ1_ExitSchool',u.Name(''))
   s.update(phase=6,at=now);return
  if s['phase']==6:
   assert not widget.is_tracker_presented() and not str(widget.get_quantity_label())
   shot(w,'tracker-hidden');s['checks'].append('existing auto selection retained; no tracked quest hides whole tracker; input unchanged')
   s.update(phase=7,at=now);return
  if s['phase']==7:finish(True)
 except Exception:finish(False,traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick)
# This existing editor helper only starts a floating PIE window; it performs no carry actions.
u.CarryEditorLibrary.start_carry_review_play()
