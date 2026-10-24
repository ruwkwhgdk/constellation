import bpy,json,numpy as np
from pathlib import Path
s=bpy.context.scene;o=bpy.data.objects["Heroine_FullSurfaceReview"];c=bpy.data.objects["Phone_Portrait_ReviewCube"]
offsets=[0,.005,.01,.015,.02,.025,.03]
totals={str(x):{"vertices":0,"frames":0} for x in offsets}
half=np.array([.0275,.06,.003])
for f in range(73,207):
 s.frame_set(f);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 data=np.empty(len(me.vertices)*3,dtype=np.float32);me.vertices.foreach_get("co",data)
 matrix=np.array(c.matrix_world.inverted()@o.matrix_world);points=data.reshape(-1,3)@matrix[:3,:3].T+matrix[:3,3]
 for shift in offsets:
  q=points-np.array([0,shift,0]);depth=np.min(half-np.abs(q),axis=1);count=int(np.count_nonzero(depth>.0005))
  totals[str(shift)]["vertices"]+=count;totals[str(shift)]["frames"]+=int(count>0)
 ev.to_mesh_clear()
(Path(bpy.data.filepath).parent/"slide_options.json").write_text(json.dumps(totals,indent=2))
print("SLIDE_OPTIONS",json.dumps(totals),flush=True)
