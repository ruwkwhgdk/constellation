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

s.frame_set(100);rr=sw.matrix_world.inverted()@r.matrix_world@r.pose.bones['hand_r'].matrix
out=[]
for deg in [-120,-90,-60,60,90,120,180]:
 for f in [49,100,278]:
  s.frame_set(f);world={b.name:b.matrix.copy() for b in r.pose.bones};rel=Matrix.Rotation(math.radians(deg),4,'Z')@rr;world['hand_r']=r.matrix_world.inverted()@sw.matrix_world@rel
  mats,m=solve('r',world);out.append({'grip':deg,'frame':f,**m})
print(json.dumps(out,indent=2));(P/'grip_scan.json').write_text(json.dumps(out,indent=2))
