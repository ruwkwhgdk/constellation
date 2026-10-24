import unreal as u,json,time,traceback
from pathlib import Path
P=Path(u.Paths.project_dir())/'ArtSource/SchoolGymDoor/Polish_v001'
B='/Game/Constellation/Environments/School/Blueprints/BP_School_Gate'
S='/Game/Constellation/Environments/School/Sets/GymCorridor/SM_GymDoorLeaf'
A=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
w=u.EditorLoadingAndSavingUtils.new_blank_map(False)
w.get_world_settings().set_editor_property('default_game_mode',u.GameModeBase)
bp=u.load_asset(B);mesh=u.load_asset(S)
actor=A.spawn_actor_from_class(bp.generated_class(),u.Vector(0,0,50));actor.set_actor_scale3d(u.Vector(1.5,1.833333,1));actor.set_actor_label('GymDoorPolishReview')
for c in actor.get_components_by_class(u.StaticMeshComponent):c.set_static_mesh(mesh);c.set_editor_property('override_materials',[])
for c in actor.get_components_by_class(u.TextRenderComponent):c.set_visibility(False)
floor=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,-5));floor.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cube'));floor.set_actor_scale3d(u.Vector(20,20,.1))
light=A.spawn_actor_from_class(u.DirectionalLight,u.Vector(-200,-100,300),u.Rotator(pitch=-35,yaw=25));light.light_component.set_mobility(u.ComponentMobility.MOVABLE);light.light_component.set_intensity(4)
sky=A.spawn_actor_from_class(u.SkyLight,u.Vector(0,0,300));sky.light_component.set_mobility(u.ComponentMobility.MOVABLE);sky.light_component.set_editor_property('intensity',1.1);sky.light_component.set_editor_property('lower_hemisphere_is_black',False);sky.light_component.set_editor_property('source_type',u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP);sky.light_component.set_editor_property('cubemap',u.load_asset('/Engine/EditorMaterials/AssetViewer/EpicQuadPanorama_CC+EV1'))
pos=u.Vector(-650,-35,160);rot=u.MathLibrary.find_look_at_rotation(pos,u.Vector(0,0,125))
cam=A.spawn_actor_from_class(u.CameraActor,pos,rot);cam.camera_component.set_field_of_view(40);u.EditorLevelLibrary.pilot_level_actor(cam);u.EditorLevelLibrary.editor_set_game_view(True)
u.EditorPythonScripting.set_keep_python_script_alive(True)

UE=u.get_editor_subsystem(u.UnrealEditorSubsystem)
state={'phase':'capture','start':time.monotonic(),'phase_time':time.monotonic()}
def phase(p):state['phase']=p;state['phase_time']=time.monotonic()
def finish(ok,error=''):
 state['passed']=ok;state['error']=error
 (P/'Reports/runtime-final.json').write_text(json.dumps(state,indent=2))
 u.unregister_slate_post_tick_callback(handle)
 if L.is_in_play_in_editor():L.editor_request_end_play()
 u.EditorPythonScripting.set_keep_python_script_alive(False);u.SystemLibrary.quit_editor()
def angles(a):return {c.get_name():c.get_editor_property('relative_rotation').yaw for c in a.get_components_by_class(u.StaticMeshComponent)}
def trace(w):
 h=u.SystemLibrary.line_trace_single(w,u.Vector(-200,60,350),u.Vector(200,60,350),u.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[],u.DrawDebugTrace.NONE,True)
 return bool(h)
def tick(dt):
 try:
  elapsed=time.monotonic()-state['phase_time']
  if time.monotonic()-state['start']>120:raise RuntimeError('Timeout '+state['phase'])
  if state['phase']=='capture' and elapsed>20:
   phase('capture_wait');u.AutomationLibrary.take_high_res_screenshot(1280,960,str(P/'Reports/after-final.png'),camera=cam,delay=1)
  elif state['phase']=='capture_wait' and elapsed>5 and (P/'Reports/after-final.png').exists():
   phase('setup')
   # Fresh instance at unit scale makes collision and hinge checks independent of the review layout.
   A.destroy_actor(actor)
   test=A.spawn_actor_from_class(bp.generated_class(),u.Vector(0,0,300));test.set_actor_label('GymDoorRuntimeTest')
   phase('pie_wait');L.editor_request_begin_play()
  elif state['phase']=='pie_wait':
   w=UE.get_game_world()
   if not w or elapsed<2:return
   aa=u.GameplayStatics.get_all_actors_of_class(w,bp.generated_class())
   if not aa:return
   a=aa[0];state['closed_angles']=angles(a);state['closed_trace_hit']=trace(w)
   phase('opening');a.call_method('Interact',args=(u.GameplayStatics.get_player_pawn(w,0),a.get_component_by_class(u.StaticMeshComponent)))
  elif state['phase']=='opening':
   w=UE.get_game_world();a=u.GameplayStatics.get_all_actors_of_class(w,bp.generated_class())[0]
   if elapsed>2 and 'mid_angles' not in state:state['mid_angles']=angles(a)
   if elapsed>7:
    state['open_angles']=angles(a);state['open_trace_hit']=trace(w)
    state['runtime_meshes']=[c.static_mesh.get_path_name() for c in a.get_components_by_class(u.StaticMeshComponent)]
    assert all(abs(v-90)<.1 for v in state['open_angles'].values()),state['open_angles']
    assert any(abs(state['mid_angles'][k]-state['closed_angles'][k])>1 for k in state['mid_angles'])
    assert state['closed_trace_hit'] and not state['open_trace_hit'],'Door passage collision did not clear'
    assert all(c.static_mesh==mesh for c in a.get_components_by_class(u.StaticMeshComponent))
    finish(True)
 except Exception:finish(False,traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick)


