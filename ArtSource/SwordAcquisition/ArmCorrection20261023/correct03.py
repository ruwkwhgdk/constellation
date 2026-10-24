import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).parent
S=P.parent/'GripRevision20261023/Heroine_Sword_RightUpper06.blend'
bpy.ops.wm.open_mainfile(filepath=str(S));s=bpy.context.scene;r=bpy.data.objects['Heroine_Rebuild_GameSkeleton'];sw=bpy.data.objects['Sword_proxy']
rest={b.name:b.matrix_local.copy() for b in r.data.bones}
def frame(y,x):
 y=y.normalized();x=(x-y*x.dot(y)).normalized();z=x.cross(y).normalized();return Matrix((x,y,z)).transposed().to_quaternion()
def rotation(v,x,d,n):return frame(d,n)@frame(v,x).inverted()
def angle(a,b,axis):return math.atan2(axis.dot(a.cross(b)),a.dot(b))
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def solve(side,world):
 names=['upperarm_'+side,'upperarm_twist_01_'+side,'lowerarm_'+side,'lowerarm_twist_01_'+side,'hand_'+side];a,t,b,d,h=names
 R,E,H=[world[n].translation.copy() for n in [a,b,h]]
 ra,rt,rb,rd,rh=[rest[n].translation for n in names];u=rb-ra;v=rh-rb;v1=rd-rb;v2=rh-rd;L1=u.length;L2=v.length
 reach=H-R;dist=reach.length;axis=reach.normalized();p=E-R-axis*(E-R).dot(axis);p.normalize();other=axis.cross(p)
 xup=rest[a].to_3x3().col[0];xlo=rest[b].to_3x3().col[0]
 hd=world[h].to_quaternion()@rest[h].to_quaternion().inverted();palmx=hd@xlo;palmy=hd@v.normalized()
 clav=r.pose.bones[a].parent.name;parentbasis=world[clav]@rest[clav].inverted()
 def candidate(theta,details=False):
  l2=L2;pole=p*math.cos(theta)+other*math.sin(theta)
  for it in range(5 if details else 2):
   x=(L1*L1-l2*l2+dist*dist)/(2*dist);height=math.sqrt(max(1e-10,L1*L1-x*x));el=R+axis*x+pole*height
   uv=(el-R).normalized();lv=(H-el).normalized();normal=uv.cross(lv)
   if normal.length<1e-5:normal=(world[a].to_quaternion()@Vector((1,0,0)))
   normal.normalize();qu=rotation(u,xup,uv,normal);qb=rotation(v,xlo,lv,normal)
   bx=qb@xlo;dx=palmx-lv*palmx.dot(lv)
   if dx.length<1e-6:dx=bx
   dx.normalize();roll=angle(bx.normalized(),dx,lv)
   qp=Quaternion(lv,roll*.5)@qb;qd=Quaternion(lv,roll)@qb
   combined=qp@v1+qd@v2;l2=combined.length
  corr=combined.rotation_difference(H-el);qp=corr@qp;qd=corr@qd
  local=(parentbasis.inverted().to_quaternion()@qu);_,ut=local.to_swing_twist('Y')
  bend=lv.angle(palmy);score=.8*roll*roll+12*bend*bend+.16*theta*theta+.12*ut*ut+4*max(0,abs(roll)-1.45)**2
  if details:return (score,el,qu,qp,qd,roll,bend)
  return score
 candidates=[(candidate(math.radians(i)),math.radians(i)) for i in range(-175,181,5)];_,theta=min(candidates)
 for step in [1,.2]:
  _,theta=min((candidate(theta+math.radians(i*step)),theta+math.radians(i*step)) for i in range(-5,6))
 score,el,qu,qp,qd,roll,bend=candidate(theta,True)
 # Full source hand transform remains locked. Proximal/distal segment rotations share pronation.
 result={}
 for n,point,q in [(a,R,qu),(t,R+qu@(rt-ra),qu),(b,el,qp),(d,el+qp@v1,qd)]:
  result[n]=Matrix.LocRotScale(point,q@rest[n].to_quaternion(),world[n].to_scale())
 result[h]=world[h].copy()
 return result,{'pole_shift_deg':math.degrees(theta),'forearm_roll_deg':math.degrees(roll),'wrist_axis_deg':math.degrees(bend),'closure_mm':((el+qp@v1+qd@v2)-H).length*1000}
