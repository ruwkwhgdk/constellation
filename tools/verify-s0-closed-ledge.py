import json,re,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'Saved/S0WetFloor/ClosedLedge_20261018'
def read(name):return json.loads((out/name).read_text(encoding='utf-8-sig'))
def clean(x):
 if isinstance(x,str):return re.sub(r'0x[0-9A-Fa-f]+','PTR',x).replace('-0.000000','0.000000')
 if isinstance(x,list):return [clean(v) for v in x]
 if isinstance(x,dict):return {k:clean(v) for k,v in x.items()}
 return x
before={r['name']:clean(r) for r in read('baseline-actors.json')}
after={r['name']:clean(r) for r in read('final-actors.json')}
changes={r['name']:r for r in read('changes.json')}
assert before.keys()==after.keys(),'Unexpected actor additions/removals'
for name,old in before.items():
 new=after[name]
 if name not in changes:assert old==new,name
 else:
  assert old['label']==new['label'] and old['collision']==new['collision']==False
  assert len(old['meshes'])==len(new['meshes'])==1
  assert old['meshes'][0]['materials']==new['meshes'][0]['materials']
  assert new['meshes'][0]['mesh']==changes[name]['new_mesh']
assert clean(read('baseline-lights.json'))==clean(read('final-lights.json'))
digest=hashlib.sha256((root/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap').read_bytes()).hexdigest()
assert digest==read('saved.json')['sha256']
report=dict(saved_reload_verified=True,changed_actor_count=len(changes),unchanged_actor_count=len(before)-len(changes),lighting_unchanged=True,sha256=digest,post_change_PIE_retest=False,post_change_GPU_measurement=False)
(out/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
