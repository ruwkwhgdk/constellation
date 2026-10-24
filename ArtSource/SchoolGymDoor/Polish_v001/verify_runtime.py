import unreal as u,json,time,traceback,hashlib
from pathlib import Path
P=Path(u.Paths.project_dir())/'ArtSource/SchoolGymDoor/Polish_v001'
B='/Game/Constellation/Environments/School/Blueprints/BP_School_Gate';S='/Game/Constellation/Environments/School/Sets/GymCorridor/SM_GymDoorLeaf'
A=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem);UE=u.get_editor_subsystem(u.UnrealEditorSubsystem)
bp=u.load_asset(B);mesh=u.load_asset(S)
graph=u.ResourceRecoveryLibrary.export_blueprint_graphs(bp)
(P/'Reports/graphs-reloaded.txt').write_text(graph,encoding='utf8')
def normalize_graph(s):return '\n'.join(x.strip() for x in s.splitlines() if x.strip())
assert normalize_graph(graph)==normalize_graph((P/'Reports/graphs-before.txt').read_text(encoding='utf8')),'Saved graph mismatch'
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
rows=[];target=None
for a in A.get_all_level_actors():
 if a.get_class()!=bp.generated_class():continue
 comps=a.get_components_by_class(u.StaticMeshComponent)
 for c in comps:
  assert c.static_mesh==mesh,(a.get_actor_label(),c.get_name(),str(c.static_mesh))
  assert c.get_material(0).get_name()=='MI_GymDoor_Navy',(a.get_actor_label(),str(c.get_material(0)))
 rows.append({'actor':a.get_actor_label(),'mesh':mesh.get_path_name(),'materials':[c.get_material(0).get_path_name() for c in comps]})
 if a.get_actor_label()=='gate3':target=a
assert len(rows)==3,rows
assert target
loc=target.get_actor_location();pos=loc-target.get_actor_forward_vector()*1900+u.Vector(0,0,350);aim=loc+u.Vector(0,0,228)
cam=A.spawn_actor_from_class(u.CameraActor,pos,u.MathLibrary.find_look_at_rotation(pos,aim),transient=True);cam.camera_component.set_field_of_view(45)
u.EditorLevelLibrary.pilot_level_actor(cam);u.EditorLevelLibrary.editor_set_game_view(True)
state={'phase':'map','start':time.monotonic(),'phase_time':time.monotonic(),'map_instances':rows}
u.EditorPythonScripting.set_keep_python_script_alive(True)
def phase(p):state['phase']=p;state['phase_time']=time.monotonic()
def finish(ok,error=''):
 state['passed']=ok;state['error']=error
 (P/'Reports/saved-runtime-verification.json').write_text(json.dumps(state,indent=2))
 u.unregister_slate_post_tick_callback(handle)
 if L.is_in_play_in_editor():L.editor_request_end_play()
 u.EditorPythonScripting.set_keep_python_script_alive(False);u.SystemLibrary.quit_editor()
def angles(a):return {c.get_name():c.get_editor_property('relative_rotation').yaw for c in a.get_components_by_class(u.StaticMeshComponent)}
def doorway_hit(w):
 hit=u.SystemLibrary.line_trace_single(w,u.Vector(-200,60,350),u.Vector(200,60,350),u.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[],u.DrawDebugTrace.NONE,True)
 return bool(hit)
def tick(dt):
 try:
  elapsed=time.monotonic()-state['phase_time']
  if time.monotonic()-state['start']>180:raise RuntimeError('Verification timeout '+state['phase'])
  if state['phase']=='map' and elapsed>20:
   u.AutomationLibrary.take_high_res_screenshot(1280,960,str(P/'Reports/in-map.png'),camera=cam,delay=1);phase('map_capture')
  elif state['phase']=='map_capture' and elapsed>5 and (P/'Reports/in-map.png').exists():
   phase('scratch_setup')
   # Isolate the interaction test from story triggers and player save state.
   w=u.EditorLoadingAndSavingUtils.new_blank_map(False);w.get_world_settings().set_editor_property('default_game_mode',u.GameModeBase)
   a=A.spawn_actor_from_class(bp.generated_class(),u.Vector(0,0,300));a.set_actor_label('GymDoorRuntimeTest')
   phase('pie_wait');L.editor_request_begin_play()
  elif state['phase']=='pie_wait':
   w=UE.get_game_world()
   if not w or elapsed<2:return
   actors=u.GameplayStatics.get_all_actors_of_class(w,bp.generated_class())
   if not actors:return
   a=actors[0];state['closed_angles']=angles(a)
   state['closed_trace_hit']=doorway_hit(w)
   phase('opening');a.call_method('Interact',args=(u.GameplayStatics.get_player_pawn(w,0),a.get_component_by_class(u.StaticMeshComponent)))
  elif state['phase']=='opening':
   w=UE.get_game_world();a=u.GameplayStatics.get_all_actors_of_class(w,bp.generated_class())[0]
   if elapsed>2 and 'mid_angles' not in state:state['mid_angles']=angles(a)
   if elapsed>7:
    state['open_angles']=angles(a)
    assert all(abs(v-90)<.1 for v in state['open_angles'].values()),state['open_angles']
    assert any(abs(state['mid_angles'][k]-state['closed_angles'][k])>1 for k in state['mid_angles']),state
    state['runtime_meshes']=[c.static_mesh.get_path_name() for c in a.get_components_by_class(u.StaticMeshComponent)]
    state['open_trace_hit']=doorway_hit(w)
    assert state['closed_trace_hit'] and not state['open_trace_hit'],'Door collision did not clear after opening'
    assert all(c.static_mesh==mesh for c in a.get_components_by_class(u.StaticMeshComponent))
    finish(True)
 except Exception:finish(False,traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick)

