import bpy,json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
R=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(R/'FaceClean/Heroine_FaceClean.blend'));o=bpy.data.objects['Heroine_FaceClean'];ps=[p for p in o.data.polygons if o.data.materials[p.material_index].name=='Face_Skin_Clean'];tree=BVHTree.FromPolygons([v.co for v in o.data.vertices],[list(p.vertices) for p in ps]);hits=[]
for i in range(100):
 for j in range(80):
  x=-.042+i*.0003;z=.873+j*.0002;q=Vector((x,-.1,z));h,n,idx,d=tree.ray_cast(q,Vector((0,1,0)))
  if h is None:continue
  h2,n2,idx2,d2=tree.ray_cast(h+Vector((0,.000002,0)),Vector((0,1,0)))
  if h2 is not None and h2.y<-.01:hits.append((x,z,h.y,h2.y,ps[idx].index,ps[idx2].index))
print('DOUBLE_HITS',len(hits));print(hits[:15]);(R/'FaceClean/diagnostics/overlap.json').write_text(json.dumps(hits))
