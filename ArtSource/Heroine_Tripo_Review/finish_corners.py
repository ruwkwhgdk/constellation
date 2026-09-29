import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;O=R/'ContourRepair'
bpy.ops.wm.open_mainfile(filepath=str(O/'Heroine_ContourRepair_Retouch.blend'));bpy.context.preferences.filepaths.save_version=0
body=bpy.data.objects['Heroine_ContourRepair'];me=body.data;orig=[v.co.copy() for v in me.vertices];oldnorm=[n.vector.copy() for n in me.corner_normals]
d=json.loads((O/'diagnostics/new_components.json').read_text());cs=d['component_ids'];headid=d['component_sizes'].index(2794);hairid=d['component_sizes'].index(7895)
def box(x,z,a,b,c,d,f=.001):return max(0,min(1,(x-a)/f,(b-x)/f,(z-c)/f,(d-z)/f))
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();weights={}
for v in bm.verts:
 x,y,z=v.co;w=0
 if cs[v.index]==headid and y<-.03:
  w=max(box(x,z,-.021,-.010,.898,.904,.0015),box(x,z,-.049,-.0415,.899,.906,.0015))
 if cs[v.index]==hairid and y<-.035:w=box(x,z,-.050,-.030,.873,.890,.002)*.5
 if w:weights[v]=w
for it in range(28):
 updates=[]
 for v,w in weights.items():
  ns=[e.other_vert(v) for e in v.link_edges if e.link_faces]
  if ns:
   avg=sum((n.co for n in ns),Vector())/len(ns);updates.append((v,v.co.lerp(avg,.3*w)))
 for v,p in updates:v.co=p
bm.normal_update();bm.to_mesh(me);bm.free();me.update()
changed={v.index for v in me.vertices if (v.co-orig[v.index]).length>1e-9}
me.normals_split_custom_set([me.vertices[l.vertex_index].normal.copy() if l.vertex_index in changed else oldnorm[i] for i,l in enumerate(me.loops)])
sc=bpy.context.scene;sc.cycles.samples=24;sc.render.filepath=str(O/'renders/sculpt_corners.png');bpy.ops.wm.save_as_mainfile(filepath=str(O/'Heroine_ContourRepair_Sculpt.blend'));bpy.ops.render.render(write_still=True)
(O/'corner_sculpt.json').write_text(json.dumps({'vertices_adjusted':len(changed),'max_displacement':max((v.co-orig[v.index]).length for v in me.vertices)},indent=2))
