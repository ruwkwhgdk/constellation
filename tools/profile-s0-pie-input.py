"""PIE performance via real Enhanced Input; scene/layout never saved."""
import unreal as u,time,json,traceback,hashlib,math
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/PIEPerformance_20261020';O.mkdir(parents=True,exist_ok=True)
mapfile=R/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap';before=hashlib.sha256(mapfile.read_bytes()).hexdigest()
assert not (O/'session.json').exists();(O/'session.json').write_text(json.dumps(dict(map_sha256=before)))
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
E=u.get_editor_subsystem(u.UnrealEditorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
S=dict(start=time.monotonic(),phase='boot',choices=[],samples=[],i=0,waypoint=0,last_sample=0)
phases=['idle','walk','idle_repeat'];waypoints=[(3060,-850),(3060,1000)]
def vec(v):return [v.x,v.y,v.z]
def finish(error=None):
 if S.get('recording'):u.SystemLibrary.execute_console_command(pawn,'csvprofile STOP')
 L.editor_request_end_play()
 (O/'result.json').write_text(json.dumps(dict(error=error,phases=phases,choices=S['choices'],samples=S['samples'],map_unchanged=hashlib.sha256(mapfile.read_bytes()).hexdigest()==before,scope='PIE; real Enhanced Input injection after opening event; no teleport/forced movement; not manual full level traversal'),indent=2))
 S.update(phase='finish',finish=time.monotonic())
def tick(dt):
 global pawn
 try:
  now=time.monotonic()
  if S['phase']=='finish':
   if now-S['finish']>4:u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
   return
  if now-S['start']>300:raise RuntimeError('PIE timed out: '+S['phase'])
  w=E.get_game_world()
  if not w:return
  pawn=u.GameplayStatics.get_player_character(w,0);pc=u.GameplayStatics.get_player_controller(w,0)
  if not pawn or not pc:return
  if S['phase']=='boot':
   ev=next((x for x in u.ObjectIterator(u.SceneEventSubsystem) if x.get_outer()==w),None)
   if not ev:return
   runner=ev.get_editor_property('active_player')
   if runner:
    if runner.is_waiting_for_choice():
     choices=['Slit','Inside'];choice=choices[min(len(S['choices']),1)]
     assert runner.select_dialogue_choice(choice);S['choices'].append(choice)
    elif runner.is_waiting_for_dialogue():runner.advance_dialogue()
    return
   stage=u.GameplayStatics.get_actor_of_class(w,u.SchoolOpeningSceneActor)
   if not stage or not stage.get_editor_property('completed') or pc.is_move_input_ignored():return
   (O/'player.json').write_text(json.dumps(dict(player=pawn.get_class().get_path_name(),location=vec(pawn.get_actor_location()),view_target=pc.get_view_target().get_name(),opening_complete=True)))
   for command in ['t.MaxFPS 0','r.VSync 0','r.GPUCsvStatsEnabled 1']:u.SystemLibrary.execute_console_command(pawn,command)
   S.update(phase='warmup',at=now);return
  if S['phase']=='warmup':
   if now-S['at']<10:return
   name=phases[S['i']];u.SystemLibrary.execute_console_command(pawn,'csvprofile STARTFILE=S0PIEPerformance_'+name+'.csv');u.SystemLibrary.execute_console_command(pawn,'csvprofile START')
   S.update(phase='record',at=now,recording=True);(O/'phase.json').write_text(json.dumps(dict(phase=name)));return
  if S['phase']=='record':
   name=phases[S['i']];pos=pawn.get_actor_location()
   if name=='walk':
    target=waypoints[S['waypoint']];dx=target[0]-pos.x;dy=target[1]-pos.y
    if math.hypot(dx,dy)<70:S['waypoint']=1-S['waypoint']
    else:
     assert not pc.is_move_input_ignored()
     pc.set_control_rotation(u.Rotator(yaw=math.degrees(math.atan2(dy,dx))))
     assert u.CarryEditorLibrary.inject_carry_review_input('/Game/Constellation/Input/IA_Move',u.Vector(0,1,0))
   if now-S['last_sample']>.1:
    S['samples'].append(dict(phase=name,t=now-S['at'],pos=vec(pos),velocity=vec(pawn.get_velocity()),ignored=pc.is_move_input_ignored()));S['last_sample']=now
   if now-S['at']>=20:
    u.SystemLibrary.execute_console_command(pawn,'csvprofile STOP');S['recording']=False
    u.CarryEditorLibrary.capture_carry_review(str(O/(name+'.png')),False)
    S['i']+=1
    if S['i']==len(phases):finish();return
    S.update(phase='warmup',at=now)
 except:finish(traceback.format_exc())
u.EditorPythonScripting.set_keep_python_script_alive(True);handle=u.register_slate_post_tick_callback(tick);L.editor_request_begin_play()
