"""First review checkpoint: adjust only the two memory-photo camera cues."""
import unreal as u, json, shutil, hashlib, time, traceback
from pathlib import Path
R=Path(u.Paths.project_dir()); O=R/'Saved/S0ReviewPhoto'; O.mkdir(exist_ok=True)
P=lambda o,k:o.get_editor_property(k)
asset=R/'Content/SceneDirector/School/DA_S0_Opening.uasset'
digest=hashlib.sha256(asset.read_bytes()).hexdigest()
backup=O/'before-DA_S0_Opening.uasset'
assert not backup.exists(),'Review already started; inspect results before reapplying'
shutil.copy2(asset,backup)
a=u.load_asset('/Game/SceneDirector/School/DA_S0_Opening'); steps=list(P(a,'steps')); changes=[]
for i,s in enumerate(steps):
 if P(s,'type')!=u.DirectorNodeType.CAMERA_MOVE:continue
 d=P(s,'destination'); pos=P(d,'value')
 if pos.distance(u.Vector(3181,-18,220))>1:continue
 r=P(s,'rotation'); old=P(r,'value')
 assert len(P(s,'motion_points'))==0,'Inspect authored curve before replacing'
 changes.append(dict(index=i,before_position=[pos.x,pos.y,pos.z],before_rotation=[old.x,old.y,old.z]))
 d.set_editor_property('value',u.Vector(3190,-40,227))
 r.set_editor_property('value',u.Vector(0,3,193))
 s.set_editor_property('destination',d);s.set_editor_property('rotation',r)
assert len(changes)==2,changes
a.set_editor_property('steps',steps); result=str(u.SceneDirectorLibrary.compile_director(a))
assert '생성 완료' in result,result
assert hashlib.sha256(asset.read_bytes()).hexdigest()==digest,'Concurrent edit'
assert u.EditorAssetLibrary.save_loaded_asset(a,False)
(O/'change.json').write_text(json.dumps(dict(changes=changes,position=[3190,-40,227],rotation=[0,3,193],compile=result),ensure_ascii=False,indent=2),encoding='utf8')
E=u.get_editor_subsystem(u.UnrealEditorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert 'SceneReleaseValidation' in u.Paths.project_saved_dir()
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
u.EditorPythonScripting.set_keep_python_script_alive(True)
S=dict(start=time.monotonic(),photo_at=0,shot=False)
def tick(dt):
 try:
  assert time.monotonic()-S['start']<180,'Capture timeout'
  w=E.get_game_world()
  if not w:return
  ev=next((e for e in u.ObjectIterator(u.SceneEventSubsystem) if e.get_outer()==w),None)
  if not ev:return
  r=P(ev,'active_player')
  if not r:return
  text=str(P(r,'current_dialogue'))
  if '사진에는 당신이' in text:
   if not S['photo_at']:S['photo_at']=time.monotonic()
   if time.monotonic()-S['photo_at']>3 and not S['shot']:
    cam=u.GameplayStatics.get_player_camera_manager(w,0)
    assert cam.get_camera_location().distance(u.Vector(3190,-40,227))<1
    u.SystemLibrary.execute_console_command(w,'Shot SHOWUI -nosuffix filename="'+str(O/'photo-after.png')+'"');S['shot']=True
   if S['shot'] and (O/'photo-after.png').exists():
    (O/'verified.json').write_text(json.dumps(dict(success=True,camera=str(u.GameplayStatics.get_player_camera_manager(w,0).get_camera_location())),indent=2))
    L.editor_request_end_play();u.unregister_slate_post_tick_callback(handle);u.log('S0_PHOTO_REVIEW_CAPTURED')
   return
  if r.is_waiting_for_choice():assert r.select_dialogue_choice('Inside')
  elif r.is_waiting_for_dialogue():r.advance_dialogue()
 except Exception:
  u.log_error(traceback.format_exc());L.editor_request_end_play();u.unregister_slate_post_tick_callback(handle)
handle=u.register_slate_post_tick_callback(tick);L.editor_request_begin_play()
