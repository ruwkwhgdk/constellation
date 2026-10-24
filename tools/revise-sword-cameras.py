"""Apply user-requested sword camera/timing revisions, preserving existing bindings."""
import unreal as u,json,time,traceback,shutil
from pathlib import Path
R=Path(u.Paths.project_dir()).resolve();O=R/'Saved/SwordAcquisition/Revision20261023';O.mkdir(parents=True,exist_ok=True)
def get(o,k):return o.get_editor_property(k)
def put(o,**kw):
 for k,v in kw.items():o.set_editor_property(k,v)
 return o
try:
 path='/Game/SceneDirector/School/DA_SwordAcquisition';src=R/'Content/SceneDirector/School/DA_SwordAcquisition.uasset';backup=O/('GraphBackup-'+time.strftime('%Y%m%d-%H%M%S')+'.uasset');shutil.copy2(src,backup)
 g=u.load_asset(path);steps=list(get(g,'steps'));N=u.DirectorNodeType
 b=next(c for c in get(g,'cameras') if str(get(c,'key'))=='B');pose=get(b,'transform');rot=pose.rotation.rotator()
 forward=u.MathLibrary.get_forward_vector(rot);end=pose.translation+forward*45+u.Vector(0,0,35)
 kept=[];skip_wait=False;after=None
 for s in steps:
  typ=get(s,'type')
  if typ==N.CAMERA_SWITCH:
   key=str(get(s,'camera_key'))
   if key=='A':skip_wait=True;continue
   if key=='B':put(s,duration=1/30,blend_seconds=0.,wait_for_completion=True)
   elif key=='C':
    s=u.SceneDirectorLibrary.make_director_step(N.CAMERA_MOVE)
    put(s,camera_key='B',duration=.8,wait_for_completion=True,activate_camera=True,destination=put(u.DirectorVectorInput(),value=end),rotation=put(u.DirectorVectorInput(),value=u.Vector(rot.roll,rot.pitch,rot.yaw)))
  elif typ==N.WAIT and skip_wait:skip_wait=False;continue
  elif typ==N.WAIT and after=='Grip':put(s,duration=.6333333333)
  elif typ==N.CAMERA_RETURN:continue # End uses existing immediate view-target restore.
  if typ==N.GAME_ACTION:after=str(get(get(s,'action_parameters'),'identifier'))
  elif typ==N.WAIT:after=None
  kept.append(s)
 for a,bnext in zip(kept,kept[1:]):
  if get(a,'type')!=N.QTE:put(a,next_nodes=[get(bnext,'id')])
 put(g,steps=kept);u.SceneDirectorLibrary.compile_director(g);assert not get(g,'needs_compile')
 shots=[s for s in kept if get(s,'type')==N.CAMERA_SWITCH];assert len(shots)==1 and get(shots[0],'blend_seconds')==0
 returns=[s for s in kept if get(s,'type')==N.CAMERA_RETURN];assert not returns
 assert u.EditorAssetLibrary.save_loaded_asset(g,False)
 (O/'camera-installed.json').write_text(json.dumps({'backup':str(backup),'initial_camera':'B','initial_blend':0,'qte_target_seconds':4.,'camera_move':{'start':str(pose),'end':str(end),'rotation':str(rot),'duration':.8},'instant_return':True},indent=2))
except:(O/'camera-install-error.txt').write_text(traceback.format_exc());u.log_error(traceback.format_exc())
finally:u.SystemLibrary.quit_editor()
