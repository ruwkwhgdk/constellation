"""Scoped visual review; save only after an explicit local adopt decision."""
import unreal as u, json, re, time, traceback, hashlib, shutil
from pathlib import Path
R=Path(u.Paths.project_dir()); O=R/'Saved/S0WetFloor/CeilingBounce_20261023'
O.mkdir(parents=True,exist_ok=True)
MAP='/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool'
FILE=R/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
SHA=hashlib.sha256(FILE.read_bytes()).hexdigest()
def norm(v): return re.sub(r'0x[0-9a-fA-F]+','PTR',json.dumps(v,sort_keys=True)).replace('-0.000000','0.000000')
def snapshot():
 return {a.get_name():{'label':a.get_actor_label(),'transform':str(a.get_actor_transform()),'collision':a.get_actor_enable_collision(),'meshes':[{'name':c.get_name(),'mesh':c.static_mesh.get_path_name() if c.static_mesh else '', 'materials':[m.get_path_name() if m else '' for m in c.get_materials()]} for c in a.get_components_by_class(u.StaticMeshComponent)]} for a in A.get_all_level_actors() if a!=cam}

def lightsnapshot():
 result={}
 for a in A.get_all_level_actors():
  for c in a.get_components_by_class(u.LightComponent):
   d={}
   for k in ['intensity','intensity_units','light_color','attenuation_radius','source_width','source_height','cast_shadows','mobility','indirect_lighting_intensity','volumetric_scattering_intensity','specular_scale']:
    try:d[k]=str(c.get_editor_property(k))
    except Exception:pass
   result[a.get_name()+'/'+c.get_name()]=d
 return result
try:
 assert u.EditorLoadingAndSavingUtils.load_map(MAP)
 A=u.get_editor_subsystem(u.EditorActorSubsystem)
 assert not any(a.get_actor_label()=='S0_Art_CeilingBounce' for a in A.get_all_level_actors())
 light=None
 cam=A.spawn_actor_from_class(u.CameraActor,u.Vector(2900,900,700),u.Rotator(pitch=-20,yaw=-138),transient=True)
 cam.camera_component.set_field_of_view(83)
 u.EditorLevelLibrary.pilot_level_actor(cam);u.EditorLevelLibrary.editor_set_game_view(True)
 u.EditorPythonScripting.set_keep_python_script_alive(True)
 shots=[(prefix+name,pos,rot,changed) for prefix,changed in [('before-',False),('candidate-',True)] for name,pos,rot in [('main',(2900,900,700),(-20,-138)),('ceiling',(1800,700,1100),(57,-120))]]
 state={'i':0,'t':time.monotonic(),'sent':False,'busy':False,'baseline':None,'ready':False}
 def tick(dt):
  global light
  if state['busy']: return
  state['busy']=True
  try:
   if state['baseline'] is None and time.monotonic()-state['t']>15:
    state['baseline']=snapshot();state['lights_before']=lightsnapshot();(O/'lights-before.json').write_text(json.dumps(state['lights_before'],indent=2));(O/'before.json').write_text(json.dumps(state['baseline'],indent=2))
   if state['i']>=len(shots):
    if not state['ready']:
     after=snapshot();before=state['baseline'];assert len(after)==len(before)+1
     assert set(after)-set(before)=={light.get_name()}
     for n,v in before.items():assert norm(v)==norm(after[n]),n
     lb=state['lights_before'];la=lightsnapshot()
     for n,v in lb.items():assert norm(v)==norm(la[n]),n
     (O/'lights-after.json').write_text(json.dumps(la,indent=2))
     (O/'after.json').write_text(json.dumps(after,indent=2))
     (O/'ready.json').write_text(json.dumps({'original_sha':SHA,'unchanged_actors':len(before),'added_light':light.get_name()}));state['ready']=True
    decision=O/'decision.txt'
    if decision.exists() and decision.read_text(encoding='utf-8-sig').strip() in ('adopt','reject'):
     if decision.read_text(encoding='utf-8-sig').strip()=='adopt':
      assert hashlib.sha256(FILE.read_bytes()).hexdigest()==SHA,'Concurrent map modification'
      A.destroy_actor(cam)
      shutil.copy2(FILE,O/'AbandonedSchool.before.umap')
      assert u.EditorLoadingAndSavingUtils.save_map(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(),MAP)
      (O/'saved.json').write_text(json.dumps({'before_sha':SHA,'after_sha':hashlib.sha256(FILE.read_bytes()).hexdigest(),'added_light':light.get_name(),'label':light.get_actor_label()},indent=2))
     u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
    elif time.monotonic()-state['t']>600: raise RuntimeError('Review decision timeout; no save')
    return
   name,p,r,changed=shots[state['i']];path=O/(name+'.png')
   if state['sent'] and path.exists() and path.stat().st_size>0:
    state.update(i=state['i']+1,t=time.monotonic(),sent=False);return
   if time.monotonic()-state['t']>180: raise RuntimeError('Capture timeout')
   if not state['sent']:
    if changed and light is None:
     light=A.spawn_actor_from_class(u.RectLight,u.Vector(1550,-400,1900),u.Rotator(pitch=90,yaw=0))
     light.set_actor_label('S0_Art_CeilingBounce');light.set_folder_path('sector0/classroom_start/ArtPolish');light.set_actor_enable_collision(False)
     c=light.get_component_by_class(u.RectLightComponent);c.set_mobility(u.ComponentMobility.MOVABLE)
     c.set_editor_property('intensity_units',u.LightUnits.CANDELAS);c.set_intensity(40.)
     c.set_light_color(u.LinearColor(.56,.68,.78,1))
     c.set_editor_property('attenuation_radius',1900.);c.set_editor_property('source_width',800.);c.set_editor_property('source_height',800.)
     c.set_editor_property('cast_shadows',True);c.set_editor_property('indirect_lighting_intensity',.3);c.set_editor_property('volumetric_scattering_intensity',0.)
    cam.set_actor_location(u.Vector(*p),False,True);cam.set_actor_rotation(u.Rotator(pitch=r[0],yaw=r[1]),False)
    if time.monotonic()-state['t']>25:
     assert not path.exists();state['sent']=True;u.AutomationLibrary.take_high_res_screenshot(1600,900,str(path),camera=cam,delay=1)
  except Exception:
   (O/'error.txt').write_text(traceback.format_exc());u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
  finally:state['busy']=False
 handle=u.register_slate_post_tick_callback(tick)
except Exception:
 (O/'error.txt').write_text(traceback.format_exc());u.SystemLibrary.quit_editor()
