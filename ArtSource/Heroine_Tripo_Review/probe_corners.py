import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(R/'ContourRepair/Heroine_ContourRepair_Retouch.blend'));ob=bpy.data.objects['Heroine_ContourRepair'];me=ob.data;tree=BVHTree.FromPolygons([v.co for v in me.vertices],[tuple(p.vertices) for p in me.polygons])
adj=[[] for v in me.vertices]
for e in me.edges:
 a,b=e.vertices;adj[a].append(b);adj[b].append(a)
ids=[-1]*len(me.vertices);counts=[]
for v in me.vertices:
 if ids[v.index]>=0:continue
 cid=len(counts);stack=[v.index];ids[v.index]=cid;cnt=0
 while stack:
  a=stack.pop();cnt+=1
  for b in adj[a]:
   if ids[b]<0:ids[b]=cid;stack.append(b)
 counts.append(cnt)
for px,py in [(735,584),(749,604),(766,625),(756,567),(744,536),(424,548),(442,544),(754,604),(535,812),(544,833),(450,755)]:
 x=-.034+(px/1100-.5)*.1;z=.902+(.5-py/1100)*.1;h,n,i,di=tree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
 if h:
  p=me.polygons[i];print('PROBE',px,py,'hit',tuple(h),'mat',me.materials[p.material_index].name,'component_size',counts[ids[p.vertices[0]]],'face',i,'vertices',list(p.vertices),flush=True)
json.dump({'component_ids':ids,'component_sizes':counts},open(R/'ContourRepair/diagnostics/new_components.json','w'))
