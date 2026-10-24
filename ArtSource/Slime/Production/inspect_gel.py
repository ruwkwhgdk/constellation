import bpy,json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
s=bpy.context.scene;s.frame_set(1);b=bpy.data.objects['Slime_Body'];t=BVHTree.FromObject(b,bpy.context.evaluated_depsgraph_get())
for xy in [(.37,-.34),(.36,-.38),(.35,-.42)]:
 p=Vector((*xy,1.42))
 for i in range(4):
  h,n,ix,d=t.ray_cast(p,Vector((0,0,-1)),3)
  print('RAY',xy, tuple(h) if h else None)
  if h is None:break
  p=h+Vector((0,0,-.002))
c=bpy.context.preferences.addons['cycles'].preferences
try:c.compute_device_type='OPTIX';c.get_devices()
except Exception as e:print(e)
print('DEVICES',[(d.name,d.type) for d in c.devices])
