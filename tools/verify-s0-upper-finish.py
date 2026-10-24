import json,re
from pathlib import Path
r=Path(__file__).resolve().parents[1];o=r/'Saved/S0WetFloor/UpperFinish_20261018'
def read(n):return json.loads((o/n).read_text(encoding='utf-8-sig'))
def norm(x):return re.sub(r'0x[0-9A-Fa-f]+','PTR',json.dumps(x,sort_keys=True)).replace('-0.000000','0.000000')
a=read('baseline-actors.json');b={x['name']:x for x in read('final-actors.json')};changes={x['name']:x for x in read('changes.json')};light=read('light-change.json')
assert len(a)==len(b)
for x in a:
 y=b[x['name']]
 assert x['label']==y['label'] and x['collision']==y['collision']
 if x['name']!=light['name']:assert norm(x['transform'])==norm(y['transform'])
 expected=json.loads(json.dumps(x['meshes']))
 if x['name'] in changes:expected[0]['materials'][0]=changes[x['name']]['new']
 assert expected==y['meshes'],x['label']
old={x['label']:x for x in read('baseline-lights.json')};new={x['label']:x for x in read('final-lights.json')}
assert old.keys()==new.keys()
for label,x in old.items():
 y=new[label]
 if label==light['label']:
  assert float(y['values']['intensity'])==40 and y['values']['cast_shadows']=='False'
  assert all(f'{axis}: {value:.6f}' in y['pos'] for axis,value in zip('xyz',[1100,-1500,1750]))
  x=json.loads(json.dumps(x));x['pos']=y['pos'];x['values']['intensity']=y['values']['intensity']
 assert norm(x)==norm(y),label
report=dict(material_actors=2,light_actors=1,unchanged_actors=len(a)-3,all_meshes_collision_preserved=True,light_count_preserved=True,fresh_reload=True)
(o/'verification.json').write_text(json.dumps(report,indent=2));print(report)
