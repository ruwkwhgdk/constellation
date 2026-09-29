import bpy
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(R/'NeutralExpression/Heroine_NeutralExpression.blend'))
ob=bpy.data.objects['Heroine_NeutralExpression'];me=ob.data;me.normals_split_custom_set([(0,0,0)]*len(me.loops));sc=bpy.context.scene;sc.cycles.samples=16;cam=sc.camera;cam.location=(0,-3,.067);cam.rotation_euler=(Vector((0,0,.067))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.24;sc.render.resolution_x=sc.render.resolution_y=1000;sc.render.filepath=str(R/'NeutralInspection/renders/shoes_recalculated_normals.png');bpy.ops.render.render(write_still=True)
