import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).parent
S=Path('C:/Users/User/.codex/visualizations/2026/09/19/01a0ba3a-ca09-73e0-b9bd-7084c8f3096b/SwordPull_Heroine01/Heroine_Sword_Final03.blend')
bpy.ops.wm.open_mainfile(filepath=str(S));s=bpy.context.scene;r=bpy.data.objects['Heroine_Rebuild_GameSkeleton'];sw=bpy.data.objects['Sword_proxy'];W=r.matrix_world.copy();Wi=W.inverted()
def upd():bpy.context.view_layer.update()
def world(n):return W@r.pose.bones[n].matrix
def pos(n):return world(n).translation
def orient(n,q):
 m=world(n);r.pose.bones[n].matrix=Wi@Matrix.LocRotScale(m.translation,q,m.to_scale());upd()
def aim(n,child,d):
 m=world(n);orient(n,(pos(child)-m.translation).rotation_difference(d)@m.to_quaternion())
def ik(side,target,desired):
 a='upperarm_'+side;b='lowerarm_'+side;c='hand_'+side;root=pos(a);mid=pos(b);end=pos(c);l1=(mid-root).length;l2=(end-mid).length;v=target-root;dist=max(abs(l1-l2)+.001,min(v.length,l1+l2-.001));v.normalize();pp=mid-root-v*(mid-root).dot(v)
 if pp.length<1e-6:pp=Vector((1,0,0))-v*v.x
 pp.normalize();hm=world(c);local=hm.inverted()@pos('middle_01_'+side);direction=(desired.to_3x3()@local).normalized();wanted=target-direction*l2-root;wanted-=v*wanted.dot(v)
 if wanted.length>1e-6:pp=pp.lerp(wanted.normalized(),.75).normalized()
 x=(l1*l1-l2*l2+dist*dist)/(2*dist);h=math.sqrt(max(0,l1*l1-x*x));aim(a,b,v*x+pp*h);aim(b,c,target-pos(b));return (pos(c)-target).length
def mix(a,b,t):
 la,qa,sa=a.decompose();lb,qb,sb=b.decompose();return Matrix.LocRotScale(la.lerp(lb,t),qa.slerp(qb,t),sa.lerp(sb,t))
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
base={};swords={}
for f in range(1,740):
 s.frame_set(f);base[f]={b.name:b.matrix_basis.copy() for b in r.pose.bones};swords[f]=sw.matrix_world.copy()
fingers=lambda side:[b.name for b in r.pose.bones if b.name.endswith('_'+side) and any(b.name.startswith(n+'_') for n in ['thumb','index','middle','ring','pinky'])]
s.frame_set(415);relR=sw.matrix_world.inverted()@world('hand_r');relR.translation.z+=.12;endSword=world('hand_r')@relR.inverted()
s.frame_set(100);relL=sw.matrix_world.inverted()@world('hand_l');relL.translation.z-=.09
print('RELATIONS',list(relR.translation),list(relL.translation),flush=True)
records={};props={};metrics=[]
for f in range(1,740):
 for n,m in base[f].items():r.pose.bones[n].matrix_basis=m
 sw.matrix_world=swords[f];upd()
 # Remove the regrip interval by matching extraction end to release start through a body transition near recovery.
 if 310<f<=355:
  t=smooth((f-310)/45)
  for n in base[f]:r.pose.bones[n].matrix_basis=mix(base[f][n],base[415][n],t)
  sw.matrix_world=mix(swords[f],endSword,t);upd()
 if f>=355 and f<=415:
  for n,m in base[415].items():r.pose.bones[n].matrix_basis=m
  sw.matrix_world=endSword;upd()
 if f>=415:
  sw.matrix_world=world('hand_r')@relR.inverted();upd()
 else:
  for it in range(8):
   for side,rel in [('r',relR),('l',relL)]:
    a=pos('upperarm_'+side);b=pos('lowerarm_'+side);c=pos('hand_'+side);limit=(b-a).length+(c-b).length-.008;desired=(sw.matrix_world@rel).translation;v=desired-a
    if v.length>limit:
     mat=sw.matrix_world.copy();mat.translation-=v.normalized()*(v.length-limit);sw.matrix_world=mat;upd()
 for side,rel,template in [('r',relR,415),('l',relL,100)]:
  wt=smooth((f-13)/36)
  if side=='l' and f>415:wt=1-smooth((f-415)/32)
  if wt>0:
   desired=mix(world('hand_'+side),sw.matrix_world@rel,wt)
   error=0
   if not (side=='r' and f>=415):error=ik(side,desired.translation,desired);orient('hand_'+side,desired.to_quaternion())
   for n in fingers(side):r.pose.bones[n].matrix_basis=mix(base[f][n],base[template][n],wt)
   upd();metrics.append({'frame':f,'side':side,'reach_error_mm':error*1000})
 records[f]={b.name:b.matrix_basis.copy() for b in r.pose.bones};props[f]=sw.matrix_world.copy()
 if f%100==0:print('SOLVED',f,flush=True)
# Force actual boundary pose and sword equality after solving contact.
records[355]={n:m.copy() for n,m in records[415].items()};props[355]=props[415].copy()
def bake(label,indices):
 r.animation_data.action=bpy.data.actions.new(label);sw.animation_data.action=bpy.data.actions.new(label+'_Prop');prev={}
 for f,src in enumerate(indices,1):
  for b in r.pose.bones:
   b.matrix_basis=records[src][b.name];b.rotation_mode='QUATERNION'
   if b.name in prev and b.rotation_quaternion.dot(prev[b.name])<0:b.rotation_quaternion.negate()
   prev[b.name]=b.rotation_quaternion.copy()
   for prop in ['location','rotation_quaternion','scale']:b.keyframe_insert(prop,frame=f)
  sw.matrix_world=props[src]
  if 'sword' in prev and sw.rotation_quaternion.dot(prev['sword'])<0:sw.rotation_quaternion.negate()
  prev['sword']=sw.rotation_quaternion.copy()
  for prop in ['location','rotation_quaternion','scale']:sw.keyframe_insert(prop,frame=f)
 for o in [r,sw]:
  act=o.animation_data.action;act.use_fake_user=True
  for layer in act.layers:
   for strip in layer.strips:
    for slot in act.slots:
     bag=strip.channelbag(slot)
     if bag:
      for fc in bag.fcurves:
       for k in fc.keyframe_points:k.interpolation='LINEAR'
 return r.animation_data.action,sw.animation_data.action
main,smain=bake('Sword_GripRevision_Continuous',range(1,740))
ranges={'Approach':(1,100),'BraceLoop':(100,172),'ExtractRecover':(244,355),'ReleaseLeft':(415,457),'Raise':(457,523),'RaisedHoldLoop':(523,595),'Lower':(667,739)}
manifest={}
for name,(start,end) in ranges.items():
 a,b=bake('Sword_'+name+'_GripRevision',range(start,end+1));manifest[name]={'action':a.name,'sword_action':b.name,'range':[start,end],'duration':(end-start)/30,'loop':name.endswith('Loop')}
r.animation_data.action=main;sw.animation_data.action=smain;s.frame_set(100);s.frame_start=1;s.frame_end=739
bpy.ops.wm.save_as_mainfile(filepath=str(P/'Heroine_Sword_RightUpper02.blend'));(P/'clips.json').write_text(json.dumps(manifest,indent=2));(P/'reach_metrics.json').write_text(json.dumps(metrics,indent=2));print('CANDIDATE_SAVED',flush=True)


