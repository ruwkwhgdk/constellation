"""Apply the user-directed slow S0 wake preset, preserving investigation branches."""
import unreal as u,json,shutil,time
from pathlib import Path
R=Path(u.Paths.project_dir()).resolve();out=R/'Saved/WakeVision/SlowRevision-20261011';out.mkdir(parents=True,exist_ok=True)
a=u.load_asset('/Game/SceneDirector/School/DA_S0_Opening');steps=list(a.get_editor_property('steps'));N=u.DirectorNodeType
src=R/'Content/SceneDirector/School/DA_S0_Opening.uasset';backup=out/src.name
if not backup.exists():shutil.copy2(src,backup)
def key(g):return tuple(g.get_editor_property(k) for k in ('a','b','c','d'))
def nxt(s):
 ids=list(s.get_editor_property('next_nodes'));assert len(ids)==1
 return next(x for x in steps if key(x.get_editor_property('id'))==key(ids[0]))
eye=next(s for s in steps if s.get_editor_property('type')==N.EYELIDS)
visions=[s for s in steps if s.get_editor_property('type')==N.VISION]
if len(visions)==1:
 vision=nxt(eye);assert vision.get_editor_property('type')==N.VISION
 hub=nxt(vision);assert hub.get_editor_property('type')==N.HUB
 cameras=[];node=nxt(hub)
 while node.get_editor_property('type')==N.CAMERA_MOVE:
  cameras.append(node);node=nxt(node)
 assert len(cameras)==3 and node.get_editor_property('type')==N.DIALOGUE
 hub.set_editor_property('next_nodes',[node.get_editor_property('id')])
 pre=next(s for s in steps if any(key(g)==key(eye.get_editor_property('id')) for g in s.get_editor_property('next_nodes')));assert pre.get_editor_property('type')==N.WAIT
 pred=next(s for s in steps if any(key(g)==key(pre.get_editor_property('id')) for g in s.get_editor_property('next_nodes')));assert pred.get_editor_property('type')==N.CAMERA_MOVE
 pred.set_editor_property('next_nodes',[eye.get_editor_property('id')])
 remove={key(x.get_editor_property('id')) for x in cameras+[pre]};steps=[s for s in steps if key(s.get_editor_property('id')) not in remove]
 for field,value in [('eye_start_hold',1),('eye_final_seconds',.5),('eye_final_hold',2),('eye_from',0),('eye_final_open',1),('wait_for_completion',False)]:eye.set_editor_property(field,value)
 blinks=[]
 for amount,closed in [(.25,1),(.55,2)]:
  b=u.DirectorBlink()
  for field,value in [('open_amount',amount),('open_seconds',3),('open_hold',2),('close_seconds',2),('closed_hold',closed)]:b.set_editor_property(field,value)
  blinks.append(b)
 eye.set_editor_property('blinks',blinks)
 phases=[(8,.85,.85,.22,.22),(1,.85,.25,.22,.06),(7,.25,.25,.06,.06),(2,.25,0,.06,0),(2.5,0,0,0,0)]
 chain=[vision]+[u.SceneDirectorLibrary.make_director_step(N.VISION) for _ in phases[1:]]
 for i,(s,p) in enumerate(zip(chain,phases)):
  for field,value in zip(('duration','blur_from','blur_to','haze_from','haze_to'),p):s.set_editor_property(field,value)
  s.set_editor_property('vision_curve',u.DirectorVisionCurve.SMOOTH);s.set_editor_property('wait_for_completion',True)
  s.set_editor_property('next_nodes',[(chain[i+1] if i+1<len(chain) else hub).get_editor_property('id')])
  pos=vision.get_editor_property('editor_position');s.set_editor_property('editor_position',u.Vector2D(pos.x+i*220,pos.y))
 steps.extend(chain[1:]);a.set_editor_property('steps',steps)
else:
 assert len(visions)==5,'Unexpected vision graph; inspect before overwriting'
steps=list(a.get_editor_property('steps'));eye=next(s for s in steps if s.get_editor_property('type')==N.EYELIDS)
duration=eye.get_editor_property('eye_start_hold')+eye.get_editor_property('eye_final_seconds')+eye.get_editor_property('eye_final_hold')+sum(b.get_editor_property('open_seconds')+b.get_editor_property('open_hold')+b.get_editor_property('close_seconds')+b.get_editor_property('closed_hold') for b in eye.get_editor_property('blinks'))
assert abs(duration-20.5)<.001
chain=[];s=nxt(eye)
while s.get_editor_property('type')==N.VISION:chain.append(s);s=nxt(s)
assert len(chain)==5 and abs(sum(s.get_editor_property('duration') for s in chain)-20.5)<.001
assert s.get_editor_property('type')==N.HUB and nxt(s).get_editor_property('type')==N.DIALOGUE
result=u.SceneDirectorLibrary.compile_director(a);assert result is not None,str(result)
assert u.EditorAssetLibrary.save_loaded_asset(a,False)
(out/'applied.json').write_text(json.dumps({'eye_seconds':duration,'opening_amounts':[b.get_editor_property('open_amount') for b in eye.get_editor_property('blinks')],'vision_phase_seconds':[s.get_editor_property('duration') for s in chain],'dialogue_immediately_after_hold':True,'compile':str(result)},ensure_ascii=False,indent=2),encoding='utf8')
u.log('S0_SLOW_WAKE_APPLIED '+str(result))
u.EditorPythonScripting.set_keep_python_script_alive(True);start=time.monotonic()
def finish(dt):
 if time.monotonic()-start>3:u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(finish)
