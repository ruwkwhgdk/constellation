import unreal as u,json,time,traceback
from pathlib import Path
P=Path(__file__).resolve().parent
OUT=P/'Preview';OUT.mkdir(exist_ok=True)
B='/Game/Constellation/Characters/Enemies/Slime_Liquid'
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
level=u.get_editor_subsystem(u.LevelEditorSubsystem)
world=u.EditorLoadingAndSavingUtils.new_blank_map(False)
mesh=u.load_asset(B+'/SKM_Slime_Liquid');idle=u.load_asset(B+'/AS_Slime_Liquid_Idle')
slime=actors.spawn_actor_from_class(u.SkeletalMeshActor,u.Vector(0,0,84.3279))
slime.set_actor_label('Liquid Slime')
c=slime.skeletal_mesh_component;c.set_skeletal_mesh_asset(mesh)
c.override_animation_data(idle,False,False,1.5,1)
c.set_update_animation_in_editor(True)
c.set_editor_property('visibility_based_anim_tick_option',u.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
floor=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,-5));floor.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cube'));floor.set_actor_scale3d(u.Vector(30,30,.1))
for pos,rot,intensity in [(u.Vector(150,150,300),u.Rotator(-45,-130,0),5)]:
 light=actors.spawn_actor_from_class(u.DirectionalLight,pos,rot);light.light_component.set_mobility(u.ComponentMobility.MOVABLE);light.light_component.set_intensity(intensity)
sky=actors.spawn_actor_from_class(u.SkyLight,u.Vector(0,0,300));sky.light_component.set_mobility(u.ComponentMobility.MOVABLE);sky.light_component.set_editor_property('intensity',1.0);sky.light_component.set_editor_property('lower_hemisphere_is_black',False)
sky.light_component.set_editor_property('source_type',u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
sky.light_component.set_editor_property('cubemap',u.load_asset('/Engine/EditorMaterials/AssetViewer/EpicQuadPanorama_CC+EV1'))
for pos,power in [(u.Vector(180,200,240),12000),(u.Vector(-200,70,180),8000)]:
 light=actors.spawn_actor_from_class(u.PointLight,pos);light.light_component.set_mobility(u.ComponentMobility.MOVABLE);light.light_component.set_intensity(power);light.light_component.set_editor_property('attenuation_radius',650);light.light_component.set_editor_property('source_radius',40)
pos=u.Vector(280,500,210);rot=u.MathLibrary.find_look_at_rotation(pos,u.Vector(0,0,78))
cam=actors.spawn_actor_from_class(u.CameraActor,pos,rot);cam.camera_component.set_field_of_view(38)
cam.set_actor_label('Slime Review Camera')
u.EditorLevelLibrary.set_level_viewport_camera_info(pos,rot)
pp=cam.camera_component.get_editor_property('post_process_settings');pp.set_editor_property('override_auto_exposure_method',True);pp.set_editor_property('auto_exposure_method',u.AutoExposureMethod.AEM_MANUAL);pp.set_editor_property('override_auto_exposure_bias',True);pp.set_editor_property('auto_exposure_bias',2);cam.camera_component.set_editor_property('post_process_settings',pp)
capture=actors.spawn_actor_from_class(u.SceneCapture2D,pos,rot);capture.set_actor_label('Slime Review Capture')
capture.capture_component2d.set_editor_property('fov_angle',38)
capture.capture_component2d.set_editor_property('post_process_settings',pp)
capture.capture_component2d.set_editor_property('capture_source',u.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
u.EditorLoadingAndSavingUtils.save_map(world,'/Game/Constellation/Review/Slime/L_Slime_Liquid')
state={'start':time.monotonic(),'captured':False}
def tick(dt):
 try:
  if time.monotonic()-state['start']>20 and not state['captured']:
   state['captured']=True
   u.AutomationLibrary.take_high_res_screenshot(800,720,str(OUT/'unreal-gel.png'),camera=cam)
  if time.monotonic()-state['start']>25:
   (P/'preview-report.json').write_text(json.dumps({'mesh':mesh.get_path_name(),'center':str(c.get_socket_location('Center')),'top':str(c.get_socket_location('Top')),'drop':str(c.get_socket_location('drop')),'bounds':str(slime.get_actor_bounds(False))},indent=2))
   u.unregister_slate_post_tick_callback(handle)
 except Exception:
  (P/'preview-error.txt').write_text(traceback.format_exc());u.unregister_slate_post_tick_callback(handle)
handle=u.register_slate_post_tick_callback(tick)
