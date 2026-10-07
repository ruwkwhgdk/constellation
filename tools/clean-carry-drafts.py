"""Remove only this feature's unused initial retarget drafts, after play verification."""
import json
from pathlib import Path
import unreal as u
out=Path(u.Paths.project_dir()).resolve()/'Saved/CarryReview'
report=json.loads((out/'play-verification.json').read_text(encoding='utf-8'))
assert 'error' not in report and all(x['passed'] for x in report['checks'])
rows=[]
for name in ('Pickup','Place','Throw','Hold','Aim'):
    path='/Game/Constellation/Characters/Heroine/Base/Animation/Carry/AS_Carry_'+name
    if not u.EditorAssetLibrary.does_asset_exist(path): continue
    refs=u.EditorAssetLibrary.find_package_referencers_for_asset(path,True)
    if refs: rows.append({'asset':path,'kept_referencers':list(refs)}); continue
    assert u.EditorAssetLibrary.delete_asset(path),path
    rows.append({'asset':path,'deleted':True})
(out/'draft-cleanup.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
u.log('CARRY_DRAFT_CLEANUP '+json.dumps(rows))
