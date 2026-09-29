import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parent;O=R/'DetailFinish2';bpy.ops.wm.open_mainfile(filepath=str(O/'pinhem_stage.blend'));bpy.context.preferences.filepaths.save_version=0
ob=bpy.data.objects['Heroine_DetailFinish2'];me=ob.data;cid=json.loads((O/'components.json').read_text())['ids'];original=[v.co.copy() for v in me.vertices];normals=[n.vector.copy() for n in me.corner_normals];adj=[set() for v in me.vertices]
for e in me.edges:a,b=e.vertices;adj[a].add(b);adj[b].add(a)
tree=BVHTree.FromPolygons(original,[p.vertices[:] for p in me.polygons if cid[p.vertices[0]]==12]);changed={};root=0
# Taper the disconnected rear strand root into the supporting hair cap.
for v in me.vertices:
 if cid[v.index]!=25 or v.co.z<.969:continue
 h,n,i,d=tree.ray_cast(Vector((v.co.x,1,v.co.z)),Vector((0,-1,0)))
 if h is None or not .015<h.y<.09:continue
 w=min(1,max(0,(v.co.z-.969)/.012));v.co.y=v.co.y*(1-w)+(h.y-.00012)*w;changed[v.index]=w;root+=1
# Small isolated rear cut, distinct from the long intentional strand separations.
cx,cz=.044,.921;near=[v for v in me.vertices if cid[v.index]==12 and v.co.y>.03 and abs(v.co.x-cx)<.010 and abs(v.co.z-cz)<.012]
ring=[v for v in near if .55<((v.co.x-cx)/.010)**2+((v.co.z-cz)/.012)**2<1.5]
patch=0
if len(ring)>8:
 A=np.array([[1,(v.co.x-cx)/.01,(v.co.z-cz)/.01,((v.co.x-cx)/.01)**2,((v.co.x-cx)*(v.co.z-cz))/.0001,((v.co.z-cz)/.01)**2] for v in ring]);b=np.array([v.co.y for v in ring]);fit=np.linalg.lstsq(A,b,rcond=None)[0]
 for v in near:
  r2=((v.co.x-cx)/.006)**2+((v.co.z-cz)/.008)**2
  if r2>=1:continue
  x,z=(v.co.x-cx)/.01,(v.co.z-cz)/.01;target=float(np.dot([1,x,z,x*x,x*z,z*z],fit));delta=max(-.001,min(.001,target-v.co.y))*(1-r2)**2;v.co.y+=delta;changed[v.index]=1-r2;patch+=1
# Smooth only pocket endpoint folds and hem thickness irregularities, preserving their openings and pleats.
weights={};pocket=0;hem=0
for v in me.vertices:
 x,y,z=v.co
 if cid[v.index]==4 and y<-.06:
  r2=((abs(x)-.0405)/.0035)**2+((z-.607)/.006)**2
  if r2<1:weights[v.index]=.34*(1-r2);pocket+=1
 if cid[v.index]==1:
  ang=math.atan2(y/.075,x/.101);edge=.4625+.014*abs(math.cos(ang))**1.5
  if z<edge+.0025:weights[v.index]=.14;hem+=1
for iteration in range(4):
 coords=[v.co.copy() for v in me.vertices]
 for i,w in weights.items():
  if not adj[i]:continue
  d=sum((coords[j] for j in adj[i]),Vector())/len(adj[i])-coords[i]
  if d.length>.00035:d*=.00035/d.length
  me.vertices[i].co+=d*w;changed[i]=.5
me.update()
for i,l in enumerate(me.loops):
 if l.vertex_index in changed:normals[i]=normals[i].lerp(me.vertices[l.vertex_index].normal,min(.6,changed[l.vertex_index])).normalized()
me.normals_split_custom_set(normals)
(O/'geometry_changes.json').write_text(json.dumps({'rear_root_vertices':root,'rear_local_patch_vertices':patch,'pocket_end_vertices':pocket,'hem_vertices':hem,'modified_vertices':len(changed),'max_displacement':max((v.co-original[v.index]).length for v in me.vertices)},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(O/'geometry_stage.blend'))
sc=bpy.context.scene;sc.cycles.samples=20
for name,loc,target,scale in [('head_back',(0,3,.89),(0,0,.89),.28),('skirt',(0,-3,.505),(0,0,.505),.34),('eye',(-.034,-3,.902),(-.034,0,.902),.10)]:
 cam=sc.camera;cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.resolution_x=sc.render.resolution_y=1000;sc.render.filepath=str(O/'renders'/f'{name}.png');bpy.ops.render.render(write_still=True)
print('GEOMETRY_DONE',flush=True)
