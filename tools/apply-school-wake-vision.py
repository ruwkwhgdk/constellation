"""Migrate only the S0 intro to common vision nodes. Run with the project editor closed."""
import unreal as u,json,shutil,time
from pathlib import Path
R=Path(u.Paths.project_dir()).resolve();D='/Game/SceneDirector/School/DA_S0_Opening';out=R/'Saved/WakeVision';out.mkdir(exist_ok=True)
src=R/'Content/SceneDirector/School/DA_S0_Opening.uasset';backup=out/'DA_S0_Opening-before-vision.uasset'
if not backup.exists():shutil.copy2(src,backup)
a=u.load_asset(D);assert a
steps=list(a.get_editor_property('steps'));N=u.DirectorNodeType
def guid_key(g):return tuple(g.get_editor_property(k) for k in ('a','b','c','d'))
existing=[s for s in steps if s.get_editor_property('type')==N.EYELIDS]
if existing:
 assert len(existing)==1;u.log('S0_WAKE_ALREADY_APPLIED')
else:
 candidates=[s for s in steps if s.get_editor_property('type')==N.GAME_ACTION and str(s.get_editor_property('action_parameters').get_editor_property('identifier'))=='OpenEyes' and abs(s.get_editor_property('action_parameters').get_editor_property('value')-2.4)<.01]
 assert len(candidates)==1,'Expected the original intro OpenEyes cue exactly once'
 eye=candidates[0];nextids=list(eye.get_editor_property('next_nodes'));assert len(nextids)==1
 vision=next(s for s in steps if guid_key(s.get_editor_property('id'))==guid_key(nextids[0]));assert vision.get_editor_property('type')==N.WAIT and abs(vision.get_editor_property('duration')-2.5)<.01
 def replace_step(old,kind):
  new=u.SceneDirectorLibrary.make_director_step(kind)
  for key in ('id','next_nodes','editor_position'):new.set_editor_property(key,old.get_editor_property(key))
  index=next(i for i,x in enumerate(steps) if guid_key(x.get_editor_property('id'))==guid_key(old.get_editor_property('id')))
  steps[index]=new;return new
 eye=replace_step(eye,N.EYELIDS);vision=replace_step(vision,N.VISION)
 eye.set_editor_property('eye_mode',u.DirectorEyeMode.BLINK);eye.set_editor_property('eye_from',0);eye.set_editor_property('eye_final_open',1);eye.set_editor_property('eye_start_hold',.4);eye.set_editor_property('eye_final_seconds',1.2);eye.set_editor_property('eye_final_hold',.8);eye.set_editor_property('wait_for_completion',False)
 blinks=[]
 for amount,op,hold,cl,closed in [(.3,.4,.12,.12,.06),(.65,.5,.2,.14,.06)]:
  b=u.DirectorBlink()
  for key,value in [('open_amount',amount),('open_seconds',op),('open_hold',hold),('close_seconds',cl),('closed_hold',closed)]:b.set_editor_property(key,value)
  blinks.append(b)
 eye.set_editor_property('blinks',blinks)
 vision.set_editor_property('duration',4);vision.set_editor_property('wait_for_completion',True)
 for key,value in [('blur_from',.85),('blur_to',0),('haze_from',.22),('haze_to',0)]:vision.set_editor_property(key,value)
 join=u.SceneDirectorLibrary.make_director_step(N.HUB);join.set_editor_property('next_nodes',vision.get_editor_property('next_nodes'));vision.set_editor_property('next_nodes',[join.get_editor_property('id')]);pos=vision.get_editor_property('editor_position');join.set_editor_property('editor_position',u.Vector2D(pos.x+130,pos.y+160));steps.append(join)
 a.set_editor_property('steps',steps)
 result=u.SceneDirectorLibrary.compile_director(a);assert result is not None,str(result);assert u.EditorAssetLibrary.save_loaded_asset(a,False)
 (out/'applied.json').write_text(json.dumps({'asset':D,'nodes':len(steps),'blink_cycles':2,'effect_seconds':4,'compile':str(result)},ensure_ascii=False,indent=2),encoding='utf8');u.log('S0_WAKE_APPLIED '+str(result))
u.EditorPythonScripting.set_keep_python_script_alive(True);start=time.monotonic()
def finish(dt):
 if time.monotonic()-start>3:u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(finish)
