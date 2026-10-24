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
 reach=H-R;dist=reach.length;axis=reach.normalized();outward=Vector((-1,0,0) if side=='r' else (1,0,0));p=outward-axis*outward.dot(axis);p.normalize();other=axis.cross(p)
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
  local=rest[a].to_quaternion().inverted()@parentbasis.inverted().to_quaternion()@qu@rest[a].to_quaternion();_,ut=local.to_swing_twist('Y')
  bend=lv.angle(palmy);score=.8*roll*roll+12*bend*bend+.16*theta*theta+.8*ut*ut+4*max(0,abs(roll)-1.45)**2
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
r.animation_data.action=bpy.data.actions.new('Pose08');r.animation_data.action.use_fake_user=True
# Read source poses once, then write selected solved poses into the preview action.
action=r.animation_data.action;source=bpy.data.actions['Sword_GripRevision_Continuous'];records={}
for f in [100,278,523]:
 r.animation_data.action=source;s.frame_set(f);original={b.name:b.matrix.copy() for b in r.pose.bones}
 wtlean=(1-smooth((f-244)/66));spine=r.pose.bones['spine_01'];m=spine.matrix.copy();q=Quaternion((1,0,0),math.radians(20)*wtlean)@Quaternion((0,1,0),math.radians(-20)*wtlean);spine.matrix=Matrix.LocRotScale(m.translation,q@m.to_quaternion(),m.to_scale());bpy.context.view_layer.update()
 world={b.name:b.matrix.copy() for b in r.pose.bones}
 for side in ['r','l']:world['hand_'+side]=original['hand_'+side].copy()
 for side in ['r','l']:
  mats,met=solve(side,world)
  for n,mat in mats.items():r.pose.bones[n].matrix=mat;bpy.context.view_layer.update()
  print('POSE',f,side,met,flush=True)
 records[f]={b.name:b.matrix_basis.copy() for b in r.pose.bones}
r.animation_data.action=action
for f,rec in records.items():
 for b in r.pose.bones:
  b.matrix_basis=rec[b.name];b.rotation_mode='QUATERNION'
  for prop in ['location','rotation_quaternion','scale']:b.keyframe_insert(prop,frame=f)
s.frame_set(100);bpy.ops.wm.save_as_mainfile(filepath=str(P/'Pose08.blend'))
