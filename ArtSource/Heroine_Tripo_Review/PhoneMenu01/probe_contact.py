import bpy,json
from pathlib import Path
from collections import Counter
from mathutils import Vector
s=bpy.context.scene;s.frame_set(46)
m=bpy.data.objects["Heroine_FullSurfaceReview"];p=bpy.data.objects["Phone_ReviewCube"]
groups={g.index:g.name for g in m.vertex_groups}
left={v.index:max(v.groups,key=lambda g:g.weight).group for v in m.data.vertices if v.groups and sum(g.weight for g in v.groups if groups[g.group].endswith("_l") and groups[g.group].startswith(("hand_","palm_","thumb_","index_","middle_","ring_","pinky_")))>0.5}
ev=m.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
vs={i:p.matrix_world.inverted()@ev.matrix_world@me.vertices[i].co for i in left};ev.to_mesh_clear()
rows=[]
for offset in (0,.004,.008,.012,.016,.020,.024):
 inside=[i for i,v in vs.items() if min(.035-abs(v.x),.006-abs(v.y-offset),.07-abs(v.z))>.001]
 rows.append({"offset":offset,"count":len(inside),"bones":dict(Counter(groups[left[i]] for i in inside))})
Path(__file__).with_name("contact_probe.json").write_text(json.dumps(rows,indent=2))
print(rows,flush=True)
