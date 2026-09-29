import bpy
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(R/'FaceClean/Heroine_FaceClean.blend'));o=bpy.data.objects['Heroine_FaceClean'];tree=BVHTree.FromPolygons([v.co for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons])
for x,z in [(-.027,.882),(-.024,.88),(-.023,.878),(-.03,.883),(-.027,.879)]:
 q=Vector((x,-1,z));hits=[]
 for i in range(6):
  h,n,idx,d=tree.ray_cast(q,Vector((0,1,0)))
  if h is None:break
  hits.append((h.y,idx,o.data.materials[o.data.polygons[idx].material_index].name,list(n)));q=h+Vector((0,.000001,0))
 print('HITS',x,z,hits)
