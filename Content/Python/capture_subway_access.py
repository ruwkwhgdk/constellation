"""Fresh editor-only render/physics inspection; never starts PIE or saves either map."""
import unreal as u,json,time,traceback
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'ArtSource/SubwayEntrance/Connection/v003';A=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
EXT='/Game/Constellation/Worlds/StartIsland/Maps/L_StartIsland';INT='/Game/Constellation/Worlds/Stairwell/Maps/L_Stairwell_PlayScale2'
shots=[(EXT,'rails',(3900,-19430,10050),(4110,-19280,10100)),(EXT,'rear_closure',(4600,-20800,10550),(3900,-19880,10180)),(EXT,'turn_guide',(3900,-20290,9810),(4220,-20530,9680)),(EXT,'dark_handoff',(4550,-20500,9800),(4900,-20500,9800)),(INT,'interior_guide',(-1000,0,520),(-1500,-260,440)),(INT,'interior_dark',(-1500,-650,520),(-1500,-1000,520))]
report={'play_tested':False,'screenshots':[],'maps':[]};index=0;started=time.time();sent=False;lastmap=None;cam=None;busy=False;probe=None

def prepare():
 global started,sent,lastmap,cam,probe
 path,name,pos,target=shots[index]
 if path!=lastmap:
  assert L.load_level(path);lastmap=path
  d={a.get_actor_label():a for a in A.get_all_level_actors()};assert 'SE_DarkTunnel' in d and 'SE_DarkExposure' in d
  expected='SE_TravelToInterior' if path==EXT else 'SE_TravelToExterior';v=d[expected]
  assert abs(v.get_actor_location().z-(9640 if path==EXT else 360))<.1
  pp=d['SE_DarkExposure'].get_editor_property('post_process');assert not pp.get_editor_property('unbound')
  settings=pp.get_editor_property('settings');assert not settings.get_editor_property('override_auto_exposure_method')
  assert settings.get_editor_property('auto_exposure_bias')==-16
  loc=v.get_actor_location();report['maps'].append(dict(map=path,portal=[loc.x,loc.y,loc.z],dark_exposure_bounded=True,local_exposure_bias=-16))
 w=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
 cam=A.spawn_actor_from_class(u.CameraActor,u.Vector(*pos),u.MathLibrary.find_look_at_rotation(u.Vector(*pos),u.Vector(*target)),transient=True);cam.camera_component.set_field_of_view(70)
 if name in ['dark_handoff','interior_dark']:
  # Static mesh-only lighting probe: no Pawn, controller, animation or BeginPlay.
  cdo=u.get_default_object(u.load_class(None,'/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine.BP_Player_Heroine_C'));source=cdo.get_editor_property('mesh')
  probe=A.spawn_actor_from_class(u.SkeletalMeshActor,u.Vector(*((4750,-20500,9640) if path==EXT else (-1500,-850,360))),transient=True)
  probe.skeletal_mesh_component.set_skeletal_mesh_asset(source.get_skeletal_mesh_asset());probe.set_actor_scale3d(source.get_editor_property('relative_scale3d'))
  for i in range(source.get_num_materials()):probe.skeletal_mesh_component.set_material(i,source.get_material(i))
 u.EditorLevelLibrary.set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation());u.EditorLevelLibrary.pilot_level_actor(cam)
 for cmd in ['r.ScreenPercentage 100','r.AntiAliasingMethod 2','r.TemporalAA.Upsampling 0']:u.SystemLibrary.execute_console_command(w,cmd)
 started=time.time();sent=False

prepare();u.EditorPythonScripting.set_keep_python_script_alive(True)
def tick(dt):
 global index,sent,busy,probe
 if busy:return
 busy=True
 try:
  elapsed=time.time()-started;path,name,pos,target=shots[index]
  if elapsed>22 and not sent:
   if name=='rear_closure':
    w=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    checks=[]
    for x in [3710,3900,4090]:
     h=u.SystemLibrary.line_trace_single(w,u.Vector(x,-20000,10100),u.Vector(x,-19800,10100),u.TraceTypeQuery.ECC_VISIBILITY,False,[],u.DrawDebugTrace.NONE,True)
     assert h and abs(h.to_tuple()[4].y+19930)<2,('rear wall gap',x,str(h))
     checks.append(x)
    rails=[a for a in A.get_all_level_actors() if a.get_actor_label().startswith('SE_KitRail_')]
    assert len(rails)==14,len(rails)
    assert not any(a.get_actor_label()=='SE_E10' for a in A.get_all_level_actors())
    report['rear_wall_blocked_at_x']=checks;report['reused_rail_instances']=len(rails)
   u.AutomationLibrary.take_high_res_screenshot(1600,1000,str(O/(name+'.png')),camera=cam,delay=2);sent=True
  if elapsed>31:
   f=O/(name+'.png');assert f.exists() and f.stat().st_mtime>started,(name,'capture not refreshed')
   report['screenshots'].append(dict(name=name,refreshed=True,static_character_probe=probe is not None));u.EditorLevelLibrary.eject_pilot_level_actor();A.destroy_actor(cam)
   if probe:A.destroy_actor(probe);probe=None
   index+=1
   if index<len(shots):prepare();return
   (O/'fresh_validation.json').write_text(json.dumps(report,indent=2));u.log('SUBWAY_DARK_CAPTURE_OK');u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
 except Exception:
  u.log_error(traceback.format_exc());u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
 finally:busy=False
handle=u.register_slate_post_tick_callback(tick)



