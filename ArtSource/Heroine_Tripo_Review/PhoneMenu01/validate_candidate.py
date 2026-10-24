import bpy, json, sys, math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,"C:/Users/User/.codex/skills/lida-avatar-workflow/scripts")
import lida_model_tools as lida
P=Path(__file__).parent
out=Path(bpy.data.filepath).parent/"Validation";out.mkdir(exist_ok=False)
s=bpy.context.scene;r=bpy.data.objects["Heroine_Rebuild_GameSkeleton"]
meshes=[o for o in bpy.data.objects if o.type=="MESH" and o.find_armature()==r]
before=json.loads((P/"Audit01/before_snapshot.json").read_text())
after=lida.snapshot_meshes(meshes,r,source_path=bpy.data.filepath)
(out/"snapshot.json").write_text(json.dumps(after,indent=2))
comparison=lida.compare_snapshots(before,after)
(out/"compare.json").write_text(json.dumps(comparison,indent=2))
print("SAVED_DATA_COMPARISON",comparison.get("status"),flush=True)
audit=lida.audit_meshes(meshes,r)
(out/"audit.json").write_text(json.dumps(audit,indent=2))
mesh=bpy.data.objects["Heroine_FullSurfaceReview"];phone=bpy.data.objects["Phone_ReviewCube"]
groups={g.index:g.name for g in mesh.vertex_groups}
left=set(v.index for v in mesh.data.vertices if sum(g.weight for g in v.groups if groups[g.group].endswith("_l") and groups[g.group].startswith(("hand_","palm_","thumb_","index_","middle_","ring_","pinky_")))>0.5)
mesh.data.calc_loop_triangles()
triangles=[tuple(t.vertices) for t in mesh.data.loop_triangles if all(i in left for i in t.vertices)]
phone.data.calc_loop_triangles();pt=[tuple(t.vertices) for t in phone.data.loop_triangles]
rows=[]
for f in range(1,152,2):
 s.frame_set(f)
 ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 verts=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear()
 pv=[phone.matrix_world@v.co for v in phone.data.vertices]
 tree=BVHTree.FromPolygons(pv,pt,all_triangles=True)
 inv=phone.matrix_world.inverted()
 interior=[]
 if not phone.hide_render:
  half=Vector((.035,.006,.07))
  for i in left:
   v=inv@verts[i]
   depth=min(half[k]-abs(v[k]) for k in range(3))
   if depth>.001:interior.append(depth)
 pairs=BVHTree.FromPolygons(verts,triangles,all_triangles=True).overlap(tree) if not phone.hide_render else []
 rows.append({"frame":f,"hand_phone_triangle_pairs":len(pairs),"interior_hand_vertices":len(interior),"max_inside_depth_mm":max(interior,default=0)*1000})
(out/"grip.json").write_text(json.dumps({"rows":rows,"limits":"Finite 15Hz surface samples; does not grade naturalness or prove collision-free between samples."},indent=2))
print("GRIP_MAX",max(x["max_inside_depth_mm"] for x in rows),flush=True)
