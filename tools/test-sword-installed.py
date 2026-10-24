import unreal as u,json,traceback
from pathlib import Path
if '-SwordVerifySuite' in u.SystemLibrary.get_command_line():u.EditorPythonScripting.set_keep_python_script_alive(True)
O=Path(u.Paths.project_dir())/'Saved/SwordAcquisition/IntegrationTests';O.mkdir(parents=True,exist_ok=True)
try:
 stage=u.load_class(None,'/Script/Constellation.SwordAcquisitionStage')
 assert stage,'Sword acquisition runtime stage is not installed'
 graph=u.load_asset('/Game/SceneDirector/School/DA_SwordAcquisition')
 assert graph,'Sword acquisition director graph is not installed'
 assert not graph.get_editor_property('needs_compile'),'Sword graph is not compiled'
 steps=list(graph.get_editor_property('steps'));N=u.DirectorNodeType
 cues=[str(s.get_editor_property('action_parameters').get_editor_property('identifier')) for s in steps if s.get_editor_property('type')==N.GAME_ACTION]
 assert cues.index('ItemUI')<cues.index('Commit'),cues
 assert any(str(s.get_editor_property('dialogue_text'))=='녹슨 검을 얻었습니다.' for s in steps)
 ui_index=next(i for i,s in enumerate(steps) if s.get_editor_property('type')==N.GAME_ACTION and str(s.get_editor_property('action_parameters').get_editor_property('identifier'))=='ItemUI')
 commit_index=next(i for i,s in enumerate(steps) if s.get_editor_property('type')==N.GAME_ACTION and str(s.get_editor_property('action_parameters').get_editor_property('identifier'))=='Commit')
 dialogue_index=next(i for i,s in enumerate(steps) if s.get_editor_property('type')==N.DIALOGUE)
 end_index=next(i for i,s in enumerate(steps) if s.get_editor_property('type')==N.END)
 assert ui_index<dialogue_index<commit_index<end_index,'Acquisition order mismatch'
 assert not any(s.get_editor_property('type')==N.CAMERA_RETURN for s in steps),'Return must use immediate End restore'
 shots=[s for s in steps if s.get_editor_property('type')==N.CAMERA_SWITCH]
 assert len(shots)==1 and str(shots[0].get_editor_property('camera_key'))=='B' and shots[0].get_editor_property('blend_seconds')==0
 moves=[s for s in steps if s.get_editor_property('type')==N.CAMERA_MOVE]
 assert len(moves)==1 and str(moves[0].get_editor_property('camera_key'))=='B'
 definition=u.load_asset('/Game/Constellation/UI/ItemAcquisition/DA_RustySword');assert definition
 assert str(definition.get_editor_property('presentation').get_editor_property('name'))=='녹슨 검'
 animation=u.load_asset('/Game/SceneDirector/School/DA_SwordAcquisitionAnimation');assert animation
 clips=animation.get_editor_property('clips')
 expected={'Approach','BraceLoop','ExtractRecover','ReleaseLeft','Raise','RaisedHoldLoop','Lower'}
 assert {str(k) for k in clips}==expected
 assert animation.get_editor_property('sample_rate')==30
 for name,clip in clips.items():
  assert clip.get_editor_property('montage')
  assert len(clip.get_editor_property('sword_samples'))>30
  assert clip.get_editor_property('loop')==(str(name) in ['BraceLoop','RaisedHoldLoop'])
 (O/'installed-result.json').write_text(json.dumps({'passed':True,'cues':cues}),encoding='utf8')
except:(O/'installed-result.json').write_text(json.dumps({'passed':False,'error':traceback.format_exc()}),encoding='utf8')
finally:
 if '-SwordVerifySuite' not in u.SystemLibrary.get_command_line():u.SystemLibrary.quit_editor()

