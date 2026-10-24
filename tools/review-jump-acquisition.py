"""Real interaction PIE recording; editor-only setup is never saved."""
import unreal as u,json,time,traceback
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/JumpAcquisition/Review05';O.mkdir(parents=True,exist_ok=True)
u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
A=u.get_editor_subsystem(u.EditorActorSubsystem);actors=list(A.get_all_level_actors())
for a in actors:
 if isinstance(a,u.SceneEventBinding) and a.get_editor_property('trigger')!=u.SceneEventTrigger.INTERACTION:a.set_editor_property('enabled',False)
 if isinstance(a,u.SchoolOpeningSceneActor):A.destroy_actor(a)
 if isinstance(a,u.PlayerStart):a.set_actor_location(u.Vector(-13820,-2450,-700),False,True);a.set_actor_rotation(u.Rotator(),False)
u.EditorPythonScripting.set_keep_python_script_alive(True)
E=u.get_editor_subsystem(u.UnrealEditorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
state={'start':time.monotonic(),'phase':'startup','frames':[],'shots':set(),'ui_start':None,'last_say':None}
L.editor_request_begin_play()
def vec(v):return [v.x,v.y,v.z]
def finish(error=None):
 if error:(O/'error.txt').write_text(error,encoding='utf8')
 (O/'recording.json').write_text(json.dumps(state['frames'],ensure_ascii=False),encoding='utf8')
 u.unregister_slate_post_tick_callback(handle);L.editor_request_end_play();u.SystemLibrary.quit_editor()
def tick(dt):
 try:
  now=time.monotonic()
  if now-state['start']>300:finish('Timed out '+state['phase']);return
  w=E.get_game_world()
  if not w:return
  pc=u.GameplayStatics.get_player_controller(w,0);pawn=u.GameplayStatics.get_player_character(w,0)
  if not pawn:return
  if state['phase']=='startup':
   if now-state['start']<8:return
   stage=u.GameplayStatics.get_actor_of_class(w,u.JumpAcquisitionStage);assert stage
   star=stage.get_editor_property('star');pawn.set_actor_location(u.Vector(-13820,-2450,-700),False,True)
   pc.set_control_rotation(u.Rotator(yaw=0,pitch=-12));pawn.set_actor_rotation(u.Rotator(),False)
   state.update(phase='settle',stage=stage,star=star,ready=now);return
  if state['phase']=='settle':
   if now-state['ready']<2:return
   u.SystemLibrary.execute_console_command(w,'SceneDirector.SkipCinematics 0')
   state['star'].call_method('Interact',(pawn,None));state.update(phase='running',run_start=now)
  stage=state['stage'];runners=list(u.GameplayStatics.get_all_actors_of_class(w,u.SceneDirectorPlayer));active=next((a for a in runners if a.is_director_playing()),None)
  ui=next(x for x in u.ObjectIterator(u.AbilityAcquisitionSubsystem) if x.get_outer()==w)
  if ui.is_presenting():
   if state['ui_start'] is None:state['ui_start']=now
   if now-state['ui_start']>7:ui.dismiss(False)
  if active and active.is_waiting_for_dialogue():
   if state['last_say'] is None:state['last_say']=now
   if now-state['last_say']>3.5:active.advance_dialogue()
  phase=str(stage.get_editor_property('phase'));cm=pc.player_camera_manager
  if phase in ['Reach','Contact','Surprise','Absorb','Chest','Palm']:
   assert isinstance(pc.get_view_target(),u.CameraActor),'Scene camera lost during '+phase
  row={'t':now-state['run_start'],'game':u.GameplayStatics.get_time_seconds(w),'phase':phase,'ui':ui.is_presenting(),'camera':vec(cm.get_camera_location()),'character':vec(pawn.get_actor_location()),'hand':vec(pawn.mesh.get_socket_location('hand_r'))}
  j=len(state['frames']);assert u.SceneDirectorLibrary.capture_game_viewport_frame(w,str(O/('frame-%05d.png'%j)))
  state['frames'].append(row)
  if phase not in state['shots'] and phase not in ['Begin','None']:
   state['shots'].add(phase);(O/(phase+'.json')).write_text(json.dumps(row),encoding='utf8')
  if not active and now-state['run_start']>2:
   ev=next(x for x in u.ObjectIterator(u.SceneEventSubsystem) if x.get_outer()==w)
   assert stage.get_editor_property('completed'),list(ev.get_editor_property('history'))
   ability=pawn.get_editor_property('Ac_Ability');assert ability.get_editor_property('IsJumpUnlocked')
   assert not pc.is_move_input_ignored() and not pc.is_look_input_ignored(),'Input lock leaked'
   assert not u.GameplayStatics.is_game_paused(w),'Pause leaked'
   assert state['ui_start'] is not None,'Ability UI did not appear'
   assert {'Inspect','Reach','Contact','Surprise','Absorb','Chest','Palm','Release'}.issubset(state['shots']),'Missing storyboard beats'
   (O/'success.json').write_text(json.dumps({'completed':True,'jump_unlocked':True,'input_restored':True,'frames':len(state['frames'])}),encoding='utf8');finish()
 except:finish(traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick)
