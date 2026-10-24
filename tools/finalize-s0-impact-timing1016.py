import unreal as u,json
from pathlib import Path
p=Path(u.Paths.project_dir())/'Saved/S0Feedback1016Final'
a=u.load_asset('/Game/SceneDirector/School/DA_S0_Opening');s=list(a.get_editor_property('steps'));assert len(s)==125
n=u.SceneDirectorLibrary.make_director_step(u.DirectorNodeType.WAIT)
n.set_editor_property('id',s[-1].get_editor_property('id'));n.set_editor_property('next_nodes',s[-1].get_editor_property('next_nodes'));n.set_editor_property('duration',s[70].get_editor_property('duration')-1.5);s[-1]=n
a.set_editor_property('steps',s);result=str(u.SceneDirectorLibrary.compile_director(a));assert '생성 완료' in result
assert u.EditorAssetLibrary.save_loaded_asset(a,False)
(p/'timing-final.json').write_text(json.dumps({'compile':result,'impact_delay':1.5,'remaining_fall':s[-1].get_editor_property('duration')},ensure_ascii=False,indent=2),encoding='utf8')
u.SystemLibrary.quit_editor()
