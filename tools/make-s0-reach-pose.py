"""Local two-bone reach on the current ExitFall, preserving contact and all other tracks."""
import json,math
from pathlib import Path
import numpy as np
O=Path(__file__).resolve().parents[1]/'ArtSource/SchoolOpening/ReachPose'
d=json.loads((O/'source.json').read_text());rows=d['rows']
def norm(x):return x/np.linalg.norm(x)
def mul(a,b):
 av,bv=np.array(a[:3]),np.array(b[:3]);return np.r_[a[3]*bv+b[3]*av+np.cross(av,bv),a[3]*b[3]-av@bv]
def inv(q):return np.r_[-np.array(q[:3]),q[3]]
def between(a,b):
 a,b=norm(a),norm(b);return norm(np.r_[np.cross(a,b),1+a@b])
def rotate(q,v):return mul(mul(q,np.r_[v,0]),inv(q))[:3]
def matrixq(m):
 # Stable largest-diagonal conversion, xyzw quaternion convention.
 k=np.array([[m[0,0]-m[1,1]-m[2,2],m[1,0]+m[0,1],m[2,0]+m[0,2],m[2,1]-m[1,2]],
 [m[1,0]+m[0,1],m[1,1]-m[0,0]-m[2,2],m[2,1]+m[1,2],m[0,2]-m[2,0]],
 [m[2,0]+m[0,2],m[2,1]+m[1,2],m[2,2]-m[0,0]-m[1,1],m[1,0]-m[0,1]],
 [m[2,1]-m[1,2],m[0,2]-m[2,0],m[1,0]-m[0,1],m[0,0]+m[1,1]+m[2,2]]])/3
 values,vectors=np.linalg.eigh(k);return vectors[:,np.argmax(values)]
def slerp(a,b,w):
 a,b=norm(np.array(a)),norm(np.array(b));dot=a@b
 if dot<0:b=-b;dot=-dot
 if dot>.9995:return norm((1-w)*a+w*b)
 angle=math.acos(max(-1,min(1,dot)));return (math.sin((1-w)*angle)*a+math.sin(w*angle)*b)/math.sin(angle)
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
tracks={n:[] for n in ['clavicle_r','upperarm_r','lowerarm_r','hand_r']};audit=[]
for f,row in enumerate(rows):
 t=f/30;w=smooth((t-.05)/.3)*(1-smooth((t-.72)/.33))
 if w<1e-8:
  for n in tracks:tracks[n].append(row[n]['local'])
  continue
 A,B,C=[np.array(row[n]['world']['t']) for n in ['upperarm_r','lowerarm_r','hand_r']]
 original_A=A.copy();anchor=np.array(row['clavicle_r']['world']['t']);clav_length=np.linalg.norm(A-anchor)
 A=anchor+norm((1-w)*(A-anchor)+w*norm(np.array([6.,6.,4.]))*clav_length)*clav_length
 clavicle=mul(between(original_A-anchor,A-anchor),row['clavicle_r']['world']['q'])
 l1,l2=np.linalg.norm(B-original_A),np.linalg.norm(C-B)
 # Reach into the unchanged first-person lens, rather than an arbitrary world height.
 cam=[(0,3030,170,-10),(1/3,3030,170,-10),(1/3+.4,3005,135,-22),(1/3+1.1,2945,65,-28),(1/3+2,2890,42,-8)]
 for c0,c1 in zip(cam,cam[1:]):
  if c0[0]<=t<=c1[0]:
   alpha=(t-c0[0])/(c1[0]-c0[0]);cx,cz,pitch=[c0[j]+alpha*(c1[j]-c0[j]) for j in [1,2,3]];break
 pitch=math.radians(pitch)
 world_x=cx-math.cos(pitch)*20-math.sin(pitch)*2
 world_z=cz+math.sin(pitch)*20-math.cos(pitch)*2
 desired=np.array([3060-world_x,6.,world_z-.15])
 target=(1-w)*C+w*desired
 direction=norm(target-A);dist=min(np.linalg.norm(target-A),l1+l2-.8);target=A+direction*dist
 pole=norm((B-original_A)-direction*((B-original_A)@direction))
 along=(l1*l1-l2*l2+dist*dist)/(2*dist);height=math.sqrt(max(0,l1*l1-along*along));elbow=A+direction*along+pole*height
 upper=mul(between(B-original_A,elbow-A),row['upperarm_r']['world']['q'])
 lower=mul(between(C-B,target-elbow),row['lowerarm_r']['world']['q'])
 assert d['parents']['lowerarm_r']=='upperarm_twist_01_r'
 lower_parent=mul(upper,row['upperarm_twist_01_r']['local']['q'])
 hand_parent=mul(lower,row['lowerarm_twist_01_r']['local']['q'])
 hand_q=row['hand_r']['world']['q']
 fwd=norm(rotate(inv(hand_q),np.array(row['middle_01_r']['world']['t'])-C))
 side=rotate(inv(hand_q),np.array(row['index_01_r']['world']['t'])-np.array(row['pinky_01_r']['world']['t']));side=norm(side-fwd*(side@fwd))
 local_basis=np.column_stack([fwd,side,np.cross(fwd,side)])
 aim=norm(np.array([1.,0.,-.18]));thumb=np.array([0.,-1.,0.]);target_basis=np.column_stack([aim,thumb,np.cross(aim,thumb)])
 hand=slerp(hand_q,matrixq(target_basis@local_basis.T),w)
 parent=row[d['parents']['clavicle_r']]['world']['q']
 for n,q in [('clavicle_r',mul(inv(parent),clavicle)),('upperarm_r',mul(inv(clavicle),upper)),('lowerarm_r',mul(inv(lower_parent),lower)),('hand_r',mul(inv(hand_parent),hand))]:
  v=dict(row[n]['local']);v['q']=norm(q).tolist();tracks[n].append(v)
 audit.append(dict(t=t,weight=w,target=target.tolist(),elbow=elbow.tolist(),lengths=[float(l1),float(l2)]))
(O/'reach-tracks.json').write_text(json.dumps(dict(fps=30,tracks=tracks,audit=audit)))
print('Reach keys:',len(rows),'Modified tracks:',list(tracks),'Original floor-contact pose restored by 1.0667s')
