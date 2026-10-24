import bpy,json
from pathlib import Path
s=bpy.context.scene
o=bpy.data.objects["Heroine_FullSurfaceReview"]
cube=bpy.data.objects["Phone_Portrait_ReviewCube"]
groups={g.index for g in o.vertex_groups if g.name.endswith("_r") and g.name.startswith(("hand","thumb","index","middle","ring","pinky"))}
indices=[v.index for v in o.data.vertices if sum(g.weight for g in v.groups if g.group in groups)<=.5]
print("CONTACT_MESH",len(o.data.vertices),[(m.name,m.type,m.show_viewport) for m in o.modifiers],"HAND_VERTICES",len(indices),flush=True)
half=[max(abs(v.co[j]) for v in cube.data.vertices) for j in range(3)]
results=[]
for f in range(73,207):
    s.frame_set(f)
    deps=bpy.context.evaluated_depsgraph_get()
    ev=o.evaluated_get(deps)
    mesh=ev.to_mesh()
    transform=cube.matrix_world.inverted()@o.matrix_world
    depths=[]
    for i in indices:
        q=transform@mesh.vertices[i].co
        depth=min(half[j]-abs(q[j]) for j in range(3))
        if depth>.0005:
            depths.append(depth)
            if f==91:
                print("BODY_CONTACT_VERTEX",i,list(q),[(o.vertex_groups[g.group].name,round(g.weight,3)) for g in o.data.vertices[i].groups if g.weight>.1],flush=True)
    if depths:
        results.append({"frame":f,"vertices_inside":len(depths),"max_depth_mm":1000*max(depths)})
    ev.to_mesh_clear()
out={"method":"Non-hand main-mesh vertices inside cube during holding, 0.5mm threshold; not a complete triangle intersection/contact test",
     "hand_vertices":len(indices),"frames":[73,206],"penetrations":results}
(Path(bpy.data.filepath).parent/"cube_body_contact.json").write_text(json.dumps(out,indent=2))
print("CONTACT",len(results),"frames",max((row["max_depth_mm"] for row in results),default=0),"mm",flush=True)

