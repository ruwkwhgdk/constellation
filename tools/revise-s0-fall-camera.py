"""Review stage 3: forward-facing fall, then blend to the real gameplay camera."""
import unreal as u,json,shutil,hashlib
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0FallCameraReview';O.mkdir(exist_ok=True)
P=lambda o,k:o.get_editor_property(k)
def sp(o,**kw):
 for k,v in kw.items():o.set_editor_property(k,v)
 return o
f=R/'Content/SceneDirector/School/DA_S0_Opening.uasset';b=O/'before-DA_S0_Opening.uasset';assert not b.exists();shutil.copy2(f,b);digest=hashlib.sha256(f.read_bytes()).hexdigest()
a=u.load_asset('/Game/SceneDirector/School/DA_S0_Opening');ss=list(P(a,'steps'));N=u.DirectorNodeType
assert str(P(P(ss[69],'action_parameters'),'identifier'))=='Fall'
assert P(ss[70],'type')==N.CAMERA_MOVE and P(ss[72],'type')==N.CAMERA_MOVE
before={str(i):dict(pos=str(P(P(ss[i],'destination'),'value')),rot=str(P(P(ss[i],'rotation'),'value'))) for i in [68,70,72]}
path=[(0,(3030,0,170),(0,-10,180)),(.4,(3005,0,135),(2,-22,180)),(1.1,(2945,0,65),(4,-28,180)),(2,(2890,0,42),(3,-8,180))]
pts=[sp(u.DirectorMotionPoint(),time=t,position=u.Vector(*pos),rotation=u.Vector(*rot),scale=u.Vector(1,1,1),interpolation=u.DirectorPathInterpolation.LINEAR) for t,pos,rot in path]
sp(ss[70],motion_points=pts,use_motion_path=True,duration=2.,wait_for_completion=True)
sp(P(ss[70],'destination'),value=u.Vector(2890,0,42))
d=P(ss[70],'destination');sp(d,value=u.Vector(2890,0,42));sp(ss[70],destination=d)
r=P(ss[70],'rotation');sp(r,value=u.Vector(3,-8,180));sp(ss[70],rotation=r)
# Keep the pre-fall camera on the same centre line; eliminate lateral motion.
d=P(ss[68],'destination');sp(d,value=u.Vector(3030,0,170));r=P(ss[68],'rotation');sp(r,value=u.Vector(0,-10,180));sp(ss[68],destination=d,rotation=r)
sp(ss[71],duration=.2)
ret=sp(u.SceneDirectorLibrary.make_director_step(N.CAMERA_RETURN),duration=3.5,wait_for_completion=True,next_nodes=P(ss[72],'next_nodes'),editor_position=P(ss[72],'editor_position'))
sp(ss[71],next_nodes=[P(ret,'id')]);ss[72]=ret
# Camera has already returned; unlock only after the complete GetUp and handoff.
sp(ss[79],duration=.1)
# Match the approved model-forward correction across the later escape, without changing timing/path.
for i in [67,73,74]:
 pts=list(P(ss[i],'motion_points'))
 for p in pts:
  v=P(p,'rotation');v.z+=90;sp(p,rotation=v)
 sp(ss[i],motion_points=pts)
sp(a,steps=ss);result=str(u.SceneDirectorLibrary.compile_director(a));assert '생성 완료' in result,result
assert hashlib.sha256(f.read_bytes()).hexdigest()==digest
assert u.EditorAssetLibrary.save_loaded_asset(a,False)
(O/'applied.json').write_text(json.dumps(dict(before=before,path=path,camera_return_seconds=3.5,compile=result),ensure_ascii=False,indent=2),encoding='utf8');u.log('S0_FALL_CAMERA_APPLIED '+result)
