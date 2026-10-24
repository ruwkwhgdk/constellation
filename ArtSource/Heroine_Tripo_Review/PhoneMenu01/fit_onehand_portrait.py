import bpy,json,numpy as np,math
from mathutils import Euler
from pathlib import Path
s=bpy.context.scene;o=bpy.data.objects["Heroine_FullSurfaceReview"];cube=bpy.data.objects["Phone_Portrait_ReviewCube"]
groups={g.index for g in o.vertex_groups if g.name.endswith("_r") and g.name.startswith(("hand","thumb","index","middle","ring","pinky"))}
indices=[v.index for v in o.data.vertices if sum(g.weight for g in v.groups if g.group in groups)>.5]
frames=[31,45,60,72,91,120,180,206,212,218,227,240]
cloud=[]
for f in frames:
 s.frame_set(f);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();mat=cube.matrix_world.inverted()@o.matrix_world
 cloud.extend([list(mat@me.vertices[i].co) for i in indices]);ev.to_mesh_clear()
points=np.array(cloud);half=np.array([.0275,.06,.003])
scores=[]
for angle in [90]:
 for spin in [0]:
  rotation=np.array(Euler((math.radians(angle),0,math.radians(spin))).to_matrix())
  for x in np.linspace(-.02,.02,9):
   for y in np.linspace(-.035,.005,9):
    for z in np.linspace(.025,.065,17):
     offset=np.array([x,y,z]);local=(points-offset)@rotation
     d=half-np.abs(local);penetration=np.min(d,axis=1)
     count=int(np.count_nonzero(penetration>.0005))
     scores.append({"inside":count,"offset":list(offset),"distance":float(np.linalg.norm(offset-np.array([0,-.015,.04]))),"rotation_deg":[angle,0,spin]})
scores.sort(key=lambda row:(row["inside"],row["distance"],sum(abs(a) for a in row["rotation_deg"])))
(Path(bpy.data.filepath).parent/"cube_fit_portrait_options.json").write_text(json.dumps(scores[:30],indent=2))
print("FIT",json.dumps(scores[:6]),flush=True)

