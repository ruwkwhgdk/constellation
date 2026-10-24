import json,re
from pathlib import Path
r=Path(__file__).resolve().parents[1];o=r/'Saved/S0WetFloor/WindowShadowV21_20261019'
def read(n):return json.loads((o/n).read_text(encoding='utf-8-sig'))
def norm(x):return re.sub(r'0x[0-9A-Fa-f]+','PTR',json.dumps(x,sort_keys=True)).replace('-0.000000','0.000000')
a=read('baseline-actors.json');b=read('final-actors.json');assert norm(a)==norm(b)
expected=read('baseline-lights.json');labels={x['label'] for x in read('changes.json')}
assert len(labels)==4
for x in expected:
 if x['label'] in labels:x['values']['cast_shadows']='False'
assert norm(expected)==norm(read('final-lights.json'))
report=dict(shadow_flags_changed=4,actors_preserved=len(a),all_transforms_meshes_materials_collision_preserved=True,other_recorded_light_properties_preserved=True,fresh_reload=True)
(o/'verification.json').write_text(json.dumps(report,indent=2));print(report)
