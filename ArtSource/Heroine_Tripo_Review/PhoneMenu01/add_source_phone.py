"""Attach a review cube; never edit source-driven bone keys."""
import bpy,json
from pathlib import Path
from mathutils import Vector,Matrix
s=bpy.context.scene;r=bpy.data.objects["Heroine_Rebuild_GameSkeleton"]
P=Path(bpy.data.filepath).parent
out=P/"Prop02";out.mkdir(exist_ok=False)
rest=r.data.bones["hand_l"].matrix_local.to_quaternion()
bpy.ops.mesh.primitive_cube_add(size=1)
p=bpy.context.object;p.name="Phone_ReviewCube";p.dimensions=(.14,.07,.012)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
rot=Matrix(((1,0,0),(0,0,1),(0,-1,0))).transposed().to_quaternion()
s.frame_set(180)
left=r.matrix_world@r.pose.bones["hand_l"].matrix
right=r.matrix_world@r.pose.bones["hand_r"].matrix
center=(left.translation+right.translation)*.5+Vector((0,-.035,.025))
# The original is a two-handed landscape grip. Keep its orientation instead
# of inventing a portrait hand pose. This is only the rigid placeholder offset.
attachment=left.inverted()@Matrix.Translation(center)
for f in range(1,709):
 s.frame_set(f)
 h=r.matrix_world@r.pose.bones["hand_l"].matrix;q=h.to_quaternion()@rest.inverted()
 p.rotation_mode="QUATERNION"
 p.matrix_world=h@attachment
 p.keyframe_insert("location",frame=f);p.keyframe_insert("rotation_quaternion",frame=f)
 p.hide_render=f<35 or f>668;p.hide_viewport=p.hide_render
 p.keyframe_insert("hide_render",frame=f);p.keyframe_insert("hide_viewport",frame=f)
s.frame_set(180)
bpy.ops.wm.save_as_mainfile(filepath=str(out/"Heroine_Mixamo_Phone_Prop02.blend"))
