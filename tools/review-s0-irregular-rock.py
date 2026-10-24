"""Scoped visual review; save only after an explicit local adopt decision."""
import unreal as u, json, re, time, traceback, hashlib, shutil
from pathlib import Path
R=Path(u.Paths.project_dir()); O=R/'Saved/S0WetFloor/IrregularRock_20261022'
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
 exec(compile((R/'tools/build-s0-irregular-rock-material.py').read_text(),'build-irregular','exec'),globals())
 material=mat
 targets=[]
 for a in A.get_all_level_actors():
  pos=a.get_actor_location()
  if not (-500<pos.x<4000 and -3000<pos.y<3000):continue
  for c in a.get_components_by_class(u.StaticMeshComponent):
   for i,m in enumerate(c.get_materials()):
    if m and m.get_name()=='M_S0_ShallowRock_V18':targets.append((a,c,i,m))
 assert len(targets)>=11,len(targets)
 allowed={a.get_name() for a,c,i,m in targets}
 (O/'targets.json').write_text(json.dumps([{'actor':a.get_name(),'label':a.get_actor_label(),'component':c.get_name(),'slot':i,'old':m.get_path_name()} for a,c,i,m in targets],indent=2))
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
     after=snapshot();before=state['baseline'];assert set(after)==set(before)
     for n,v in before.items():
      if n in allowed:
       assert all(norm(v[k])==norm(after[n][k]) for k in ('label','transform','collision')),n
       expected=json.loads(json.dumps(v))
       for mesh in expected['meshes']:
        mesh['materials']=[material.get_path_name() if '/M_S0_ShallowRock_V18.' in m else m for m in mesh['materials']]
       assert norm(expected)==norm(after[n]),n
      else:assert norm(v)==norm(after[n]),n
     (O/'after.json').write_text(json.dumps(after,indent=2));(O/'ready.json').write_text(json.dumps({'original_sha':SHA,'unchanged_actors':len(before)-len(allowed),'material_only_actors':len(allowed)}));state['ready']=True
    decision=O/'decision.txt'
    if decision.exists():
     if decision.read_text().strip()=='adopt':
      assert hashlib.sha256(FILE.read_bytes()).hexdigest()==SHA,'Concurrent map modification'
      A.destroy_actor(cam)
      shutil.copy2(FILE,O/'AbandonedSchool.before.umap')
      assert u.EditorLoadingAndSavingUtils.save_map(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(),MAP)
      (O/'saved.json').write_text(json.dumps({'before_sha':SHA,'after_sha':hashlib.sha256(FILE.read_bytes()).hexdigest(),'material_only_actors':sorted(allowed),'material':material.get_path_name()},indent=2))
     u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
    elif time.monotonic()-state['t']>600: raise RuntimeError('Review decision timeout; no save')
    return
   name,p,r,changed=shots[state['i']];path=O/(name+'.png')
   if state['sent'] and path.exists() and path.stat().st_size>0:
    state.update(i=state['i']+1,t=time.monotonic(),sent=False);return
   if time.monotonic()-state['t']>180: raise RuntimeError('Capture timeout')
   if not state['sent']:
    for a,c,i,m in targets:c.set_material(i,material if changed else m)
    cam.set_actor_location(u.Vector(*p),False,True);cam.set_actor_rotation(u.Rotator(pitch=r[0],yaw=r[1]),False)
    if time.monotonic()-state['t']>25:
     assert not path.exists();state['sent']=True;u.AutomationLibrary.take_high_res_screenshot(1600,900,str(path),camera=cam,delay=1)
  except Exception:
   (O/'error.txt').write_text(traceback.format_exc());u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
  finally:state['busy']=False
 handle=u.register_slate_post_tick_callback(tick)
except Exception:
 (O/'error.txt').write_text(traceback.format_exc());u.SystemLibrary.quit_editor()
