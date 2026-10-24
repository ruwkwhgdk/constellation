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
state={'phase':'after','start':time.monotonic(),'time':time.monotonic()}
def phase(p):state['phase']=p;state['time']=time.monotonic()
def shot(name):u.AutomationLibrary.take_high_res_screenshot(1280,960,str(P/'Reports'/name),camera=cam,delay=1)
def finish():
 u.unregister_slate_post_tick_callback(handle);u.EditorPythonScripting.set_keep_python_script_alive(False);u.SystemLibrary.quit_editor()
def tick(dt):
 try:
  elapsed=time.monotonic()-state['time']
  if time.monotonic()-state['start']>240:raise RuntimeError('Review timeout '+state['phase'])
  if state['phase']=='before' and elapsed>15:shot('before.png');phase('before_capture')
  elif state['phase']=='before_capture' and elapsed>4 and (P/'Reports/before.png').exists():
   phase('applying')
   exec(compile((P/'apply_polish.py').read_text(),str(P/'apply_polish.py'),'exec'),{'__file__':str(P/'apply_polish.py')});phase('after')
  elif state['phase']=='after' and elapsed>25:shot('after.png');phase('after_capture')
  elif state['phase']=='after_capture' and elapsed>4 and (P/'Reports/after.png').exists():
   # Preview the unchanged hinge rotations at the existing fully open angles.
   for c in actor.get_components_by_class(u.StaticMeshComponent):c.set_relative_rotation(u.Rotator(yaw=90),False,False)
   phase('open')
  elif state['phase']=='open' and elapsed>3:shot('open.png');phase('open_capture')
  elif state['phase']=='open_capture' and elapsed>4 and (P/'Reports/open.png').exists():
   finish()
 except Exception:
  (P/'Reports/review-error.txt').write_text(traceback.format_exc());finish()
handle=u.register_slate_post_tick_callback(tick)
