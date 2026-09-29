import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'rig_unbound.blend'))
rig=bpy.data.objects['Heroine_AnimationRig'];body=bpy.data.objects['Heroine_DetailFinish2']
ids=json.loads((P.parent/'DetailFinish2/components.json').read_text())['ids']
names=[b.name for b in rig.data.bones if b.use_deform];idx={n:i for i,n in enumerate(names)}
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def blend(a,b,t):
 out={k:v*(1-t) for k,v in a.items()}
 for k,v in b.items():out[k]=out.get(k,0)+v*t
 return out
def chain_weights(p,ns,width):
 best=None
 for i,n in enumerate(ns):
  b=rig.data.bones[n];v=b.tail_local-b.head_local;l=v.length;t=(p-b.head_local).dot(v)/l**2
  d=(p-(b.head_local+v*max(0,min(1,t)))).length_squared
  if best is None or d<best[0]:best=(d,i,t,l)
 _,i,t,l=best
 w={ns[i]:1.0}
 if t*l<width and i>0:w=blend({ns[i-1]:1},w,smooth((t*l+width)/(2*width)))
 elif (1-t)*l<width and i<len(ns)-1:w=blend(w,{ns[i+1]:1},smooth((t*l-l+width)/(2*width)))
 return w
spines=['DEF-spine'+('.%03d'%i if i else '') for i in range(4)]
def torso(p):return chain_weights(p,spines,.037)
def leg(p,side):
 ns=[f'DEF-thigh.{side}',f'DEF-thigh.{side}.001',f'DEF-shin.{side}',f'DEF-shin.{side}.001',f'DEF-foot.{side}',f'DEF-toe.{side}']
 return blend(chain_weights(p,ns,.026),{'DEF-spine':1},smooth((p.z-.51)/.085))
def arm(p,side):
 ns=[f'DEF-shoulder.{side}',f'DEF-upper_arm.{side}',f'DEF-upper_arm.{side}.001',f'DEF-forearm.{side}',f'DEF-forearm.{side}.001',f'DEF-hand.{side}']
 return chain_weights(p,ns,.023)
def hand(p,side):
 scores=[]
 for f in ['thumb','f_index','f_middle','f_ring','f_pinky']:
  ns=[f'DEF-{f}.{i:02}.{side}' for i in range(1,4)]
  d=1e9
  for n in ns:
   b=rig.data.bones[n];v=b.tail_local-b.head_local;t=max(0,min(1,(p-b.head_local).dot(v)/v.length_squared));d=min(d,(p-b.head_local-v*t).length)
  scores.append((d,f,ns))
 d,f,ns=min(scores)
 amount=smooth((abs(p.x)+.015-(.354 if f=='thumb' else .378))/.018)
 return blend(arm(p,side),chain_weights(p,ns,.0045),amount)
def skirt(p):
 angle=math.atan2(p.x/.093,-p.y/.068)%(2*math.pi);u=angle/(2*math.pi)*8;i=int(u);t=u-i
 w=blend(chain_weights(p,[f'DEF-skirt_{i:02}.01',f'DEF-skirt_{i:02}.02'],.022),chain_weights(p,[f'DEF-skirt_{(i+1)%8:02}.01',f'DEF-skirt_{(i+1)%8:02}.02'],.022),smooth(t))
 return blend(w,{'DEF-spine':1},smooth((p.z-.492)/.037))
def hair(p):
 side='L' if p.x>=0 else 'R';name=('hair_back_' if p.y>.028 else 'hair_side_')+side
 # Bangs and crown remain attached to the head to preserve eye coverage.
 amount=smooth((.956-p.z)/.065)*smooth((abs(p.x)-.045)/.025) if p.y<.025 else smooth((.96-p.z)/.060)
 return blend({'DEF-spine.006':1},chain_weights(p,[f'DEF-{name}.01',f'DEF-{name}.02'],.017),amount)
for o in [o for o in bpy.context.scene.objects if o.type=='MESH']:
 if o.name.startswith('WGT-'):continue
 o.vertex_groups.clear();groups=[o.vertex_groups.new(name=n) for n in names]
 W=np.zeros((len(o.data.vertices),len(names)),dtype=np.float64)
 for v in o.data.vertices:
  p=o.matrix_world@v.co;side='L' if p.x>=0 else 'R'
  if o==body:
   c=ids[v.index]
   if c in [0,2,26]:w=leg(p,side)
   elif c==1:w=skirt(p)
   elif c in [3,32]:w=hand(p,side)
   elif c in [12,24,25,33,34]:w=hair(p)
   elif c==14:w=chain_weights(p,['DEF-spine.003','DEF-spine.004','DEF-spine.005','DEF-spine.006'],.009) if p.z<.853 else {'DEF-spine.006':1}
   elif c in [19,20,21,22,23,28,29,30,31]:w={'DEF-spine.006':1}
   elif c==4:
    a=smooth((abs(p.x)-.05)/.070)*smooth((p.z-.70)/.06)
    w=blend(torso(p),arm(p,side),a)
   else:w=torso(p)
  elif o.name=='Heroine_Pearl_Bracelet':w={'DEF-forearm.R.001':1}
  else:w={'DEF-spine.006':1}
  for n,weight in w.items():W[v.index,idx[n]]=weight
 # Smooth over actual edge connectivity, not proximity across fingers or clothing layers.
 if o==body:
  edges=np.array([e.vertices[:] for e in o.data.edges]);a=np.r_[edges[:,0],edges[:,1]];b=np.r_[edges[:,1],edges[:,0]];degree=np.bincount(a,minlength=len(W))
  mask=np.array([c in [0,1,2,3,4,26,32] for c in ids])&(degree>0)
  for _ in range(4):
   acc=np.zeros_like(W);np.add.at(acc,a,W[b]);W[mask]=.70*W[mask]+.30*acc[mask]/degree[mask,None]
 for vi,row in enumerate(W):
  keep=np.argsort(row)[-4:];total=sum(row[k] for k in keep)
  assert total>0
  for k in keep:
   if row[k]/total>1e-6:groups[k].add([vi],float(row[k]/total),'REPLACE')
 for g in list(o.vertex_groups):
  if not any(any(w.group==g.index for w in v.groups) for v in o.data.vertices):o.vertex_groups.remove(g)
 mat=o.matrix_world.copy();o.parent=rig;o.matrix_world=mat
 m=o.modifiers.new('Game Skinning','ARMATURE');m.object=rig;m.use_deform_preserve_volume=False
 print('BOUND',o.name,len(W),flush=True)
# Runtime deformation uses rotation/translation, without Rigify's nonuniform stretch scaling.
# This avoids shear that cannot be represented faithfully by an Unreal bone's TRS transform.
for b in rig.data.bones:
 if not b.use_deform:continue
 b.inherit_scale='NONE'
 c=rig.pose.bones[b.name].constraints.new('LIMIT_SCALE');c.name='Game-safe unit deform scale';c.owner_space='POSE'
 for axis in ['x','y','z']:
  setattr(c,'use_min_'+axis,True);setattr(c,'use_max_'+axis,True);setattr(c,'min_'+axis,1.0);setattr(c,'max_'+axis,1.0)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'rig_bound.blend'))
