import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'shoulder_source.blend'));o=bpy.data.objects['Heroine_DetailFinish2'];ids=json.loads((P.parent/'DetailFinish2/components.json').read_text())['ids'];faces=[list(p.vertices) for p in o.data.polygons if all(ids[v]==14 for v in p.vertices)];bvh=BVHTree.FromPolygons([v.co for v in o.data.vertices],faces)
for z in [.887,.891,.895,.9,.904,.908]:
 print(z,[(x,tuple(bvh.ray_cast(Vector((x,-.15,z)),Vector((0,1,0)))[0] or Vector((0,0,0)))) for x in [-.047,-.041,-.035,-.029,-.023,-.017]])
