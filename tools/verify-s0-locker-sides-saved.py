"""Fresh-process verification of the saved locker side camera correction."""
import unreal as u,json
from pathlib import Path
P=lambda o,k:o.get_editor_property(k)
a=u.load_asset('/Game/SceneDirector/School/DA_S0_Opening');ss=list(P(a,'steps'));assert len(ss)==125
for i,yaw in [(115,145.),(117,215.)]:
 assert P(P(ss[i],'destination'),'value').distance(u.Vector(3195,0,214.6))<.01
 assert abs(P(P(ss[i],'rotation'),'value').z-yaw)<.01
 assert abs(P(ss[i],'duration')-2.)<.001
assert P(P(ss[119],'destination'),'value').distance(u.Vector(3203,0,214.6))<.01
assert abs(P(P(ss[119],'rotation'),'value').z-180.)<.01
result=str(u.SceneDirectorLibrary.compile_director(a));assert '생성 완료' in result
(Path(u.Paths.project_dir())/'Saved/S0LockerSides/saved-verification.json').write_text(json.dumps(dict(success=True,compile=result,steps=[115,117],return_to_center_preserved=True),ensure_ascii=False,indent=2),encoding='utf8')
u.SystemLibrary.quit_editor()
