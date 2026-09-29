import bpy,json
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parent;O=R/'DetailFinish'
bpy.ops.wm.open_mainfile(filepath=str(O/'stage5.blend'));bpy.context.preferences.filepaths.save_version=0
ob=bpy.data.objects['Heroine_DetailFinish'];me=ob.data
tree=BVHTree.FromPolygons([v.co for v in me.vertices],[p.vertices[:] for p in me.polygons if me.materials[p.material_index].name=='M_Skin'])
details=set(i for p in me.polygons if me.materials[p.material_index].name=='M_Details' for i in p.vertices);ns=[n.vector.copy() for n in me.corner_normals];fit={}
curve=np.polyfit([-.045,-.038,-.028,-.022,-.015],[.9066,.9074,.9076,.9068,.9048],3)
for i in details:
 v=me.vertices[i];x,y,z=v.co
 if not(-.044<x<-.017 and y<-.048):continue
 dz=z-float(np.polyval(curve,x))
 if not -.0005<dz<.0011:continue
 h,n,p,d=tree.ray_cast(Vector((x,-1,z+.0004)),Vector((0,1,0)))
 if h is None or not -.063<h.y<-.043:continue
 w=min(1,max(0,(dz+.0005)/.0007));dy=max(0,min(.002,h.y+.00005-y));v.co.y+=dy*w;fit[i]=(n,w)
me.update()
for li,l in enumerate(me.loops):
 if l.vertex_index in fit:
  n,w=fit[l.vertex_index];ns[li]=ns[li].lerp(n,w*.8).normalized()
me.normals_split_custom_set(ns)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'rim_candidate.blend'))
sc=bpy.context.scene;sc.cycles.samples=24;cam=sc.camera;cam.location=(-.034,-3,.902);cam.rotation_euler=(Vector((-.034,0,.902))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.10;sc.render.resolution_x=sc.render.resolution_y=1000;sc.render.filepath=str(O/'renders/rim_candidate.png');bpy.ops.render.render(write_still=True);print('RIM_CANDIDATE',len(fit),flush=True)
