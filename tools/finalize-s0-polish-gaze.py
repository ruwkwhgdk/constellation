import unreal as u,json
from pathlib import Path
P=lambda o,k:o.get_editor_property(k)
def sp(o,**kw):
 for k,v in kw.items():o.set_editor_property(k,v)
 return o
a=u.load_asset('/Game/SceneDirector/School/DA_S0_Opening');ss=list(P(a,'steps'))
assert not any(str(P(P(s,'action_parameters'),'identifier'))=='StopGirlLook' for s in ss)
n=sp(u.SceneDirectorLibrary.make_director_step(u.DirectorNodeType.GAME_ACTION),action_key=P(ss[59],'action_key'),action_parameters=sp(u.DirectorActionParameters(),identifier='StopGirlLook'),next_nodes=P(ss[66],'next_nodes'))
sp(ss[66],next_nodes=[P(n,'id')]);ss.append(n);sp(a,steps=ss)
result=str(u.SceneDirectorLibrary.compile_director(a));assert '생성 완료' in result,result
assert u.EditorAssetLibrary.save_loaded_asset(a,False)
u.log('S0_GAZE_STOP_APPLIED '+result)
