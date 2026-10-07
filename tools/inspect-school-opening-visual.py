import unreal as u,json,time
from pathlib import Path
O=Path(u.Paths.project_dir())/'Saved/S0Opening';A=u.get_editor_subsystem(u.EditorActorSubsystem)
w=u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
rows=[]
for a in A.get_all_level_actors():
 p=a.get_actor_location()
 if 1400<p.x<3600 and abs(p.y)<1000 and -300<p.z<500:
  rows.append({'name':a.get_name(),'label':a.get_actor_label(),'pos':[p.x,p.y,p.z],'class':a.get_class().get_name()})
(O/'nearby.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
report={}
for label,path in [('girl','/Game/Constellation/Characters/NPC/Blueprints/BP_NPC_Little_Girl'),('hero','/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine')]:
 c=u.load_class(None,path+'.'+path.split('/')[-1]+'_C');a=A.spawn_actor_from_class(c,u.Vector(0,0,-10000),transient=True)
 comps=a.get_components_by_class(u.SkeletalMeshComponent);items=[]
 for s in comps:
  mesh=s.get_skeletal_mesh_asset()
  if not mesh:continue
  items.append({'component':s.get_name(),'mesh':mesh.get_path_name(),'skeleton':mesh.get_editor_property('skeleton').get_path_name(),'scale':str(s.get_editor_property('relative_scale3d')),'bones':[str(s.get_bone_name(i)) for i in range(s.get_num_bones())],'anim':str(s.get_editor_property('animation_data'))})
 report[label]=items;A.destroy_actor(a)
for key in ['SM_Locker_Body','SM_Locker_Door']:
 m=u.load_asset('/Game/Constellation/Environments/School/Props/SM_Locker/'+key);report[key]=str(m.get_bounding_box())
(O/'rigs.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
cam=A.spawn_actor_from_class(u.CameraActor,u.Vector(2800,360,190),u.Rotator(pitch=-5,yaw=20,roll=0),transient=True);cam.camera_component.set_field_of_view(75)
u.EditorLevelLibrary.set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation());u.EditorLevelLibrary.pilot_level_actor(cam)
u.EditorPythonScripting.set_keep_python_script_alive(True)
start=time.time();sent=False
def tick(dt):
 global sent
 if time.time()-start>12 and not sent:
  u.AutomationLibrary.take_high_res_screenshot(1280,720,str(O/'start-room.png'),camera=cam,delay=1);sent=True
 if time.time()-start>24:
  u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(tick)
