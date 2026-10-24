import unreal as u,json,traceback
from pathlib import Path
O=Path(u.Paths.project_dir())/'Saved/SwordAcquisition/Revision20261023';O.mkdir(parents=True,exist_ok=True)
g=u.load_asset('/Game/SceneDirector/School/DA_SwordAcquisition');steps=list(g.get_editor_property('steps'));errors=[]
rows=[]
for s in steps:
 row={'type':str(s.get_editor_property('type')),'id':str(s.get_editor_property('id')),'duration':s.get_editor_property('duration'),'camera':str(s.get_editor_property('camera_key')),'blend':s.get_editor_property('blend_seconds'),'wait':s.get_editor_property('wait_for_completion'),'cue':str(s.get_editor_property('action_parameters').get_editor_property('identifier'))}
 try:row['instant_return']=s.get_editor_property('instant_camera_return')
 except:row['instant_return']='missing'
 rows.append(row)
shots=[r for r in rows if 'CAMERA_SWITCH' in r['type']]
if len(shots)!=1 or shots[0]['camera']!='B' or shots[0]['blend']!=0:errors.append('Initial/early camera is not one fixed reference cut')
if any(r['instant_return']=='missing' for r in rows):errors.append('Missing explicit instant return support')
(O/'graph-before.json').write_text(json.dumps({'steps':rows,'cameras':[{'key':str(c.get_editor_property('key')),'transform':str(c.get_editor_property('transform')),'fov':c.get_editor_property('field_of_view')} for c in g.get_editor_property('cameras')]},indent=2))
(O/'contract-red.json').write_text(json.dumps({'errors':errors},indent=2));u.SystemLibrary.quit_editor()
