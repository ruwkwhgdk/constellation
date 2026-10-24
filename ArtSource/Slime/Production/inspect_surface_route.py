import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
s=bpy.context.scene;s.frame_set(1);b=bpy.data.objects['Slime_Body'];cam=s.camera
tree=BVHTree.FromPolygons([v.co for v in b.data.vertices],[list(p.vertices) for p in b.data.polygons])
corners=cam.data.view_frame(scene=s);left=min(p.x for p in corners);right=max(p.x for p in corners)
bottom=min(p.y for p in corners);top=max(p.y for p in corners)
rows=[]
for x,y in [(320,177),(326,190),(336,214),(341,230),(351,255),(362,285),(374,325),(379,356),(377,380),(374,392)]:
    local=Vector((left+(right-left)*x/548,top-(top-bottom)*y/502,0))
    origin=cam.matrix_world@local;direction=cam.matrix_world.to_quaternion()@Vector((0,0,-1))
    loc,n,idx,d=tree.ray_cast(origin,direction,100)
    rows.append({'pixel':[x,y],'location':list(loc) if loc else None,'normal':list(n) if n else None,'face':idx})
for name,p in [('tip',Vector((.36,-.35,1.28)))]:
    uv=world_to_camera_view(s,cam,p);rows.append({'name':name,'pixel':[uv.x*548,(1-uv.y)*502]})
out=Path(__file__).resolve().parent
(out/'route-probe.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows,indent=2))
