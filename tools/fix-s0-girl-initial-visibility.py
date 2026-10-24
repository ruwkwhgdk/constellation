import unreal as u
P=lambda o,k:o.get_editor_property(k)
a=u.load_asset('/Game/SceneDirector/School/DA_S0_Opening');s=list(P(a,'steps'))
assert str(P(P(s[5],'action_parameters'),'identifier'))=='Begin'
s[87].set_editor_property('visible',True)
n=u.SceneDirectorLibrary.make_director_step(u.DirectorNodeType.WAIT);n.set_editor_property('duration',.1);n.set_editor_property('next_nodes',P(s[5],'next_nodes'));n.set_editor_property('editor_position',u.Vector2D(1000,500));s[5].set_editor_property('next_nodes',[P(n,'id')]);s.append(n)
a.set_editor_property('steps',s);result=str(u.SceneDirectorLibrary.compile_director(a));assert '생성 완료' in result,result;assert u.EditorAssetLibrary.save_loaded_asset(a,False);u.log(result)
