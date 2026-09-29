import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parent;O=R/'DetailFinish2';bpy.ops.wm.open_mainfile(filepath=str(O/'restored_seams.blend'));bpy.context.preferences.filepaths.save_version=0;body=bpy.data.objects['Heroine_DetailFinish2'];me=body.data;band=bpy.data.objects['Lower_Lid_Skin_-1']
# Keep the rear-facet correction without the rejected face deletion.
with bpy.data.libraries.load(str(O/'fold_stage.blend'),link=False) as (a,b):b.objects=['Heroine_DetailFinish2']
rearbody=b.objects[0];rearids=json.loads((O/'fold_changes.json').read_text())['rear_facet_vertices'];ns=[n.vector.copy() for n in me.corner_normals]
for i in rearids:me.vertices[i].co=rearbody.data.vertices[i].co
bpy.data.objects.remove(rearbody);me.update()
for i,l in enumerate(me.loops):
 if l.vertex_index in rearids:ns[i]=me.vertices[l.vertex_index].normal.copy()
me.normals_split_custom_set(ns)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'safe_stage.blend'))
# Trial: preserve the eyeliner contour and conform the existing skin strip to the cheek.
with bpy.data.libraries.load(str(R/'BoundaryLocal/Heroine_BoundaryLocal.blend'),link=False) as (a,b):b.objects=['Lower_Lid_Skin_-1']
donor=b.objects[0];original=[v.co.copy() for v in donor.data.vertices];bpy.data.objects.remove(donor)
cid=json.loads((O/'components.json').read_text())['ids'];tree=BVHTree.FromPolygons([v.co for v in me.vertices],[p.vertices[:] for p in me.polygons if cid[p.vertices[0]]==14])
for row in range(49):
 top=original[row*4];bottom=original[row*4+3];factor=1+.7*math.exp(-((row-39)/7)**2);width=(top.z-bottom.z)*factor
 for k in range(4):
  v=band.data.vertices[row*4+k];t=k/3;z=top.z-width*t;x=original[row*4+k].x;h,n,i,d=tree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
  y=original[row*4+k].y
  if h is not None and -.07<h.y<-.03:
   y=top.y*(1-t)+(h.y-.000035)*t
   if k>0:y=min(y,h.y-.000035)
  v.co=(x,y,z)
band.data.update();band.data.normals_split_custom_set([band.data.vertices[l.vertex_index].normal.copy() for l in band.data.loops])
bpy.ops.wm.save_as_mainfile(filepath=str(O/'lidfit_candidate.blend'))
sc=bpy.context.scene;sc.cycles.samples=24;cam=sc.camera;cam.location=(-.034,-3,.902);cam.rotation_euler=(Vector((-.034,0,.902))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.10;sc.render.resolution_x=sc.render.resolution_y=1000;sc.render.filepath=str(O/'renders/lidfit_candidate.png');bpy.ops.render.render(write_still=True);print('LIDFIT_DONE',flush=True)
