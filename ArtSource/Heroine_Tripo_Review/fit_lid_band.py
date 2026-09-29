import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
R=Path(__file__).resolve().parent;O=R/'ContourRepair'
bpy.ops.wm.open_mainfile(filepath=str(O/'Heroine_ContourRepair_Final.blend'));bpy.context.preferences.filepaths.save_version=0
body=bpy.data.objects['Heroine_ContourRepair'];me=body.data;me.calc_loop_triangles();ts=[t for t in me.loop_triangles if me.materials[t.material_index].name=='M_Skin'];coords=[v.co.copy() for v in me.vertices];tree=BVHTree.FromPolygons(coords,[t.vertices[:] for t in ts],all_triangles=True)
uvs=[[Vector((*me.uv_layers.active.data[l].uv,0)) for l in t.loops] for t in ts]
band=bpy.data.objects['Lower_Lid_Skin_-1'];bm=band.data;newuv=[]
for v in bm.vertices:
 row=v.index//4;k=v.index%4;t=row/48;top=bm.vertices[row*4].co.copy()
 if row>40:
  factor=max(0,(46-row)/6);v.co.z=top.z+(v.co.z-top.z)*factor
 hit,n,i,dist=tree.ray_cast(Vector((v.co.x,-1,v.co.z)),Vector((0,1,0)))
 if hit:
  uv=barycentric_transform(hit,*(coords[j] for j in ts[i].vertices),*uvs[i]);newuv.append(uv.to_2d())
  if k>0 and row>40:v.co.y=top.y+(hit.y+.00012-top.y)*(k/3)
 else:newuv.append(Vector((.5,.5)))
# Retain the source skin tone; ray projection at the socket edge samples old painted liner.
bm.update()
sc=bpy.context.scene;sc.cycles.samples=24;sc.render.filepath=str(O/'renders/fitted_lid.png');bpy.ops.wm.save_as_mainfile(filepath=str(O/'Heroine_ContourRepair_Fitted.blend'));bpy.ops.render.render(write_still=True)
