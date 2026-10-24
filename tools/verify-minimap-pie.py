import unreal as u,time,json,traceback,math
from pathlib import Path
root=Path(u.Paths.project_dir());out=root/'Saved/Minimap';editor=u.get_editor_subsystem(u.UnrealEditorSubsystem);level=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert 'Minimap/PIE' in Path(u.Paths.project_saved_dir()).as_posix()
s={'phase':0,'start':time.monotonic(),'checks':[]}
def finish(ok,error=''):
 (out/'pie-result.json').write_text(json.dumps({'success':ok,'error':error,'checks':s['checks']},ensure_ascii=False,indent=2),encoding='utf8');u.log('MINIMAP_PIE_RESULT '+str(ok)+' '+error);u.unregister_slate_post_tick_callback(handle);level.editor_request_end_play();u.SystemLibrary.quit_editor()
def findsub(w,cls):return next((x for x in u.ObjectIterator(cls) if x.get_outer()==w),None)
def shot(w,name):u.SystemLibrary.execute_console_command(w,'Shot showui nosuffix filename='+(out/(name+'.png')).as_posix())
def global_cell(f,i):return u.IntPoint(int(round(f.origin.x/f.cell_size))+i%f.width,int(round(f.origin.y/f.cell_size))+i//f.width)
def floor(data,id):return next(f for f in data.floors if str(f.floor_id)==str(id))
def move(p,x,y,z):p.set_actor_location(u.Vector(x,y,z+p.capsule_component.get_scaled_capsule_half_height()+3),False,False)
def tick(dt):
 try:
  if time.monotonic()-s['start']>360:raise RuntimeError('Minimap PIE timeout phase '+str(s['phase']))
  w=editor.get_game_world()
  if not w:return
  now=u.GameplayStatics.get_time_seconds(w);pc=u.GameplayStatics.get_player_controller(w,0);pawn=pc.get_controlled_pawn() if pc else None
  sub=findsub(w,u.MinimapWorldSubsystem)
  if not pawn or not sub:return
  memory=findsub(u.GameplayStatics.get_game_instance(w),u.MinimapExplorationSubsystem)
  if s['phase']==0:
   if str(sub.get_current_floor_id())=='None' or sub.get_discovered_cell_count()==0:return
   data=u.GameplayStatics.get_actor_of_class(w,u.MinimapRegionActor).get_editor_property('data');f=floor(data,sub.get_current_floor_id())
   s.update(data=data,f=f,at=now,phase=1,pc=pc,pawn=pawn,sub=sub,memory=memory,initial=sub.get_discovered_cell_count(),cursor=pc.get_editor_property('show_mouse_cursor'),move=pc.is_move_input_ignored(),look=pc.is_look_input_ignored())
   s['checks'].append('saved school region creates minimap and progressively discovers actual starting floor');return
  assert not u.GameplayStatics.is_game_paused(w)
  assert pc.get_editor_property('show_mouse_cursor')==s['cursor']
  if s['phase']==1 and now-s['at']>1:
   assert pc.is_move_input_ignored()==s['move'] and pc.is_look_input_ignored()==s['look'];shot(w,'minimap-start')
   f=s['f'];pos=pawn.get_actor_location();s['oldpos']=pos
   move(pawn,pos.x-450,pos.y,0);s.update(phase=2,at=now);return
  if s['phase']==2 and now-s['at']>1:
   assert sub.get_discovered_cell_count()>s['initial'],'Walking did not expand discovery';s['checks'].append('actual movement grows discovery without clearing previous cells');shot(w,'minimap-explored')
   quests=findsub(u.GameplayStatics.get_game_instance(w),u.QuestSubsystem);quests.try_unlock_quest('MQ1_ExitSchool');quests.accept_quest('MQ1_ExitSchool');quests.set_tracked_quest('MQ1_ExitSchool')
   s.update(phase=3,at=now);return
  if s['phase']==3 and now-s['at']>.4:
   shot(w,'minimap-quest')
   # The explicit objective API uses real level positions; it must not reveal terrain.
   count=sub.get_discovered_cell_count();sub.set_objective_override('AbandonedSchool',s['f'].floor_id,u.Vector(-950,0,1000));s['before_target']=count;s.update(phase=4,at=now);return
  if s['phase']==4 and now-s['at']>.5:
   assert sub.get_discovered_cell_count()==s['before_target'],'Objective revealed terrain';s['checks'].append('objective binding/override does not reveal surrounding terrain');shot(w,'minimap-edge-target')
   f=s['f'];cells=list(f.get_editor_property('cells'));heights=list(f.get_editor_property('surface_z'));probe=None
   for i,v in enumerate(cells):
    x=i%f.width;y=i//f.width
    if v!=2 or x<3 or x>=f.width-3 or y<3 or y>=f.height-3:continue
    for step in (1,f.width):
     a=i-step*2;b=i+step*2
     if cells[a]==1 and cells[b]==1 and abs(heights[a]-heights[b])<25 and not memory.is_revealed('AbandonedSchool',f.floor_id,50,global_cell(f,b)):
      probe=(a,b);break
    if probe:break
   assert probe,'No actual wall-separated floor probe found'
   a,b=probe;s['wall_b']=b;move(pawn,f.origin.x+(a%f.width+.5)*50,f.origin.y+(a//f.width+.5)*50,heights[a]);s.update(phase=5,at=now);return
  if s['phase']==5 and now-s['at']>1:
   f=s['f'];assert not memory.is_revealed('AbandonedSchool',f.floor_id,50,global_cell(f,s['wall_b'])),'Adjacent floor leaked through actual wall';s['checks'].append('actual structural wall prevents neighboring floor discovery')
   sub.clear_objective_override();sub.unlock_region('AbandonedSchool');sub.unlock_region('AbandonedSchool');assert memory.is_region_unlocked('AbandonedSchool');assert memory.flush();s.update(phase=6,at=now);return
  if s['phase']==6 and now-s['at']>.5:
   shot(w,'minimap-unlocked');saved=u.GameplayStatics.load_game_from_slot('ConstellationSaveGame',0);assert saved
   s['checks'].append('partial exploration plus repeated region unlock and shared save flush')
   pc.unpossess();pc.possess(pawn);s.update(phase=7,at=now);return
  if s['phase']==7 and now-s['at']>.5:
   assert memory.is_region_unlocked('AbandonedSchool') and sub.get_discovered_cell_count()>0;s['checks'].append('re-possession retains map and discovery');finish(True)
 except Exception:finish(False,traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick);level.editor_request_begin_play()
