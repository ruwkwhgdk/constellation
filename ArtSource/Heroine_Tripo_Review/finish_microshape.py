import bpy,json
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;O=R/'DetailFinish'
bpy.ops.wm.open_mainfile(filepath=str(O/'stage4.blend'));bpy.context.preferences.filepaths.save_version=0
ob=bpy.data.objects['Heroine_DetailFinish'];me=ob.data;norms=[n.vector.copy() for n in me.corner_normals];orig=[v.co.copy() for v in me.vertices];adj=[set() for v in me.vertices];mats=[set() for v in me.vertices]
for e in me.edges:a,b=e.vertices;adj[a].add(b);adj[b].add(a)
for p in me.polygons:
 for i in p.vertices:mats[i].add(me.materials[p.material_index].name)
curve=np.polyfit([-.045,-.038,-.028,-.022,-.015],[.9066,.9074,.9076,.9068,.9048],3)
rim={};mouth={};tips={}
for v in me.vertices:
 x,y,z=v.co
 if -.044<x<-.017 and y<-.048 and 'M_Details' in mats[v.index]:
  distance=abs(z-float(np.polyval(curve,x)))
  if distance<.001:rim[v.index]=1-distance/.001
 if .006<abs(x)<.0105 and y<-.05 and .8584<z<.8601:mouth[v.index]=.16
 if abs(x)>.416 and 'M_Skin' in mats[v.index]:tips[v.index]=.17
for i,w in rim.items():me.vertices[i].co.y+=.00048*w;me.vertices[i].co.z-=.00010*w
for group in [mouth,tips]:
 for iteration in range(2):
  pos=[v.co.copy() for v in me.vertices]
  for i,w in group.items():
   if not adj[i]:continue
   delta=sum((pos[j] for j in adj[i]),Vector())/len(adj[i])-pos[i]
   if i in mouth:delta.x=0
   if delta.length>.00022:delta*=.00022/delta.length
   me.vertices[i].co+=delta*w
me.update();modified=set(rim)|set(mouth)|set(tips)
# Local normal blending only; retain all other imported loop normals.
for li,l in enumerate(me.loops):
 if l.vertex_index in modified:norms[li]=norms[li].lerp(me.vertices[l.vertex_index].normal,.35).normalized()
me.normals_split_custom_set(norms)
(O/'microshape_changes.json').write_text(json.dumps({'rim_vertices':len(rim),'mouth_vertices':len(mouth),'fingertip_vertices':len(tips),'max_displacement':max((v.co-orig[v.index]).length for v in me.vertices)},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(O/'stage5.blend'))
sc=bpy.context.scene;sc.cycles.samples=24;cam=sc.camera;cam.location=(-.034,-3,.902);cam.rotation_euler=(Vector((-.034,0,.902))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.10;sc.render.resolution_x=sc.render.resolution_y=1000;sc.render.filepath=str(O/'renders/eye.png');bpy.ops.render.render(write_still=True)
print('MICROSHAPE_DONE',flush=True)
