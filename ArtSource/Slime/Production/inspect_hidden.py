import bpy
from mathutils.bvhtree import BVHTree
s=bpy.context.scene;b=bpy.data.objects['Slime_Body'];d=bpy.data.objects['Slime_Droplet']
for f in [1]+[92+i/5 for i in range(26)]:
 s.frame_set(int(f),subframe=f-int(f));dep=bpy.context.evaluated_depsgraph_get();tree=BVHTree.FromObject(b,dep);ev=d.evaluated_get(dep);m=ev.to_mesh();vals=[]
 for v in m.vertices:
  p=ev.matrix_world@v.co;h,n,_,_=tree.find_nearest(p);vals.append((p-h).dot(n))
 ev.to_mesh_clear();print('HIDDEN',f,round(max(vals),5),list(bpy.data.objects['Slime_Liquid_Rig'].pose.bones['drop'].head))
