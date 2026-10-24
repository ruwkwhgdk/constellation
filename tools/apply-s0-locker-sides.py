"""Apply reviewed camera-only correction to a freshly loaded production graph."""
import unreal as u,json,shutil,hashlib
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0LockerSides';P=lambda o,k:o.get_editor_property(k)
f=R/'Content/SceneDirector/School/DA_S0_Opening.uasset';before=hashlib.sha256(f.read_bytes()).hexdigest()
b=O/'before-side-fix-DA_S0_Opening.uasset'
if not b.exists():shutil.copy2(f,b)
a=u.load_asset('/Game/SceneDirector/School/DA_S0_Opening');ss=list(P(a,'steps'));assert len(ss)==125
for i,old_yaw,new_yaw in [(115,120.,145.),(117,240.,215.)]:
 s=ss[i];assert P(s,'type')==u.DirectorNodeType.CAMERA_MOVE
 old=P(P(s,'rotation'),'value');assert abs(old.z-old_yaw)<.01,'Camera changed concurrently'
 d=P(s,'destination');assert P(d,'value').distance(u.Vector(3203,0,214.6))<.01
 d.set_editor_property('value',u.Vector(3195,0,214.6));s.set_editor_property('destination',d)
 r=P(s,'rotation');r.set_editor_property('value',u.Vector(0,0,new_yaw));s.set_editor_property('rotation',r)
a.set_editor_property('steps',ss);result=str(u.SceneDirectorLibrary.compile_director(a));assert '생성 완료' in result
assert hashlib.sha256(f.read_bytes()).hexdigest()==before,'Concurrent asset change'
assert u.EditorAssetLibrary.save_loaded_asset(a,False)
(O/'applied.json').write_text(json.dumps(dict(compile=result,changed_steps=[115,117],camera_x=3195,left_yaw=145,right_yaw=215,map_modified=False),ensure_ascii=False,indent=2),encoding='utf8')
u.SystemLibrary.quit_editor()
