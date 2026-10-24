"""Scoped visual review; save only after an explicit local adopt decision."""
import unreal as u, json, re, time, traceback, hashlib, shutil
from pathlib import Path
R=Path(u.Paths.project_dir()); O=R/'Saved/S0WetFloor/WallTransitionFinal_20261023'
O.mkdir(parents=True,exist_ok=True)
MAP='/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool'
FILE=R/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
SHA=hashlib.sha256(FILE.read_bytes()).hexdigest()
def norm(v): return re.sub(r'0x[0-9a-fA-F]+','PTR',json.dumps(v,sort_keys=True)).replace('-0.000000','0.000000')
def snapshot():
 return {a.get_name():{'label':a.get_actor_label(),'transform':str(a.get_actor_transform()),'collision':a.get_actor_enable_collision(),'meshes':[{'name':c.get_name(),'mesh':c.static_mesh.get_path_name() if c.static_mesh else '', 'materials':[m.get_path_name() if m else '' for m in c.get_materials()]} for c in a.get_components_by_class(u.StaticMeshComponent)]} for a in A.get_all_level_actors() if a!=cam}
try:
 assert u.EditorLoadingAndSavingUtils.load_map(MAP)
 A=u.get_editor_subsystem(u.EditorActorSubsystem)
 assert not any(a.get_actor_label().startswith('S0_Art_WallTransition_') for a in A.get_all_level_actors())
 material=u.load_asset('/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor/M_S0_IrregularRock_V24')
 added=[]
 def add_candidate():
  specs=[(1,1020,1990,440,150,240,1100,0),(2,1430,1995,500,150,190,1060,180),(3,1840,1990,380,150,210,1040,0)]
  for i,(kind,x,y,w,d,h,top,yaw) in enumerate(specs):
   mesh=u.load_asset('/Game/LuosCaves/Meshes/Props_Rocks/SM_LCave_P_Rock_%02d'%kind);assert mesh
   a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0),u.Rotator(yaw=yaw))
   a.set_actor_label('S0_Art_WallTransition_%02d'%i);a.static_mesh_component.set_static_mesh(mesh)
   a.static_mesh_component.set_material(0,material);a.set_actor_enable_collision(False)
   center,e=a.get_actor_bounds(False);a.set_actor_scale3d(u.Vector(w/(2*e.x),d/(2*e.y),h/(2*e.z)))
   center,e=a.get_actor_bounds(False);a.set_actor_location(u.Vector(x-center.x,y-center.y,top-center.z-e.z),False,True)
   center,e=a.get_actor_bounds(False);assert center.y-e.y>1900 and center.z-e.z>600
   added.append(a)
 cam=A.spawn_actor_from_class(u.CameraActor,u.Vector(2900,900,700),u.Rotator(pitch=-20,yaw=-138),transient=True)
 cam.camera_component.set_field_of_view(83)
 u.EditorLevelLibrary.pilot_level_actor(cam);u.EditorLevelLibrary.editor_set_game_view(True)
 u.EditorPythonScripting.set_keep_python_script_alive(True)
 shots=[('before-main',(2900,900,700),(-20,-138),False),('before-near',(1700,400,300),(5,90),False),('candidate-main',(2900,900,700),(-20,-138),True),('candidate-near',(1700,400,300),(5,90),True)]
 state={'i':0,'t':time.monotonic(),'sent':False,'busy':False,'baseline':None,'ready':False}
 def tick(dt):
  if state['busy']: return
  state['busy']=True
  try:
   if state['baseline'] is None and time.monotonic()-state['t']>15:
    state['baseline']=snapshot();(O/'before.json').write_text(json.dumps(state['baseline'],indent=2))
   if state['i']>=len(shots):
    if not state['ready']:
     after=snapshot();before=state['baseline'];assert set(before).issubset(after)
     assert len(after)==len(before)+3
     for n,v in before.items(): assert norm(v)==norm(after[n]),n
     assert len(added)==3 and all(not a.get_actor_enable_collision() for a in added)
     (O/'after.json').write_text(json.dumps(after,indent=2));(O/'ready.json').write_text(json.dumps({'original_sha':SHA,'unchanged_actors':len(before),'added':3}));state['ready']=True
    decision=O/'decision.txt'
    if decision.exists():
     if decision.read_text().strip()=='adopt':
      assert hashlib.sha256(FILE.read_bytes()).hexdigest()==SHA,'Concurrent map modification'
      A.destroy_actor(cam)
      shutil.copy2(FILE,O/'AbandonedSchool.before.umap')
      assert u.EditorLoadingAndSavingUtils.save_map(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(),MAP)
      (O/'saved.json').write_text(json.dumps({'before_sha':SHA,'after_sha':hashlib.sha256(FILE.read_bytes()).hexdigest(),'added_labels':[a.get_actor_label() for a in added]},indent=2))
     u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
    elif time.monotonic()-state['t']>600: raise RuntimeError('Review decision timeout; no save')
    return
   name,p,r,changed=shots[state['i']];path=O/(name+'.png')
   if state['sent'] and path.exists() and path.stat().st_size>0:
    state.update(i=state['i']+1,t=time.monotonic(),sent=False);return
   if time.monotonic()-state['t']>180: raise RuntimeError('Capture timeout')
   if not state['sent']:
    if changed and not added and state['baseline'] is not None: add_candidate()
    cam.set_actor_location(u.Vector(*p),False,True);cam.set_actor_rotation(u.Rotator(pitch=r[0],yaw=r[1]),False)
    if time.monotonic()-state['t']>25:
     assert not path.exists();state['sent']=True;u.AutomationLibrary.take_high_res_screenshot(1600,900,str(path),camera=cam,delay=1)
  except Exception:
   (O/'error.txt').write_text(traceback.format_exc());u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
  finally:state['busy']=False
 handle=u.register_slate_post_tick_callback(tick)
except Exception:
 (O/'error.txt').write_text(traceback.format_exc());u.SystemLibrary.quit_editor()
