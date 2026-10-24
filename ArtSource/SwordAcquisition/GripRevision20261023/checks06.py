import json,math,hashlib
from pathlib import Path
P=Path(__file__).parent;D=P/'Delivery06';d=json.loads((D/'motion.json').read_text());source=Path(d['source']);baseline=json.loads((P/'snapshot_before.json').read_text());old=json.loads(Path('C:/Users/User/.codex/visualizations/2026/09/19/01a0ba3a-ca09-73e0-b9bd-7084c8f3096b/SwordPull_Heroine01/UnrealApply01/motion.json').read_text());checks=json.loads((P/'delivery_checks06.json').read_text())
def rot(q,v):
 x,y,z,w=q;vx,vy,vz=v;tx=2*(y*vz-z*vy);ty=2*(z*vx-x*vz);tz=2*(x*vy-y*vx)
 return [vx+w*tx+y*tz-z*ty,vy+w*ty+z*tx-x*tz,vz+w*tz+x*ty-y*tx]
def mul(a,b):
 x,y,z,w=a;X,Y,Z,W=b;return [w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z]
def qdiff(a,b):return 2*math.degrees(math.acos(min(1,abs(sum(x*y for x,y in zip(a,b)))/(sum(x*x for x in a)*sum(x*x for x in b))**.5)))
vals=[];rotation_steps={}
for name,c in d['clips'].items():
 rotation_steps[name]={}
 for n in ['upperarm_r','lowerarm_r','hand_r','upperarm_l','lowerarm_l','hand_l']:
  qs=[r[n]['q'] for r in c['rows']];v=[qdiff(a,b) for a,b in zip(qs,qs[1:])];rotation_steps[name][n]={'max_degrees':max(v),'sample':v.index(max(v))+1}
 for f,(row,sw) in enumerate(zip(c['rows'],c['sword'])):
  if name=='Approach' and f<48:continue
  q=sw['q'];qi=[-q[0],-q[1],-q[2],q[3]];v=rot(qi,[x-y for x,y in zip(row['hand_r']['t'],sw['t'])]);vals.append((name,f,[x/z for x,z in zip(v,sw['s'])],mul(qi,row['hand_r']['q'])))
ref=vals[0];contact=max(math.dist(ref[2],v[2]) for v in vals);rotation=max(qdiff(ref[3],v[3]) for v in vals)
checks.update(bone_count=len(d['parents']),parents_identical=d['parents']==old['parents'],source_sha256_matches_export=hashlib.sha256(source.read_bytes()).hexdigest()==d['source_sha256'],original_preserved=hashlib.sha256(Path(old['source']).read_bytes()).hexdigest()==baseline['source']['sha256'],right_contact_max_translation_delta_cm=contact,right_contact_max_rotation_delta_degrees=rotation,rotation_steps=rotation_steps)
assert checks['source_sha256_matches_export'] and checks['original_preserved'] and checks['parents_identical'];assert contact<.001 and rotation<.01;assert checks['first_sword_max_delta']==0;assert all(v['bones']==0 and v['sword']==0 for v in checks['boundaries'].values());assert max(v['max_degrees'] for c in rotation_steps.values() for v in c.values())<15
(P/'delivery_checks06.json').write_text(json.dumps(checks,indent=2));print(json.dumps({'contact_cm':contact,'contact_degrees':rotation,'approach_rotation':rotation_steps['Approach'],'source':d['source_sha256'],'original_preserved':checks['original_preserved']},indent=2))
