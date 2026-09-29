import unreal, json, time, traceback
from pathlib import Path
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
P=Path(__file__).resolve().parent
# Temporary, bounded bridge for this preview validation session only.
bridge_started=time.time();bridge_seen=(P/'preview_update.py').stat().st_mtime if (P/'preview_update.py').exists() else 0
def preview_bridge(delta):
 global bridge_seen
 if time.time()-bridge_started>1800:
  unreal.unregister_slate_post_tick_callback(bridge_handle);return
 request=P/'preview_update.py'
 if request.exists() and request.stat().st_mtime>bridge_seen:
  bridge_seen=request.stat().st_mtime
  try:exec(compile(request.read_text(encoding='utf-8-sig'),str(request),'exec'),globals())
  except Exception:(P/'preview_update_error.txt').write_text(traceback.format_exc())
bridge_handle=unreal.register_slate_post_tick_callback(preview_bridge)
B='/Game/Resources/Characters/PC/player_heroine_new'
N='player_heroine_new'
level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world=unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
world.get_world_settings().set_editor_property('default_game_mode',unreal.GameModeBase)
level.editor_set_viewport_realtime(True)
mesh=unreal.load_asset(B+'/SK_'+N+'_WalkPreview')
anim=unreal.load_asset(B+'/Animations/AS_'+N+'_Walk_Timid')
hero=actors.spawn_actor_from_class(unreal.SkeletalMeshActor,unreal.Vector(0,0,0))
hero.set_actor_label('player_heroine_new — Timid walk preview')
comp=hero.skeletal_mesh_component
comp.set_skeletal_mesh_asset(mesh)
comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
comp.override_animation_data(anim,True,True,0.0,1.0)
comp.set_update_animation_in_editor(True)
comp.set_editor_property('visibility_based_anim_tick_option',unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
comp.play_animation(anim,True)
comp.set_position(0.016,False)
floor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,-5))
floor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
floor.set_actor_scale3d(unreal.Vector(8,8,.1))
floor.set_actor_label('Preview floor')
sun=actors.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,200),unreal.Rotator(-35,-145,0))
sun.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
sun.light_component.set_intensity(300.0)
sky=actors.spawn_actor_from_class(unreal.SkyLight,unreal.Vector(0,0,200))
sky.light_component.set_editor_property('intensity',1.0)
sky.light_component.set_editor_property('lower_hemisphere_is_black',False)
for pos,intensity in [(unreal.Vector(130,-130,170),1500),(unreal.Vector(-100,100,170),1800)]:
 light=actors.spawn_actor_from_class(unreal.PointLight,pos)
 light.light_component.set_intensity(intensity)
 light.light_component.set_editor_property('attenuation_radius',600.0)
 light.light_component.set_editor_property('source_radius',60.0)
campos=unreal.Vector(300,-75,110)
rot=unreal.MathLibrary.find_look_at_rotation(campos,unreal.Vector(0,0,84))
camera=actors.spawn_actor_from_class(unreal.CameraActor,campos,rot)
camera.set_actor_label('Full character camera')
camera.camera_component.set_field_of_view(38)
camera.camera_component.set_editor_property('aspect_ratio',1.0)
camera.camera_component.set_editor_property('constrain_aspect_ratio',True)
settings=camera.camera_component.get_editor_property('post_process_settings')
settings.set_editor_property('override_auto_exposure_method',True)
settings.set_editor_property('auto_exposure_method',unreal.AutoExposureMethod.AEM_MANUAL)
settings.set_editor_property('override_auto_exposure_bias',True)
settings.set_editor_property('auto_exposure_bias',3.0)
camera.camera_component.set_editor_property('post_process_settings',settings)
unreal.EditorLevelLibrary.set_level_viewport_camera_info(campos,rot)
assert unreal.EditorLoadingAndSavingUtils.save_map(world,B+'/Preview/L_'+N+'_Walk_Timid')
unreal.EditorAssetLibrary.sync_browser_to_objects([B+'/Animations/AS_'+N+'_Walk_Timid'])
level.pilot_level_actor(camera)
start=time.time(); state={'capture':False}
def tick(delta):
 try:
  elapsed=time.time()-start
  if elapsed>8 and not state.get('sim_started'):
   state['sim_started']=True;level.editor_play_simulate()
  if elapsed>15 and 'first_foot' not in state:
   game_world=unreal.EditorLevelLibrary.get_game_world()
   test_actors=unreal.GameplayStatics.get_all_actors_of_class(game_world,unreal.SkeletalMeshActor)
   test_comp=next(a.skeletal_mesh_component for a in test_actors if a.skeletal_mesh_component.get_editor_property('skeletal_mesh_asset')==mesh)
   state['test_comp']=test_comp;state['first_foot']=test_comp.get_socket_location('foot_l');state['first_time']=time.time()
  if 'first_foot' in state and time.time()-state['first_time']>.25 and not state.get('verified'):
   p=state['first_foot'];q=state['test_comp'].get_socket_location('foot_l');distance=((p.x-q.x)**2+(p.y-q.y)**2+(p.z-q.z)**2)**.5
   state['verified']=True
   (P/'unreal_live_verification.json').write_text(json.dumps({'pass':distance>.1,'animated_foot_delta_cm':distance,'mode':'Simulate In Editor','mesh':mesh.get_path_name(),'animation':anim.get_path_name()},indent=2))
  if elapsed>30 and not state['capture']:
   state['capture']=True
   unreal.AutomationLibrary.take_high_res_screenshot(1000,1000,str(P/'unreal_walk_timid.png'),camera=camera)
  if elapsed>45:
   helper=unreal.get_default_object(unreal.load_class(None,'/Script/PhysicsToolsets.PhysicsAssetToolset'))
   bodies=helper.call_method('GetBodyNames',args=(mesh.get_editor_property('physics_asset'),))
   (P/'walk_preview_result.json').write_text(json.dumps({'map':B+'/Preview/L_'+N+'_Walk_Timid','physics_bodies':list(bodies),'animation':anim.get_path_name(),'height_cm':mesh.get_bounds().box_extent.z*2,'upperarm_l':str(comp.get_socket_location('upperarm_l')),'head':str(comp.get_socket_location('head')),'asset_source':mesh.get_editor_property('asset_import_data').get_first_filename()},indent=2))
   unreal.unregister_slate_post_tick_callback(handle)
 except Exception:
  (P/'preview_error.txt').write_text(traceback.format_exc())
  unreal.unregister_slate_post_tick_callback(handle)
handle=unreal.register_slate_post_tick_callback(tick)
