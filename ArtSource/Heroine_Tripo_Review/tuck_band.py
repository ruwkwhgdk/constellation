import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parent;O=R/'ContourRepair';bpy.ops.wm.open_mainfile(filepath=str(O/'Heroine_ContourRepair_BandRestored.blend'));bpy.context.preferences.filepaths.save_version=0
me=bpy.data.objects['Heroine_ContourRepair'].data;skinpolys=[tuple(p.vertices) for p in me.polygons if me.materials[p.material_index].name=='M_Skin'];tree=BVHTree.FromPolygons([v.co for v in me.vertices],skinpolys)
band=bpy.data.objects['Lower_Lid_Skin_-1'];changed=0
for v in band.data.vertices:
 if v.index//4<36:continue
 h,n,i,d=tree.ray_cast(Vector((v.co.x,-1,v.co.z)),Vector((0,1,0)))
 if h is not None and -.08<h.y<-.025 and v.co.y<h.y+.00012:v.co.y=h.y+.00012;changed+=1
band.data.update()
sc=bpy.context.scene;sc.cycles.samples=24;bpy.ops.wm.save_as_mainfile(filepath=str(O/'Heroine_ContourRepair_Ready.blend'));sc.render.use_border=True;sc.render.use_crop_to_border=True;sc.render.border_min_x=.58;sc.render.border_max_x=.75;sc.render.border_min_y=.34;sc.render.border_max_y=.56;sc.render.filepath=str(O/'renders/tucked_band.png');bpy.ops.render.render(write_still=True);print('TUCKED',changed)
