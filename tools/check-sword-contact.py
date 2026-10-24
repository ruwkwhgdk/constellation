"""Check exported contact/clip-boundary contracts; does not judge joint anatomy."""
import json,math,sys,hashlib
from pathlib import Path
P=Path(sys.argv[1]);d=json.loads((P/'motion.json').read_text());t=json.loads((P/'sword_tracks.json').read_text())
def mul(a,b):
 x,y,z,w=a;X,Y,Z,W=b;return [w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z]
def inv(q):return [-q[0],-q[1],-q[2],q[3]]
def rel(a,b):return {'t':mul(mul(inv(b['q']),[*[x-y for x,y in zip(a['t'],b['t'])],0]),b['q'])[:3],'q':mul(inv(b['q']),a['q'])}
def dist(a,b):return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
def angle(a,b):return math.degrees(2*math.acos(min(1,abs(sum(x*y for x,y in zip(a,b)))/math.sqrt(sum(x*x for x in a)*sum(x*x for x in b)))))
order=['Approach','BraceLoop','ExtractRecover','ReleaseLeft','Raise','RaisedHoldLoop','Lower'];assert set(d['clips'])==set(order)
errors=[];ref=None;translation=rotation=0
for name in order:
 c=d['clips'][name];sw=t['clips'][name]['sword'];assert len(c['rows'])==len(sw)
 for i,(row,sword) in enumerate(zip(c['rows'],sw)):
  if name=='Approach' and i<49:continue
  hand=rel(row['hand_r'],sword)
  if ref is None:ref=hand
  translation=max(translation,dist(hand['t'],ref['t']));rotation=max(rotation,angle(hand['q'],ref['q']))
assert translation<.05,('right contact translation cm',translation)
assert rotation<.1,('right contact rotation deg',rotation)
boundaries=[]
for a,b in zip(order,order[1:]):
 A=d['clips'][a]['rows'][-1];B=d['clips'][b]['rows'][0];pos=max(dist(A[n]['t'],B[n]['t']) for n in A);rot=max(angle(A[n]['q'],B[n]['q']) for n in A);sa=t['clips'][a]['sword'][-1];sb=t['clips'][b]['sword'][0]
 assert pos<.05 and rot<.1,(a,b,pos,rot)
 assert dist(sa['t'],sb['t'])<.05 and angle(sa['q'],sb['q'])<.1,(a,b,'sword')
 boundaries.append({'from':a,'to':b,'bone_translation_cm':pos,'bone_angle_degrees':rot})
row=d['clips']['BraceLoop']['rows'][0];sword=t['clips']['BraceLoop']['sword'][0];rz=rel(row['hand_r'],sword)['t'][2];lz=rel(row['hand_l'],sword)['t'][2];assert rz>lz,(rz,lz)
held=d['clips']['RaisedHoldLoop']['rows'][0];helds=t['clips']['RaisedHoldLoop']['sword'][0];thumb=[a-b for a,b in zip(held['thumb_03_r']['t'],held['thumb_01_r']['t'])];q=helds['q'];thumb=mul(mul(inv(q),[*thumb,0]),q)[:3];thumb_to_blade_cos=-thumb[2]/math.sqrt(sum(v*v for v in thumb));assert thumb_to_blade_cos>0,('Raised grip points thumb toward pommel',thumb_to_blade_cos)
baseline=P.parents[1]/'GripRevision20261023/Delivery'
if baseline.exists():
 old=json.loads((baseline/'motion.json').read_text());olds=json.loads((baseline/'sword_tracks.json').read_text());a=t['clips']['Approach']['sword'][0];b=olds['clips']['Approach']['sword'][0]
 assert dist(a['t'],b['t'])<.01 and angle(a['q'],b['q'])<.01,'Initial floor sword changed'
 legs=[n for n in d['parents'] if n=='pelvis' or n.startswith(('thigh_','calf_','foot_','ball_'))]
 for name in order:
  for a,b in zip(d['clips'][name]['rows'],old['clips'][name]['rows']):
   assert max(dist(a[n]['t'],b[n]['t']) for n in legs)<.01,('Lower-body movement changed',name)
report={'passed':True,'right_contact_max_cm':translation,'right_contact_max_degrees':rotation,'right_above_left_cm':rz-lz,'raised_thumb_to_blade_axis_cos':thumb_to_blade_cos,'boundaries':boundaries,'scope':'contact and boundary continuity only, not anatomical visual acceptance'}
(P/'contact-contract.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
