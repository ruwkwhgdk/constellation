import unreal as u
P=lambda o,k:o.get_editor_property(k)
a=u.load_asset('/Game/SceneDirector/School/DA_S0_Opening');ss=list(P(a,'steps'))
# A path's final key must hold through the dialogue gap; linear 360 -> 0
# interpolation caused a full unwanted spin before the escape path begins.
for i in [54,70]:
 pts=list(P(ss[i],'motion_points'));pts[-1].set_editor_property('interpolation',u.DirectorPathInterpolation.CONSTANT);ss[i].set_editor_property('motion_points',pts)
a.set_editor_property('steps',ss);result=str(u.SceneDirectorLibrary.compile_director(a));assert '생성 완료' in result,result
assert u.EditorAssetLibrary.save_loaded_asset(a,False);u.log('S0_ARRIVAL_HOLD_FIXED '+result)
