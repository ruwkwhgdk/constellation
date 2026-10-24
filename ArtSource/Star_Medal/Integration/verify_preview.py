import unreal as u,json,time
from pathlib import Path
P=Path(u.Paths.project_dir())/'ArtSource/Star_Medal/Integration'
B='/Game/Constellation/Gameplay/Interaction/Actors/BP_CollectableItem_StarCoin'
D='/Game/Constellation/Environments/Shared/Props/Star_Medal'
bp=u.load_asset(B);mesh=u.load_asset(D+'/SM_Star_Medal');mi=u.load_asset(D+'/MI_Star_Medal')
A=u.get_editor_subsystem(u.EditorActorSubsystem)
world=u.EditorLoadingAndSavingUtils.new_blank_map(False)
actor=A.spawn_actor_from_class(bp.generated_class(),u.Vector(0,0,65))
c=actor.get_component_by_class(u.StaticMeshComponent)
assert c.static_mesh==mesh,c.static_mesh
assert c.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION
assert abs(c.get_relative_transform().scale3d.z-.5)<.0001
assert all(s.material_interface==mi for s in mesh.static_materials)
M=u.MaterialEditingLibrary
for param,suffix in [('BaseColor','BaseColor'),('Normal','Normal'),('Roughness','Roughness'),('Metalic','Metallic')]:
 assert M.get_material_instance_texture_parameter_value(mi,param)==u.load_asset(D+'/T_Star_Medal_'+suffix)
gold=u.load_asset('/Game/Constellation/Gameplay/Interaction/Actors/BP_CollectableItem_Gold')
gold_actor=A.spawn_actor_from_class(gold.generated_class(),u.Vector(0,0,-10000))
gold_mesh=gold_actor.get_component_by_class(u.StaticMeshComponent).static_mesh
assert gold_mesh!=mesh
A.destroy_actor(gold_actor)
report={'passed':True,'spawned_star_coin_mesh':c.static_mesh.get_path_name(),'transform':str(c.get_relative_transform()),'collision':str(c.get_collision_enabled()),'gold_mesh':gold_mesh.get_path_name(),'components':[{'class':x.get_class().get_name(),'name':x.get_name()} for x in actor.get_components_by_class(u.ActorComponent)],'material_parameters_verified':True,'bounds':str(mesh.get_bounding_box())}
(P/'verification.json').write_text(json.dumps(report,indent=2))
# Two views in an unsaved scratch world; no project map is modified.
actor.set_actor_location(u.Vector(-65,0,65),False,False)
back=A.spawn_actor_from_class(bp.generated_class(),u.Vector(65,0,65),u.Rotator(yaw=180))
floor=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,-5));floor.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cube'));floor.set_actor_scale3d(u.Vector(20,20,.1))
light=A.spawn_actor_from_class(u.DirectionalLight,u.Vector(100,-200,300),u.Rotator(-45,70,0));light.light_component.set_mobility(u.ComponentMobility.MOVABLE);light.light_component.set_intensity(5)
sky=A.spawn_actor_from_class(u.SkyLight,u.Vector(0,0,300));sky.light_component.set_mobility(u.ComponentMobility.MOVABLE);sky.light_component.set_editor_property('intensity',1.2);sky.light_component.set_editor_property('lower_hemisphere_is_black',False);sky.light_component.set_editor_property('source_type',u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP);sky.light_component.set_editor_property('cubemap',u.load_asset('/Engine/EditorMaterials/AssetViewer/EpicQuadPanorama_CC+EV1'))
pos=u.Vector(15,-420,145);rot=u.MathLibrary.find_look_at_rotation(pos,u.Vector(0,0,65))
cam=A.spawn_actor_from_class(u.CameraActor,pos,rot);cam.camera_component.set_field_of_view(40)
u.EditorLevelLibrary.pilot_level_actor(cam);u.EditorLevelLibrary.editor_set_game_view(True)
u.EditorPythonScripting.set_keep_python_script_alive(True);start=time.monotonic();sent=False
def tick(dt):
 global sent
 if not sent and time.monotonic()-start>20:
  u.AutomationLibrary.take_high_res_screenshot(1280,800,str(P/'preview.png'),camera=cam,delay=1);sent=True
 if (sent and (P/'preview.png').exists()) or time.monotonic()-start>100:
  u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.execute_console_command(None,'QUIT')
handle=u.register_slate_post_tick_callback(tick)
