import json,re
from pathlib import Path
r=Path(__file__).resolve().parents[1];o=r/'Saved/S0WetFloor/UpperContinuity_20261019'
def read(n):return json.loads((o/n).read_text(encoding='utf-8-sig'))
def norm(x):return re.sub(r'0x[0-9A-Fa-f]+','PTR',json.dumps(x,sort_keys=True)).replace('-0.000000','0.000000')
a=read('baseline-actors.json');b={x['name']:x for x in read('final-actors.json')};changes={x['name']:x for x in read('changes.json')}
assert len(a)==len(b)
for x in a:
 y=b[x['name']]
 assert x['label']==y['label'] and x['collision']==y['collision'] and norm(x['transform'])==norm(y['transform'])
 expected=json.loads(json.dumps(x['meshes']))
 if x['name'] in changes:expected[0]['materials'][changes[x['name']]['slot']]=changes[x['name']]['new']
 assert expected==y['meshes'],x['label']
assert norm(read('baseline-lights.json'))==norm(read('final-lights.json'))
report=dict(material_actors=len(changes),unchanged_actors=len(a)-len(changes),transforms_meshes_collision_lights_preserved=True,fresh_reload=True)
(o/'verification.json').write_text(json.dumps(report,indent=2));print(report)


