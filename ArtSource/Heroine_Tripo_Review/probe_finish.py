import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(R/'DetailFinish/stage3.blend'));o=bpy.data.objects['Heroine_DetailFinish'];m=o.data;t=BVHTree.FromPolygons([v.co for v in m.vertices],[p.vertices[:] for p in m.polygons]);out=[]
for px,py in [(500,447),(560,446),(620,456),(650,464),(658,626),(620,637),(520,660),(770,925),(910,928)]:
 x=-.034+(px/1000-.5)*.1;z=.902+(.5-py/1000)*.1;hit,n,i,d=t.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
 if hit:out.append({'pixel':[px,py],'point':list(hit),'normal':list(n),'face':i,'material':m.materials[m.polygons[i].material_index].name,'verts':[list(m.vertices[j].co) for j in m.polygons[i].vertices]})
(R/'DetailFinish/probes.json').write_text(json.dumps(out,indent=2));print(json.dumps(out),flush=True)
