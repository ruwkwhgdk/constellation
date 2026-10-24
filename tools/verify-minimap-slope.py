"""Actual school ramp and temporary missing-data review, with isolated saves."""
import unreal as u,time,json,traceback
from pathlib import Path
root=Path(u.Paths.project_dir());out=root/'Saved/Minimap'
assert 'Minimap/PIE' in Path(u.Paths.project_saved_dir()).as_posix()
editor=u.get_editor_subsystem(u.UnrealEditorSubsystem);level=u.get_editor_subsystem(u.LevelEditorSubsystem)
s={'phase':0,'start':time.monotonic(),'checks':[]}
def sub(outer,cls):return next((o for o in u.ObjectIterator(cls) if o.get_outer()==outer),None)
def finish(ok,error=''):
 if 'floors' in s:s['data'].set_editor_property('floors',s['floors'])
 (out/'slope-pie-result.json').write_text(json.dumps(dict(success=ok,error=error,checks=s['checks']),ensure_ascii=False,indent=2),encoding='utf8')
 u.log('SLOPE_PIE_RESULT '+str(ok)+' '+error)
 u.unregister_slate_post_tick_callback(handle);level.editor_request_end_play();u.SystemLibrary.quit_editor()
def shot(w,name):u.SystemLibrary.execute_console_command(w,'Shot showui filename='+(out/name).as_posix())
def tick(dt):
 try:
  if time.monotonic()-s['start']>240:raise RuntimeError('Timeout '+str(s['phase']))
  w=editor.get_game_world()
  if not w:return
  now=u.GameplayStatics.get_time_seconds(w);pc=u.GameplayStatics.get_player_controller(w,0);p=pc.get_controlled_pawn() if pc else None
  m=sub(w,u.MinimapWorldSubsystem)
  if not p or not m or now<2:return
  if s['phase']==0:
   for a in u.GameplayStatics.get_all_actors_of_class(w,u.SchoolOpeningSceneActor):a.call_method('DirectorStopped',(False,))
   for a in u.ObjectIterator(u.UserWidget):
    if a.is_in_viewport() and a.get_class().get_name() in ('WBP_Fade_C','WBP_Tutorial_C'):a.remove_from_parent()
   pc.player_camera_manager.stop_camera_fade()
   pc.set_control_rotation(u.Rotator(pitch=-15,yaw=180,roll=0))
   data=u.GameplayStatics.get_actor_of_class(w,u.MinimapRegionActor).get_editor_property('data')
   floors=list(data.floors);points=[]
   # Maintained ramp_1 spans Y 3413..4227 at X=-5580, surface about 1050..1338.
   for y in (3525,3725,3925,4125):
    points.append((-5575,y,1500))
   s.update(data=data,floors=floors,points=points,index=0,phase=1,at=now)
   return
  if s['phase']==1:
   x,y,z=s['points'][s['index']];p.set_actor_location(u.Vector(x,y,z+p.capsule_component.get_scaled_capsule_half_height()+5),False,False)
   s.update(phase=2,at=now);return
  if s['phase']==2 and now-s['at']>2.5:
   x,y,z=s['points'][s['index']]
   assert p.character_movement.is_moving_on_ground(),'Not grounded on ramp'
   pos=p.get_actor_location();assert abs(pos.x-x)<75 and abs(pos.y-y)<75,'Pawn moved away from ramp probe'
   feet=pos.z-p.capsule_component.get_scaled_capsule_half_height()
   u.log('RAMP_SAMPLE '+u.MinimapEditorLibrary.describe_floor_samples(s['data'],u.Vector(pos.x,pos.y,feet)))
   u.log('RAMP_CONTACT '+u.MinimapEditorLibrary.describe_pawn_ground(w))
   assert 1000<feet<1450,'Wrong ground surface: '+str(feet)
   assert str(m.get_current_floor_id())!='None','Grounded ramp lost floor'
   assert m.get_discovered_cell_count()>0,'Confirmed ramp ground did not reveal any cells'
   assert any(o.is_in_viewport() for o in u.ObjectIterator(u.MinimapWidget))
   s['checks'].append('ramp ground resolves at '+str(s['points'][s['index']]))
   s['index']+=1
   if s['index']<len(s['points']):s['phase']=1;return
   shot(w,'slope-ramp');s.update(phase=3,at=now);return
  if s['phase']==3 and now-s['at']>.5:
   # Runtime-only data outage; never save this asset mutation.
   memory=sub(u.GameplayStatics.get_game_instance(w),u.MinimapExplorationSubsystem)
   s['memory']=memory;s['discovered_before']=m.get_discovered_cell_count()
   s['data'].set_editor_property('floors',[]);s.update(phase=4,at=now);return
  if s['phase']==4 and now-s['at']>1.5:
   assert str(m.get_current_floor_id())=='None'
   assert m.get_discovered_cell_count()==0
   shot(w,'slope-unresolved');s['checks'].append('unresolved floor keeps HUD shell mounted without discovery')
   s.update(phase=5,at=now);return
  if s['phase']==5 and now-s['at']>.5:
   s['data'].set_editor_property('floors',s['floors']);s.update(phase=6,at=now);return
  if s['phase']==6 and now-s['at']>1:
   assert str(m.get_current_floor_id())!='None'
   assert m.get_discovered_cell_count()==s['discovered_before'],'Outage/restoration changed discovery'
   s['checks'].append('ground data restoration reacquires floor with unchanged discovery');finish(True)
 except Exception:finish(False,traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick)
u.CarryEditorLibrary.start_carry_review_play()
