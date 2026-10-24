"""Restore six intentional progression-gate props, preserving the latest map."""
import unreal as u,json,hashlib,shutil,re,time,traceback
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/RestoreGate_20261019';O.mkdir(parents=True,exist_ok=True)
MAP='/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool'
F=R/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
verify='-RestoreFurnitureVerify' in u.SystemLibrary.get_command_line()
def sha():return hashlib.sha256(F.read_bytes()).hexdigest()
def norm(x):return re.sub(r'0x[0-9A-Fa-f]+','PTR',json.dumps(x,sort_keys=True)).replace('-0.000000','0.000000')
def snapshot():
 source=(R/'tools/review-s0-shallow-rock.py').read_text()
 scope=dict(u=u,O=O,A=A,json=json)
 exec(source[source.index('rows=[];lights=[]'):source.index('cmd=u.SystemLibrary')],scope)
 return dict(actors=scope['rows'],lights=scope['lights'])
try:
 initial=sha()
 assert u.EditorLoadingAndSavingUtils.load_map(MAP)
 A=u.get_editor_subsystem(u.EditorActorSubsystem)
 moves=json.loads((R/'Saved/S0WetFloor/RampFurniture_20261018/moves.json').read_text())
 assert len(moves)==6
 actors={a.get_name():a for a in A.get_all_level_actors()}
 if not verify:
  assert not (O/'saved.json').exists(),'Already restored; use verify mode'
  baseline=snapshot();(O/'baseline.json').write_text(json.dumps(baseline,indent=2))
  records=[]
  for row in moves:
   a=actors[row['name']];p=a.get_actor_location();current=[p.x,p.y,p.z]
   assert all(abs(x-y)<.01 for x,y in zip(current,row['after'])),(row['name'],'Newer position conflicts with relocation record',current)
   records.append(dict(name=row['name'],label=a.get_actor_label(),current=current,restored=row['before']))
  for row in moves:
   a=actors[row['name']];rotation=a.get_actor_rotation();scale=a.get_actor_scale3d()
   a.set_actor_location(u.Vector(*row['before']),False,True)
   assert a.get_actor_rotation()==rotation and a.get_actor_scale3d()==scale
  expected=snapshot();names={x['name'] for x in moves}
  before={x['name']:x for x in baseline['actors']};after={x['name']:x for x in expected['actors']}
  assert before.keys()==after.keys()
  for name in before:
   old=dict(before[name]);new=dict(after[name])
   if name in names:old.pop('transform');new.pop('transform')
   assert norm(old)==norm(new),name
  assert norm(baseline['lights'])==norm(expected['lights'])
  assert sha()==initial,'Map changed externally; do not save'
  shutil.copy2(F,O/'AbandonedSchool.before.umap')
  (O/'expected.json').write_text(json.dumps(expected,indent=2))
  (O/'restored.json').write_text(json.dumps(records,indent=2))
  assert u.EditorLoadingAndSavingUtils.save_map(u.EditorLevelLibrary.get_editor_world(),MAP)
  (O/'saved.json').write_text(json.dumps(dict(before_sha256=initial,sha256=sha(),restored=6),indent=2))
  u.SystemLibrary.quit_editor()
 else:
  assert initial==json.loads((O/'saved.json').read_text())['sha256']
  actual=snapshot();assert norm(actual)==norm(json.loads((O/'expected.json').read_text()))
  for row in moves:
   p=actors[row['name']].get_actor_location()
   assert all(abs(x-y)<.01 for x,y in zip([p.x,p.y,p.z],row['before']))
  (O/'verification.json').write_text(json.dumps(dict(restored=6,other_actors_preserved=len(actual['actors'])-6,recorded_lights_preserved=True,fresh_reload=True,sha256=initial),indent=2))
  cam=A.spawn_actor_from_class(u.CameraActor,u.Vector(1800,-1700,900),u.Rotator(pitch=-28,yaw=-140),transient=True)
  cam.camera_component.set_field_of_view(75);u.EditorLevelLibrary.pilot_level_actor(cam);u.EditorLevelLibrary.editor_set_game_view(True)
  start=time.monotonic();state={'sent':False};u.EditorPythonScripting.set_keep_python_script_alive(True)
  def tick(dt):
   if time.monotonic()-start>25 and not state['sent']:
    u.AutomationLibrary.take_high_res_screenshot(1600,900,str(O/'restored-gate.png'),camera=cam,delay=1);state['sent']=True
   if time.monotonic()-start>32 and (O/'restored-gate.png').exists():
    u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
  handle=u.register_slate_post_tick_callback(tick)
except:
 (O/('verify-error.txt' if verify else 'restore-error.txt')).write_text(traceback.format_exc());u.SystemLibrary.quit_editor()
