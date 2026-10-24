import bpy,json
from pathlib import Path
from mathutils import Vector
s=bpy.context.scene;o=bpy.data.objects["Heroine_FullSurfaceReview"];c=bpy.data.objects["Phone_Portrait_ReviewCube"]
groups={g.index for g in o.vertex_groups if g.name.startswith("spine") or g.name=="pelvis"}
indices=[v.index for v in o.data.vertices if sum(g.weight for g in v.groups if g.group in groups)>.5]
rows=[]
for frame in [73,91,120,150,180,206]:
 s.frame_set(frame);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 corners=[c.matrix_world@Vector(v) for v in c.bound_box]
 lo=[min(v[j] for v in corners) for j in range(3)];hi=[max(v[j] for v in corners) for j in range(3)]
 body=[o.matrix_world@me.vertices[i].co for i in indices]
 overlap=[v for v in body if lo[0]-.005<=v.x<=hi[0]+.005 and lo[2]-.005<=v.z<=hi[2]+.005]
 shift=max(0,hi[1]-min(v.y for v in overlap)+.005) if overlap else 0
 rows.append({"frame":frame,"forward_clearance_m":shift})
 ev.to_mesh_clear()
(Path(bpy.data.filepath).parent/"torso_clearance.json").write_text(json.dumps(rows,indent=2))
print("TORSO_CLEARANCE",json.dumps(rows),flush=True)
