"""Actual-map PIE regression. Run with an isolated -UserDir containing SceneReleaseValidation.
No editor assets are saved. Report is written to the isolated user's Saved directory.
"""
import unreal as u
import time,json,traceback
from pathlib import Path
save_dir=Path(u.Paths.project_saved_dir()).resolve()
assert 'SceneReleaseValidation' in str(save_dir), 'Requires isolated -UserDir; never run against player saves'
out=save_dir/'scene-pie-result.json'
editor=u.get_editor_subsystem(u.UnrealEditorSubsystem)
level=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
# This suite covers the four pre-existing events. S0 has its own two-order/cancel suite.
# Isolate it in this unsaved test world so LevelReady cannot take the active event slot.
actor_subsystem=u.get_editor_subsystem(u.EditorActorSubsystem)
for actor in actor_subsystem.get_all_level_actors():
 if isinstance(actor,u.SchoolOpeningSceneActor):actor_subsystem.destroy_actor(actor)
 elif isinstance(actor,u.SceneEventBinding):
  director=actor.get_editor_property('director')
  if director and director.get_name()=='DA_S0_Opening':actor.set_editor_property('enabled',False)
state={'phase':'boot','start':time.monotonic(),'phase_start':time.monotonic(),'results':[], 'index':0,'reload':False}
names=['DA_Appear_Slime_Event','DA_Dump_Slime_Star_Obj_Get_Event','DA_Little_Girl_Event_Mushroom_Cave','DA_StatueInteraction']
def phase(p):
 state['phase']=p;state['phase_start']=time.monotonic();u.log('SCENE_PIE_PHASE '+p)
def finish(ok,error=''):
 state['success']=ok;state['error']=error
 out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({k:v for k,v in state.items() if k not in ['runner','world','events','binding']},ensure_ascii=False,indent=2),encoding='utf-8')
 u.log('SCENE_PIE_RESULT '+str(ok)+' '+error)
 u.unregister_slate_post_tick_callback(handle)
 level.editor_request_end_play()
 u.SystemLibrary.quit_editor()
def tick(dt):
 try:
  if time.monotonic()-state['start']>480:raise RuntimeError('Overall PIE timeout')
  if time.monotonic()-state['phase_start']>150:raise RuntimeError('Phase timeout: '+state['phase'])
  if state['phase']=='end':
   if not level.is_in_play_in_editor():level.editor_request_begin_play();phase('boot')
   return
  w=editor.get_game_world()
  if not w:return
  e=next((obj for obj in u.ObjectIterator(u.SceneEventSubsystem) if obj.get_outer()==w),None)
  if not e:return
  if state['phase']=='boot':
   if not e.get_editor_property('level_ready'):return
   assert u.GameplayStatics.get_player_pawn(w,0), 'No actual player pawn'
   state['world']=w;state['events']=e
   state['results'].append({'ready':True,'reload':state['reload']})
   phase('start_scene');return
  if state['phase']=='start_scene':
   target='DA_StatueInteraction' if state['reload'] else names[state['index']]
   bindings=[a for a in u.GameplayStatics.get_all_actors_of_class(w,u.SceneEventBinding) if a.get_editor_property('director') and a.get_editor_property('director').get_name()==target]
   assert len(bindings)==1, (target,'ambiguous/missing binding')
   b=bindings[0]
   if target=='DA_Little_Girl_Event_Mushroom_Cave' and not state.get('entered_volume'):
    volume=b.get_editor_property('source');assert volume
    center,_=volume.get_actor_bounds(False)
    u.GameplayStatics.get_player_pawn(w,0).set_actor_location(center,False,True)
    state['entered_volume']=True
    return
   r=e.get_editor_property('active_player')
   if target=='DA_Little_Girl_Event_Mushroom_Cave':
    if not r:return
   else:
    b.test_signal();r=e.get_editor_property('active_player')
   assert r,(target,str(b.get_editor_property('status')),list(e.get_editor_property('history')))
   u.log('SCENE_PIE_START '+target+' pawn='+str(u.GameplayStatics.get_player_pawn(w,0)))
   state['runner']=r;state['binding']=b;state['dialogues']=0;state['last_text']=''
   if state['reload']:
    values={str(k):v for k,v in r.get_editor_property('bool_values').items()};assert values.get('HasInteracted') is True,values
    state['results'].append({'restored_HasInteracted':True,'event':str(r.get_editor_property('event_key'))});e.cancel_active();finish(True);return
   phase('playing');return
  if state['phase']=='playing':
   r=state['runner']
   if e.get_editor_property('active_player'):
    if names[state['index']]=='DA_Little_Girl_Event_Mushroom_Cave' and r.is_waiting_for_dialogue() and not state.get('girl_cancel_checked'):
     e.cancel_active()
     assert not e.get_editor_property('active_player'),'Girl cancellation did not stop'
     pc=u.GameplayStatics.get_player_controller(w,0)
     assert not pc.is_move_input_ignored() and not pc.is_look_input_ignored(),'Girl cancellation did not restore controls'
     state['girl_cancel_checked']=True;state['results'].append({'girl_cancel_restored_controls':True})
     state['binding'].test_signal();state['runner']=e.get_editor_property('active_player')
     assert state['runner'],'Girl scene could not restart after cancellation'
     return
    if r.is_waiting_for_choice():
     choices=r.get_editor_property('current_choices');assert r.select_dialogue_choice(choices[0].get_editor_property('key'))
    elif r.is_waiting_for_dialogue():
     text=str(r.get_editor_property('current_dialogue'))
     if text!=state['last_text']:state['dialogues']+=1;state['last_text']=text
     r.advance_dialogue()
    return
   status=str(state['binding'].get_editor_property('status'));history=list(e.get_editor_property('history'))
   assert not e.get_editor_property('last_save_error'),str(e.get_editor_property('last_save_error'))
   assert '완료' in status,(status,history)
   pc=u.GameplayStatics.get_player_controller(w,0)
   assert not pc.is_move_input_ignored(),('Movement not restored',names[state['index']],history)
   assert not pc.is_look_input_ignored(),'Look not restored'
   state['results'].append({'scene':names[state['index']],'status':status,'dialogues':state['dialogues'],'history':[str(x) for x in history]})
   state['index']+=1
   if state['index']==len(names):
    assert u.GameplayStatics.does_save_game_exist('ConstellationSaveGame',0),'No shared save file'
    state['reload']=True;state.pop('runner',None);state.pop('world',None);state.pop('events',None);state.pop('binding',None)
    level.editor_request_end_play();phase('end')
   else:phase('start_scene')
 except Exception:finish(False,traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick)
level.editor_request_begin_play()
