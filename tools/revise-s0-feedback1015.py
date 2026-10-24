"""S0 feedback: persist non-framing fixes; camera drafts remain opt-in/in-memory."""
import unreal as u,json,shutil,hashlib
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0Feedback1015';P=lambda o,k:o.get_editor_property(k)
def sp(o,**kw):
 for k,v in kw.items():o.set_editor_property(k,v)
 return o
def revise(a,camera_draft=False):
 ss=list(P(a,'steps'));N=u.DirectorNodeType
 def link(x,y):sp(x,next_nodes=[P(y,'id')])
 def make(typ,**kw):
  n=sp(u.SceneDirectorLibrary.make_director_step(typ),**kw);ss.append(n);return n
 if len(ss)==113:
  # The girl already exists off screen. Do not reveal her in the visible slit.
  sp(ss[104],visible=True)
  pts=list(P(ss[47],'motion_points'));v=P(pts[0],'position');v.y=1500.;sp(pts[0],position=v);sp(ss[47],motion_points=pts)
  sp(ss[44],duration=.4)
  for i in [19,31]:sp(ss[i],duration=1.4)
  sh=P(ss[109],'shake');sp(sh,translation_range=1.68,rotation_range=1.44);sp(ss[109],shake=sh)
  # Running stays visible through the slit. Return the view only after arrival + one second.
  link(ss[52],ss[110]);link(ss[110],ss[54]);sp(ss[54],wait_for_completion=True)
  pause=make(N.WAIT,duration=1.);link(ss[54],pause);link(pause,ss[86]);link(ss[53],ss[55]);link(ss[55],ss[111])
  # Avoid an unannounced click gate followed by 2.5 seconds of silence.
  sp(ss[56],dialogue_advance=u.DirectorDialogueAdvance.TIMED,duration=1.2)
  sp(ss[58],duration=.2);sp(ss[60],duration=.4)
  # Same physical camera and FOV through the fall; no 115 -> 55 degree cut.
  sp(ss[70],camera_key='Eyes');sp(ss[72],camera_key='Eyes')
 if camera_draft:
  # Single uninterrupted first-person fall, aimed forward at the escaping girl.
  pts=[]
  for t,pos,rot in [(0.,(3030,0,170),(0,-10,180)),(.6,(3030,0,170),(0,-10,180)),(1.6,(2890,0,42),(0,-3,180)),(2+1/3,(2890,0,42),(0,-3,180))]:
   pts.append(sp(u.DirectorMotionPoint(),time=t,position=u.Vector(*pos),rotation=u.Vector(*rot),scale=u.Vector(1,1,1),interpolation=u.DirectorPathInterpolation.LINEAR))
  sp(pts[-1],interpolation=u.DirectorPathInterpolation.CONSTANT)
  sp(ss[70],motion_points=pts)
  reveal=make(N.GAME_ACTION,action_key=P(ss[69],'action_key'),action_parameters=sp(u.DirectorActionParameters(),identifier='ThirdPerson'))
  link(ss[71],reveal);link(reveal,ss[72])
  # Look left / right / centre before the confined-space narration.
  previous=ss[96]
  for yaw,hold in [(120.,2.),(240.,2.),(180.,0.)]:
   move=make(N.CAMERA_MOVE,camera_key='Eyes',duration=2.,wait_for_completion=True,
    destination=P(ss[6],'destination'),rotation=sp(u.DirectorVectorInput(),value=u.Vector(0,0,yaw)))
   link(previous,move);previous=move
   if hold:
    wait=make(N.WAIT,duration=hold);link(previous,wait);previous=wait
  link(previous,ss[97])
  # Rear centreline, elevated view; no orbit toward the character's side.
  sp(ss[72],destination=sp(u.DirectorVectorInput(),value=u.Vector(3075,0,170)),rotation=sp(u.DirectorVectorInput(),value=u.Vector(0,-65,180)),duration=3.5)
  # Start blending while GetUp is playing, retaining the input lock until it finishes.
  ret=make(N.CAMERA_RETURN,duration=6.3,wait_for_completion=False)
  link(ss[93],ret);link(ret,ss[94]);sp(ss[79],duration=.1)
 sp(a,steps=ss);result=str(u.SceneDirectorLibrary.compile_director(a));assert '생성 완료' in result,result
 return result
if __name__=='__main__':
 files=[R/'Content/SceneDirector/School/DA_S0_Opening.uasset',R/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap']
 hashes={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
 for f in files:
  backup=O/('before-'+f.name)
  if backup.exists():assert backup.read_bytes()==f.read_bytes(),'Already applied or concurrently changed'
  else:shutil.copy2(f,backup)
 w=u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
 a=u.load_asset('/Game/SceneDirector/School/DA_S0_Opening');result=revise(a)
 girl=next(x for x in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if x.get_actor_label()=='S0_LittleGirl_Blocking')
 girl.set_actor_location(u.Vector(2320,1500,67),False,False);girl.set_actor_hidden_in_game(False)
 count=u.SceneDirectorLibrary.remove_school_opening_legacy_presentation(w,True);assert count==3,count
 for f in files:assert hashlib.sha256(f.read_bytes()).hexdigest()==hashes[str(f)],'Concurrent change: '+str(f)
 assert u.EditorAssetLibrary.save_loaded_asset(a,False);assert u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
 (O/'applied.json').write_text(json.dumps(dict(compile=result,legacy_calls_removed=count,camera_draft_saved=False),ensure_ascii=False,indent=2),encoding='utf8')
 u.log('S0_FEEDBACK_APPLIED '+result)
