import unreal as u
P=lambda o,k:o.get_editor_property(k)
a=u.load_asset('/Game/SceneDirector/School/DA_S0_Opening');ss=list(P(a,'steps'))
turns=[s for s in ss if P(s,'type')==u.DirectorNodeType.CHARACTER_MOVE and abs(P(s,'duration')-.7)<.01];assert len(turns)==1
for s in [ss[47],ss[54],turns[0]]:
 pts=list(P(s,'motion_points'))
 for p in pts:
  r=P(p,'rotation');r.z+=90;p.set_editor_property('rotation',r)
 s.set_editor_property('motion_points',pts)
a.set_editor_property('steps',ss);result=str(u.SceneDirectorLibrary.compile_director(a));assert '생성 완료' in result;assert u.EditorAssetLibrary.save_loaded_asset(a,False);u.log(result)
