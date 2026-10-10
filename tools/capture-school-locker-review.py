"""Unreal rendered comparison in an unsaved world. Does not replace gameplay assets."""
import unreal as u,time,json
from pathlib import Path
R=Path(u.Paths.project_dir()).resolve();O=R/'ArtSource/SchoolLocker/Review';A=u.get_editor_subsystem(u.EditorActorSubsystem)
u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
D='/Game/Constellation/Review/SchoolLocker';aa=A.get_all_level_actors();by={a.get_actor_label():a for a in aa}
for a in aa:
 for c in a.get_components_by_class(u.StaticMeshComponent):
  if c.static_mesh and c.static_mesh.get_name() in ['SM_Locker','SM_Locker_Body','SM_Locker_Door']:
   c.set_static_mesh(u.load_asset(D+'/Meshes/'+c.static_mesh.get_name()));c.set_editor_property('override_materials',[])
for label,pos,scale in [('S0_MemoryPhoto',(3154,-48,229),(.14,.18,1)),('S0_StarCard',(3154,48,225),(.12,.18,1)),('S0_Note',(3154,48,203),(.095,.095,1))]:
 a=by[label];a.set_actor_location(u.Vector(*pos),False,True);a.set_actor_scale3d(u.Vector(*scale))
for a in aa:
 if a.get_actor_label().startswith('S0_Charm_'):
  p=a.get_actor_location();p.y-=49;p.z+=41;a.set_actor_location(p,False,True);a.set_actor_scale3d(a.get_actor_scale3d()*.6)
by['S0_InteriorFill'].point_light_component.set_intensity(.025)
spot=A.spawn_actor_from_class(u.SpotLight,u.Vector(3142,0,219),u.Rotator(pitch=-20,yaw=0),transient=True);spot.spot_light_component.set_mobility(u.ComponentMobility.MOVABLE);spot.spot_light_component.set_intensity(.4);spot.spot_light_component.set_attenuation_radius(180);spot.spot_light_component.set_inner_cone_angle(25);spot.spot_light_component.set_outer_cone_angle(45);spot.spot_light_component.set_light_color(u.LinearColor(1,.69,.36))
# Remove emissive fill from narrative props in this unsaved review.
for name in ['M_MemoryPhoto_Draft','M_ConstellationCard','M_StarNote','M_CharmCream','M_CharmPink','M_CharmGold']:
 m=u.load_asset('/Game/SceneDirector/School/S0/'+name)
 for ex in u.ObjectIterator(u.MaterialExpressionMultiply):
  if ex.get_outer()==m:ex.set_editor_property('const_b',0)
 u.MaterialEditingLibrary.recompile_material(m)
cam=A.spawn_actor_from_class(u.CameraActor,u.Vector(3203,0,214),u.Rotator(yaw=180),transient=True);cam.camera_component.set_field_of_view(115);u.EditorLevelLibrary.pilot_level_actor(cam);u.EditorLevelLibrary.editor_set_game_view(True)
shots=[('locker-inside-r3',(3203,0,214),u.Rotator(yaw=180),115),('locker-vent-r3',(3165,0,214.6),u.Rotator(yaw=180),75),('locker-outside-r3',(2830,220,190),u.Rotator(yaw=-33,pitch=-7),65)]
u.EditorPythonScripting.set_keep_python_script_alive(True);S={'i':0,'sent':False,'t':time.monotonic(),'start':time.monotonic()}
def tick(dt):
 if time.monotonic()-S['start']>240 or S['i']>=len(shots):u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor();return
 name,pos,rot,fov=shots[S['i']];p=O/(name+'.png')
 if S['sent']:
  if p.exists():S['i']+=1;S['sent']=False;S['t']=time.monotonic()
  return
 cam.set_actor_location(u.Vector(*pos),False,True);cam.set_actor_rotation(rot,False);cam.camera_component.set_field_of_view(fov)
 if time.monotonic()-S['t']>10:u.AutomationLibrary.take_high_res_screenshot(1536,864,str(p),camera=cam,delay=1);S['sent']=True
handle=u.register_slate_post_tick_callback(tick)
