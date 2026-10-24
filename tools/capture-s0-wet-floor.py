import unreal as u,time,json,traceback
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/20261017';O.mkdir(parents=True,exist_ok=True)
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
A=u.get_editor_subsystem(u.EditorActorSubsystem);E=u.EditorAssetLibrary
info={}
for path in ['/Game/Constellation/Environments/School/Sets/MiddleCorridor/M_SchoolFloorWorld','/Game/Constellation/Environments/Cave/Sets/SchoolCave/Pass4/M_DetailedStone','/Game/Constellation/Environments/Cave/Sets/SchoolCave/Pass4/M_ShallowReflectiveWater']:
 m=E.load_asset(path)
 info[path]=[t.get_path_name() for t in u.MaterialEditingLibrary.get_used_textures(m)] if m else []
(O/'textures.json').write_text(json.dumps(info,indent=2))
cam=A.spawn_actor_from_class(u.CameraActor,u.Vector(3050,-2650,1650),u.Rotator(pitch=-25,yaw=130),transient=True)
cam.camera_component.set_field_of_view(83)
u.EditorLevelLibrary.pilot_level_actor(cam);u.EditorLevelLibrary.editor_set_game_view(True)
u.EditorLevelLibrary.set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation())
u.EditorPythonScripting.set_keep_python_script_alive(True)
tag='after' if 'WetAfter' in u.SystemLibrary.get_command_line() else 'before'
if tag=='after':
 baseline=json.loads((O/'actors.json').read_text(encoding='utf8'));by={a.get_name():a for a in A.get_all_level_actors()};errors=[];checked=0
 removed={'ART_SchoolCave_Puddle%02d'%i for i in range(1,5)}
 floors={'classroom_start_floor_'+str(i) for i in range(1,9)}
 for row in baseline:
  if row['label'] in removed:continue
  a=by.get(row['name'])
  if not a:errors.append('Missing '+row['label']);continue
  p=a.get_actor_location();s=a.get_actor_scale3d()
  if max(abs(v-b) for v,b in zip([p.x,p.y,p.z],row['pos']))>.01:errors.append('Moved '+row['label'])
  if max(abs(v-b) for v,b in zip([s.x,s.y,s.z],row['scale']))>.001:errors.append('Scaled '+row['label'])
  comps={c.get_name():c for c in a.get_components_by_class(u.StaticMeshComponent)}
  for r in row['meshes']:
   c=comps.get(r['name'])
   if not c:errors.append('Missing component '+row['label']);continue
   if (c.static_mesh.get_path_name() if c.static_mesh else '')!=r['mesh']:errors.append('Changed mesh '+row['label'])
   mats=[m.get_path_name() if m else '' for m in c.get_materials()]
   if row['label'] not in floors and mats!=r['materials']:errors.append('Changed material '+row['label'])
  checked+=1
 water=next(a for a in by.values() if a.get_actor_label()=='S0_WetFloor_ShallowWater')
 assert not water.get_actor_enable_collision()
 volume=next(a for a in by.values() if a.get_actor_label()=='S0_WetFloor_ReflectionVolume')
 post=volume.get_component_by_class(u.PostProcessComponent);settings=post.get_editor_property('settings')
 assert not post.get_editor_property('unbound')
 assert not settings.get_editor_property('override_auto_exposure_bias')
 assert not settings.get_editor_property('override_indirect_lighting_intensity')
 assert not settings.get_editor_property('override_bloom_intensity')
 (O/'verified.json').write_text(json.dumps(dict(checked_actors=checked,errors=errors,water_collision=False,saved_map_reopened=True),indent=2))
 assert not errors,errors[:10]
S={'t':time.monotonic(),'i':0,'sent':False,'busy':False}
shots=[('overview',(3050,-2650,1650),(-25,130)),('floor',(2600,0,220),(-10,180))]
def tick(dt):
 if S['busy']:return
 S['busy']=True
 try:
  if S['i']>=len(shots):u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor();return
  name,p,r=shots[S['i']];path=O/(tag+'-'+name+'.png')
  if S['sent'] and path.exists():S.update(i=S['i']+1,sent=False,t=time.monotonic());return
  if time.monotonic()-S['t']>240:raise RuntimeError('Capture timeout')
  if not S['sent']:
   cam.set_actor_location(u.Vector(*p),False,True);cam.set_actor_rotation(u.Rotator(pitch=r[0],yaw=r[1]),False)
   if time.monotonic()-S['t']>18:
    S['sent']=True;u.AutomationLibrary.take_high_res_screenshot(1600,900,str(path),camera=cam,delay=1)
 except Exception:
  (O/'capture-error.txt').write_text(traceback.format_exc());u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
 finally:S['busy']=False
handle=u.register_slate_post_tick_callback(tick)
