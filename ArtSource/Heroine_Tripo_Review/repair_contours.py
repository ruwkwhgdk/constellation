"""Conservative local sculpt cleanup; keep the existing eye art and materials."""
import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;O=R/'ContourRepair';(O/'renders').mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'BoundaryLocal/Heroine_BoundaryLocal.blend'))
bpy.context.preferences.filepaths.save_version=0
body=bpy.data.objects['Heroine_BoundaryLocal'];body.name='Heroine_ContourRepair';me=body.data
orig=np.array([tuple(v.co) for v in me.vertices]);original_normals=[n.vector.copy() for n in me.corner_normals]
d=json.loads((O/'diagnostics/mesh.json').read_text());comps=d['components']
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table()
def box(x,z,a,b,c,d,f=.001):return max(0,min(1,(x-a)/f,(b-x)/f,(z-c)/f,(d-z)/f))
def weight(v):
 x,y,z=v.co
 if y>-.027 or comps[v.index]!=14:return 0
 return max(box(x,z,-.052,-.010,.913,.925,.002),box(x,z,-.0195,-.009,.897,.910,.002),box(x,z,-.052,-.044,.899,.911,.0015))
weights={v:weight(v) for v in bm.verts};affected=[v for v in bm.verts if weights[v]>0]
# Unfold only the locally raised skin edges, retaining their original texture coordinates.
for it in range(36):
 updates=[]
 for v in affected:
  ns=[e.other_vert(v) for e in v.link_edges if e.link_faces]
  if not ns:continue
  avg=sum((n.co for n in ns),Vector())/len(ns)
  delta=(avg-v.co)*(.38*weights[v]);updates.append((v,v.co+delta))
 for v,p in updates:v.co=p
bm.normal_update();bm.to_mesh(me);bm.free();me.update()
normals=[]
for i,l in enumerate(me.loops):
 v=me.vertices[l.vertex_index];w=weights.get(None,0)
 changed=np.linalg.norm(np.array(v.co)-orig[v.index])>1e-9
 normals.append(v.normal.copy() if changed else original_normals[i])
me.normals_split_custom_set(normals)
sc=bpy.context.scene;cam=sc.camera;cam.location=(-.034,-3,.902);cam.rotation_euler=(Vector((-.034,0,.902))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.10;sc.render.resolution_x=sc.render.resolution_y=1100;sc.cycles.samples=24
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Heroine_ContourRepair.blend'))
sc.render.filepath=str(O/'renders/geometry.png');bpy.ops.render.render(write_still=True)
(O/'geometry_changes.json').write_text(json.dumps({'modified_vertices':sum(np.linalg.norm(np.array(v.co)-orig[v.index])>1e-9 for v in me.vertices),'max_displacement':max(np.linalg.norm(np.array(v.co)-orig[v.index]) for v in me.vertices)},indent=2))
