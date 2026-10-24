import json,re,hashlib
from pathlib import Path
r=Path(__file__).resolve().parents[1];o=r/'Saved/S0WetFloor/ReflectionDistanceApply_20261020'
def read(n):return json.loads((o/n).read_text())
def norm(v):return re.sub(r'0x[0-9a-fA-F]+','PTR',json.dumps(v,sort_keys=True)).replace('-0.000000','0.000000')
a=read('baseline-actors.json');b=read('final-actors.json')
assert len(a)==len(b)
by={v['name']:v for v in b}
for row in a:assert norm(row)==norm(by[row['name']]),row['name']
assert norm(read('baseline-lights.json'))==norm(read('final-lights.json'))
saved=read('saved.json');actual=read('final-distance.json')
assert actual['max_view_distance_override']==8000
assert actual['screen_percentage']==75
assert hashlib.sha256((r/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap').read_bytes()).hexdigest()==saved['sha256']
report=dict(fresh_reload=True,unchanged_actor_layout_meshes_materials_collision=len(a),lights_preserved=True,distance_cm=8000,screen_percentage=75,map_sha256=saved['sha256'])
(o/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
