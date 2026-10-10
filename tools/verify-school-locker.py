"""Reload final gameplay assets, verify shared materials/collisions and capture real saved-map views."""
import unreal as u,time,json
from pathlib import Path
R=Path(u.Paths.project_dir()).resolve();O=R/'ArtSource/SchoolLocker/Review';A=u.get_editor_subsystem(u.EditorActorSubsystem);E=u.EditorAssetLibrary;M=u.MaterialEditingLibrary
u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
base='/Game/Constellation/Environments/School/Props/SM_Locker/';master=u.load_asset('/Game/Constellation/MaterialLibrary/Materials/M_Base_PBR');SSE=u.get_editor_subsystem(u.StaticMeshEditorSubsystem);checks=[]
for n,hulls in [('SM_Locker',1),('SM_Locker_Body',6),('SM_Locker_Door',1)]:
 mesh=u.load_asset(base+n);assert mesh
 slots=mesh.get_editor_property('static_materials');assert len(slots)>=3
 for slot in slots:
  mat=slot.material_interface;assert isinstance(mat,u.MaterialInstanceConstant),(n,str(mat));assert mat.get_editor_property('parent')==master,(n,str(mat.get_editor_property('parent')))
  for p in ['BaseColor','Roughness','Metalic','Normal']:assert M.get_material_instance_texture_parameter_value(mat,p),(n,p)
 count=SSE.get_simple_collision_count(mesh)+SSE.get_convex_collision_count(mesh);assert count>=hulls,(n,count,hulls)
 b=mesh.get_bounding_box();checks.append({'mesh':n,'materials':[str(s.material_interface.get_path_name()) for s in slots],'hulls':count,'bounds':str(b)})
# Fresh BP instances ensure both closed and open variants resolve the replaced resources.
for n in ['BP_School_Locker','BP_School_Locker_Open']:
 path='/Game/Constellation/Environments/School/Blueprints/'+n;actor=A.spawn_actor_from_class(u.load_class(None,path+'.'+n+'_C'),u.Vector(0,0,-10000),transient=True)
 for c in actor.get_components_by_class(u.StaticMeshComponent):
  for i in range(c.get_num_materials()):assert c.get_material(i).get_editor_property('parent')==master,(n,i)
 A.destroy_actor(actor)
(O/'saved-verification.json').write_text(json.dumps({'success':True,'master':master.get_path_name(),'meshes':checks,'bp_variants':2},indent=2));u.log('LOCKER_SAVED_VERIFY_PASS')
cam=A.spawn_actor_from_class(u.CameraActor,u.Vector(3203,0,214.6),u.Rotator(yaw=180),transient=True);cam.camera_component.set_field_of_view(115);u.EditorLevelLibrary.pilot_level_actor(cam);u.EditorLevelLibrary.editor_set_game_view(True)
shots=[('locker-final-inside',(3203,0,214.6),u.Rotator(yaw=180),115),('locker-final-vent',(3165,0,214.6),u.Rotator(yaw=180),115),('locker-final-outside',(2830,220,190),u.Rotator(yaw=-33,pitch=-7),65),('locker-final-open',(2840,220,185),u.Rotator(yaw=-32,pitch=-7),65)]
u.EditorPythonScripting.set_keep_python_script_alive(True);S={'i':0,'sent':False,'t':time.monotonic(),'start':time.monotonic(),'wall_start':time.time()}
def tick(dt):
 if time.monotonic()-S['start']>240 or S['i']>=len(shots):u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor();return
 name,pos,rot,fov=shots[S['i']];p=O/(name+'-uvfixed.png')
 if S['sent']:
  if p.exists() and p.stat().st_mtime>S['wall_start']:S['i']+=1;S['sent']=False;S['t']=time.monotonic()
  return
 if name.endswith('-open'):
  door=next(a for a in A.get_all_level_actors() if a.get_actor_label()=='S0_LockerDoor');door.set_actor_rotation(u.Rotator(yaw=-15),False)
 cam.set_actor_location(u.Vector(*pos),False,True);cam.set_actor_rotation(rot,False);cam.camera_component.set_field_of_view(fov)
 if time.monotonic()-S['t']>9:u.AutomationLibrary.take_high_res_screenshot(1536,864,str(p),camera=cam,delay=1);S['sent']=True
handle=u.register_slate_post_tick_callback(tick)