rr=Matrix(json.loads((P/'natural_grip.json').read_text()))
# Record natural finger articulation from the preserved original, never its mesh.
bpy.ops.wm.open_mainfile(filepath='C:/Users/User/.codex/visualizations/2026/09/19/01a0ba3a-ca09-73e0-b9bd-7084c8f3096b/SwordPull_Heroine01/Heroine_Sword_Final03.blend');s=bpy.context.scene;r=bpy.data.objects['Heroine_Rebuild_GameSkeleton'];s.frame_set(100)
finger_names=[b.name for b in r.pose.bones if b.name.endswith('_r') and any(b.name.startswith(k+'_') for k in ['thumb','index','middle','ring','pinky'])];finger_pose={n:r.pose.bones[n].matrix_basis.copy() for n in finger_names}
bpy.ops.wm.open_mainfile(filepath=str(S));s=bpy.context.scene;r=bpy.data.objects['Heroine_Rebuild_GameSkeleton'];sw=bpy.data.objects['Sword_proxy'];s.frame_set(13);approach=r.pose.bones['hand_r'].matrix.copy()
records={};props={};metrics=[]
for f in range(1,740):
 s.frame_set(f);world={b.name:b.matrix.copy() for b in r.pose.bones};base={b.name:b.matrix_basis.copy() for b in r.pose.bones};props[f]=sw.matrix_world.copy()
 if 415<f<490:
  desired=r.matrix_world.inverted()@props[f]@rr
  root=world['upperarm_r'].translation;elbow=desired.translation-(desired.to_quaternion()@rest['hand_r'].to_quaternion().inverted())@(rest['hand_r'].translation-rest['lowerarm_r'].translation)
  delta=root+(elbow-root).normalized()*(rest['lowerarm_r'].translation-rest['upperarm_r'].translation).length-elbow
  props[f].translation+=r.matrix_world.to_3x3()@delta*(math.sin(math.pi*(f-415)/75)**2)
 wtgrip=smooth((f-13)/36);desired=r.matrix_world.inverted()@props[f]@rr
 if f<=13:desired=world['hand_r'].copy()
 elif f<49:desired=Matrix.LocRotScale(world['hand_r'].translation.lerp(desired.translation,wtgrip),approach.to_quaternion().slerp(desired.to_quaternion(),wtgrip),desired.to_scale())
 world['hand_r']=desired
 for n in finger_names:
  a=base[n];b=finger_pose[n];r.pose.bones[n].matrix_basis=Matrix.LocRotScale(a.translation.lerp(b.translation,wtgrip),a.to_quaternion().slerp(b.to_quaternion(),wtgrip),a.to_scale().lerp(b.to_scale(),wtgrip))
 # Left contact follows the adjusted sword while it is still holding it.
 if 415<f<447:
  delta=r.matrix_world.inverted().to_3x3()@(props[f].translation-sw.matrix_world.translation);world['hand_l'].translation+=delta*(1-smooth((f-415)/32))
 for side in ['r','l']:
  mats,m=solve(side,world)
  # Preserve the calm start, ease into coherent solution by initial grasp.
  wt=smooth((f-1)/36)
  for n,mat in mats.items():
   if n.startswith('hand_'):continue
   old=world[n];loc=old.translation.lerp(mat.translation,wt);q=old.to_quaternion().slerp(mat.to_quaternion(),wt);r.pose.bones[n].matrix=Matrix.LocRotScale(loc,q,mat.to_scale());bpy.context.view_layer.update()
  r.pose.bones['hand_'+side].matrix=world['hand_'+side];bpy.context.view_layer.update()
  metrics.append({'frame':f,'side':side,**m})
 records[f]={b.name:b.matrix_basis.copy() for b in r.pose.bones}
 if f%100==0:print('SOLVED',f,flush=True)
# independent solver yields identical duplicate poses, explicitly preserve exact boundary identity
for dst,src in [(172,100),(244,100),(355,415),(595,523),(667,523)]:
 records[dst]={n:m.copy() for n,m in records[src].items()};props[dst]=props[src].copy()
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
main,smain=bake('Sword_ArmCorrection_Continuous',range(1,740))
ranges={'Approach':(1,100),'BraceLoop':(100,172),'ExtractRecover':(244,355),'ReleaseLeft':(415,457),'Raise':(457,523),'RaisedHoldLoop':(523,595),'Lower':(667,739)}
manifest={}
for name,(start,end) in ranges.items():
 a,b=bake('Sword_'+name+'_ArmCorrection',range(start,end+1));manifest[name]={'action':a.name,'sword_action':b.name,'range':[start,end],'duration':(end-start)/30,'loop':name.endswith('Loop')}
r.animation_data.action=main;sw.animation_data.action=smain;s.frame_set(100);s.frame_start=1;s.frame_end=739
bpy.ops.wm.save_as_mainfile(filepath=str(P/'Heroine_Sword_ArmCorrection03.blend'));(P/'clips.json').write_text(json.dumps(manifest,indent=2));(P/'solve_metrics03.json').write_text(json.dumps(metrics,indent=2));print('CANDIDATE_SAVED',flush=True)




