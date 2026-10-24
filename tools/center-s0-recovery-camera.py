import unreal as u
a=u.load_asset('/Game/SceneDirector/School/DA_S0_Opening');ss=list(a.get_editor_property('steps'));s=ss[72]
assert s.get_editor_property('type')==u.DirectorNodeType.CAMERA_MOVE
r=s.get_editor_property('rotation');r.set_editor_property('value',u.Vector(0,-55,139));s.set_editor_property('rotation',r)
a.set_editor_property('steps',ss);result=str(u.SceneDirectorLibrary.compile_director(a));assert '생성 완료' in result,result
assert u.EditorAssetLibrary.save_loaded_asset(a,False);u.log('S0_RECOVERY_CENTERED '+result)
