import hashlib,re,shutil
review=(R/'tools/review-s0-shallow-rock.py').read_text()
exec(review[review.index('rows=[];lights=[]'):review.index('cmd=u.SystemLibrary')])
def norm(x):return re.sub(r'0x[0-9A-Fa-f]+','PTR',json.dumps(x,sort_keys=True)).replace('-0.000000','0.000000')
assert norm(rows)==norm(json.loads((O/'baseline-actors.json').read_text())),'Actor changes outside shadows'
expected=json.loads((O/'baseline-lights.json').read_text());labels={x['label'] for x in json.loads((O/'changes.json').read_text())}
for x in expected:
 if x['label'] in labels:x['values']['cast_shadows']='False'
assert norm(lights)==norm(expected),'Unexpected light changes'
mapfile=R/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
assert hashlib.sha256(mapfile.read_bytes()).hexdigest()==json.loads((O/'session.json').read_text())['map_sha256']
shutil.copy2(mapfile,O/'AbandonedSchool.before.umap')
assert u.EditorLoadingAndSavingUtils.save_map(u.EditorLevelLibrary.get_editor_world(),'/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
(O/'saved.json').write_text(json.dumps(dict(shadow_lights=4,sha256=hashlib.sha256(mapfile.read_bytes()).hexdigest()),indent=2))
u.SystemLibrary.quit_editor()
