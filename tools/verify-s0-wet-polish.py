"""Validate saved-map invariants against the pre-polish scene; no mutations."""
import json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'Saved/S0WetFloor/Polish_20261017'
before=json.loads((O/'baseline-actors.json').read_text());after=json.loads((O/'final-actors.json').read_text())
by={a['name']:a for a in after};errors=[]
floor_labels={'classroom_start_floor_'+str(i) for i in range(1,9)}
allowed=floor_labels|{'S0_WetFloor_ShallowWater'}
def clean(s):return re.sub(r'0x[0-9A-Fa-f]+','PTR',s)
for a in before:
 b=by.get(a['name'])
 if b is None:errors.append('Missing '+a['label']);continue
 for field in ['transform','collision']:
  if clean(str(a[field]))!=clean(str(b[field])):errors.append('Changed '+field+' '+a['label'])
 bm={m['name']:m for m in b['meshes']}
 for m in a['meshes']:
  n=bm.get(m['name'])
  if not n or m['mesh']!=n['mesh']:errors.append('Changed mesh '+a['label']);continue
  if a['label'] not in allowed and m['materials']!=n['materials']:errors.append('Changed material '+a['label'])
for a in after:
 if a['label'] in floor_labels and not any('M_S0_WoodCaveFloor_V2' in p for m in a['meshes'] for p in m['materials']):errors.append('Floor not polished '+a['label'])
 if a['label']=='S0_WetFloor_ShallowWater':
  if a['collision']:errors.append('Water collision enabled')
  if not any('M_S0_ShallowWater_V2' in p for m in a['meshes'] for p in m['materials']):errors.append('Water not polished')
new=[a['label'] for a in after if a['name'] not in {b['name'] for b in before}]
for label in new:
 if not label.startswith('S0_WetPolish_'):errors.append('Unexpected addition '+label)
for a in after:
 if a['label'].startswith('S0_WetPolish_Shore') and a['collision']:errors.append('Shore collision enabled '+a['label'])
bl=json.loads((O/'baseline-lights.json').read_text());al={a['label']:a for a in json.loads((O/'final-lights.json').read_text())}
for l in bl:
 if l['label']=='ART_SchoolCave_CeilingKey':continue
 if l['label'] not in al or clean(json.dumps(l,sort_keys=True))!=clean(json.dumps(al[l['label']],sort_keys=True)):errors.append('Unexpected light change '+l['label'])
if al.get('ART_SchoolCave_CeilingKey',{}).get('values',{}).get('cast_shadows')!='True':errors.append('Ceiling shadows missing')
mats=json.loads((O/'final-materials.json').read_text())
if 'DEFAULT_LIT' not in mats['M_S0_ShallowWater_V2']['shading_model']:errors.append('Incorrect thin-film shader')
if mats['M_S0_ShallowWater_V2']['water_outputs']!=0:errors.append('Stale water shader output')
report=dict(preserved_actors=len(before),new_actors=new,errors=errors,scope='Transforms, existing collision, meshes and out-of-scope materials; actual play and GPU performance not tested')
(O/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
assert not errors

