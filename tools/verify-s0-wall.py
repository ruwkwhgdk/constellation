"""Saved scene validation against exact pre-pass actor/material manifest."""
import json,re
from pathlib import Path
O=Path(__file__).resolve().parents[1]/'Saved/S0WetFloor/WallPass_20261017'
read=lambda n:json.loads((O/n).read_text())
clean=lambda s:re.sub(r'0x[0-9A-Fa-f]+','PTR',str(s))
before=read('baseline-actors.json');after=read('final-actors.json');by={a['name']:a for a in after}
allowed={(r[0],r[2],r[3]):r[5] for r in read('allowed-material-changes.json')}
transforms={a['name']:a['after'] for a in read('allowed-transforms.json')}
errors=[]
assert len(transforms)==5
for a in before:
 b=by.get(a['name'])
 if not b:errors.append('Missing '+a['label']);continue
 for k in ['transform','collision']:
  if clean(transforms.get(a['name'],a[k]) if k=='transform' else a[k])!=clean(b[k]):errors.append('Changed '+k+' '+a['label'])
 bm={c['name']:c for c in b['meshes']}
 for c in a['meshes']:
  d=bm.get(c['name'])
  if not d or d['mesh']!=c['mesh']:errors.append('Mesh changed '+a['label']);continue
  expected=[allowed.get((a['name'],c['name'],i),m) for i,m in enumerate(c['materials'])]
  if d['materials']!=expected:errors.append('Unexpected material '+a['label'])
oldnames={a['name'] for a in before}
new=[a for a in after if a['name'] not in oldnames]
if new:errors.append('Unexpected new actors')
for a in new:
 if not a['label'].startswith('S0_Art_'):errors.append('Unexpected addition '+a['label'])
 if a['meshes'] and a['collision']:errors.append('New collision '+a['label'])
bl=read('baseline-lights.json');al={a['label']:a for a in read('final-lights.json')}
for a in bl:
 if a['label'] not in al or clean(json.dumps(a,sort_keys=True))!=clean(json.dumps(al[a['label']],sort_keys=True)):errors.append('Existing light changed '+a['label'])
log=(O/'final.log').read_text(errors='replace')
for token in ['Failed to compile Material','LogPython: Error','LogMaterial: Error']:
 if token in log:errors.append(token)
for name in ['concept','floor','reverse','floor-offset']:
 if not (O/('final-'+name+'.png')).exists():errors.append('Missing capture '+name)
report={'preserved_actors':len(before),'material_slots':len(allowed),'added':[a['label'] for a in new],'errors':errors,'limits':'Actor transforms, mesh/material and actor collision flags; no gameplay or GPU performance validation.'}
(O/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));assert not errors
