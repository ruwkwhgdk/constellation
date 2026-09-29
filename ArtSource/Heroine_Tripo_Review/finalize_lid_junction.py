import bpy,bmesh,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;O=R/'ContourRepair';bpy.ops.wm.open_mainfile(filepath=str(O/'Heroine_ContourRepair_OverlapFixed.blend'));bpy.context.preferences.filepaths.save_version=0
band=bpy.data.objects['Lower_Lid_Skin_-1'];me=band.data;bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table()
for v in bm.verts:
 row=v.index//4;k=v.index%4
 if 36<row<=40:
  t=(40-row)/4;top=bm.verts[row*4].co.copy();v.co=top+(v.co-top)*t
remove=[f for f in bm.faces if min(v.index//4 for v in f.verts)>=40]
bmesh.ops.delete(bm,geom=remove,context='FACES');bm.to_mesh(me);bm.free();me.update()
body=bpy.data.objects['Heroine_ContourRepair'];me=body.data;norms=[n.vector.copy() for n in me.corner_normals];orig=[v.co.copy() for v in me.vertices]
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();weights={}
for v in bm.verts:
 x,y,z=v.co
 if y<-.044 and -.023<x<-.018 and .8983<z<.9015 and all(me.materials[f.material_index].name=='M_Skin' for f in v.link_faces):
  w=max(0,min(1,(x+.023)/.001,( -.018-x)/.001,(z-.8983)/.0008,(.9015-z)/.0008));weights[v]=w
for it in range(12):
 updates=[]
 for v,w in weights.items():
  ns=[e.other_vert(v) for e in v.link_edges if e.link_faces]
  if ns:updates.append((v,v.co.lerp(sum((a.co for a in ns),Vector())/len(ns),.3*w)))
 for v,p in updates:v.co=p
bm.normal_update();bm.to_mesh(me);bm.free();me.update()
changed={v.index for v in me.vertices if (v.co-orig[v.index]).length>1e-9};me.normals_split_custom_set([me.vertices[l.vertex_index].normal.copy() if l.vertex_index in changed else norms[i] for i,l in enumerate(me.loops)])
sc=bpy.context.scene;sc.cycles.samples=24;bpy.ops.wm.save_as_mainfile(filepath=str(O/'Heroine_ContourRepair_Checked.blend'));sc.render.use_border=True;sc.render.use_crop_to_border=True;sc.render.border_min_x=.58;sc.render.border_max_x=.75;sc.render.border_min_y=.34;sc.render.border_max_y=.56;sc.render.filepath=str(O/'renders/junction.png');bpy.ops.render.render(write_still=True)
