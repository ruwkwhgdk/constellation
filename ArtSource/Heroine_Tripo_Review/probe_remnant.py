import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parent;O=R/'ContourRepair';bpy.ops.wm.open_mainfile(filepath=str(O/'Heroine_ContourRepair_OverlapFixed.blend'));ob=bpy.data.objects['Heroine_ContourRepair'];me=ob.data;tree=BVHTree.FromPolygons([v.co for v in me.vertices],[tuple(p.vertices) for p in me.polygons])
for px,py in [(758,621),(742,590),(699,575)]:
 x=-.034+(px/1100-.5)*.1;z=.902+(.5-py/1100)*.1;start=Vector((x,-1,z));hits=[]
 print('SCENE',px,py,bpy.context.scene.ray_cast(bpy.context.evaluated_depsgraph_get(),start,Vector((0,1,0))))
 for j in range(6):
  h,n,i,di=tree.ray_cast(start,Vector((0,1,0)))
  if h is None:break
  p=me.polygons[i];hits.append({'y':h.y,'face':i,'material':me.materials[p.material_index].name,'normal':tuple(n),'vertices':[[vi,*me.vertices[vi].co] for vi in p.vertices]});start=h+Vector((0,.00001,0))
 print('RAY',px,py,json.dumps(hits),flush=True)
