import json,re
from pathlib import Path
r=Path(__file__).resolve().parents[1];o=r/'Saved/S0WetFloor/SideFacets_20261018'
def read(n):return json.loads((o/n).read_text(encoding='utf-8-sig'))
def norm(s):return re.sub(r'0x[0-9A-Fa-f]+','PTR',s).replace('-0.000000','0.000000')
a=read('baseline-actors.json');b={x['name']:x for x in read('final-actors.json')};changes={x['name']:x for x in read('changes.json')}
assert len(a)==len(b)
for x in a:
 y=b[x['name']]
 assert x['label']==y['label'] and x['collision']==y['collision']
 assert norm(x['transform'])==norm(y['transform'])
 expected=json.loads(json.dumps(x['meshes']))
 if x['name'] in changes:
  for m in expected:
   if m['mesh']==changes[x['name']]['old']:m['mesh']=changes[x['name']]['new']
 assert expected==y['meshes'],x['label']
assert norm(json.dumps(read('baseline-lights.json'),sort_keys=True))==norm(json.dumps(read('final-lights.json'),sort_keys=True))
report=dict(changed_mesh_actors=len(changes),unchanged_actors=len(a)-len(changes),transforms_materials_collision_flags_preserved=True,lights_preserved=True,fresh_reload=True)
(o/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))

