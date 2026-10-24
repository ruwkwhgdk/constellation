import json,math,hashlib
from pathlib import Path
P=Path(__file__).parent;d=json.loads((P/'Delivery06/motion.json').read_text());old=json.loads(Path('C:/Users/User/.codex/visualizations/2026/09/19/01a0ba3a-ca09-73e0-b9bd-7084c8f3096b/SwordPull_Heroine01/UnrealApply01/motion.json').read_text())
def angle(a,b):return math.degrees(math.acos(max(-1,min(1,sum(x*y for x,y in zip(a,b))/(sum(x*x for x in a)*sum(x*x for x in b))**.5))))
def sub(a,b):return [x-y for x,y in zip(a,b)]
def diff(a,b):return max(abs(x-y) for k in ['t','q','s'] for x,y in zip(a[k],b[k]))
out={'source':d['source'],'source_sha256':d['source_sha256'],'clips':{},'boundaries':{},'first_sword_max_delta':diff(d['clips']['Approach']['sword'][0],old['clips']['Approach']['sword'][0])}
for name,c in d['clips'].items():
 row={'duration':c['duration'],'samples':len(c['rows']),'wrist':{}}
 for side in ['r','l']:
  vals=[]
  for f,bones in enumerate(c['rows']):
   a,e,w,m=[bones[n+'_'+side]['t'] for n in ['upperarm','lowerarm','hand','middle_01']];vals.append((angle(sub(w,e),sub(m,w)),f))
  row['wrist'][side]={'max_axis_angle':max(vals)[0],'sample':max(vals)[1]}
 if name.endswith('Loop'):
  row['loop_endpoint_delta']=max(diff(c['rows'][0][n],c['rows'][-1][n]) for n in c['rows'][0])
 out['clips'][name]=row
for a,b in [('Approach','BraceLoop'),('BraceLoop','ExtractRecover'),('ExtractRecover','ReleaseLeft'),('ReleaseLeft','Raise'),('Raise','RaisedHoldLoop'),('RaisedHoldLoop','Lower')]:
 ca=d['clips'][a];cb=d['clips'][b];out['boundaries'][a+'>'+b]={'bones':max(diff(ca['rows'][-1][n],cb['rows'][0][n]) for n in ca['rows'][-1]),'sword':diff(ca['sword'][-1],cb['sword'][0])}
(P/'delivery_checks06.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
