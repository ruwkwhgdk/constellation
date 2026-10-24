"""Read-only player-eye contact survey. Never save map."""
import unreal as u,json,time,traceback,hashlib
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/PlayerContact_20261024';O.mkdir(parents=True,exist_ok=True)
mapfile=R/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
sha=hashlib.sha256(mapfile.read_bytes()).hexdigest()
assert sha=='e3007f3587d41def1b8c8833b2b49e29265c7c7d804cb5900b3a5a4c8b89bc5a'
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
A=u.get_editor_subsystem(u.EditorActorSubsystem)
cam=A.spawn_actor_from_class(u.CameraActor,u.Vector(2900,900,700),u.Rotator(pitch=-20,yaw=-138),transient=True)
cam.camera_component.set_field_of_view(83)
u.EditorLevelLibrary.pilot_level_actor(cam);u.EditorLevelLibrary.editor_set_game_view(True)
u.EditorPythonScripting.set_keep_python_script_alive(True)
shots=[('rear-contact',(1700,400,180),(5,90)),('side-contact',(600,400,180),(10,65)),('ramp-contact',(2300,300,180),(8,-85))]
state={'i':0,'t':time.monotonic(),'sent':False,'busy':False}
def tick(dt):
 if state['busy']:return
 state['busy']=True
 try:
  if state['i']>=len(shots):
   assert hashlib.sha256(mapfile.read_bytes()).hexdigest()==sha
   (O/'captures-complete.json').write_text(json.dumps({'map_unchanged':True,'images':[s[0]+'.png' for s in shots]}))
   u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor();return
  name,p,r=shots[state['i']];path=O/(name+'.png')
  if state['sent'] and path.exists() and path.stat().st_size>0:
   state.update(i=state['i']+1,t=time.monotonic(),sent=False);return
  if time.monotonic()-state['t']>180:raise RuntimeError('Capture timeout')
  if not state['sent']:
   cam.set_actor_location(u.Vector(*p),False,True);cam.set_actor_rotation(u.Rotator(pitch=r[0],yaw=r[1]),False)
   if time.monotonic()-state['t']>25:
    assert not path.exists(),'Use fresh output captures'
    state['sent']=True;u.AutomationLibrary.take_high_res_screenshot(1600,900,str(path),camera=cam,delay=1)
 except Exception:
  (O/'verify-error.txt').write_text(traceback.format_exc());u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
 finally:state['busy']=False
handle=u.register_slate_post_tick_callback(tick)

