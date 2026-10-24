"""Attach a portrait cube to the source-derived right-hand pose; no pose edits."""
import bpy,json
from pathlib import Path
from mathutils import Vector, Matrix
p=Path(bpy.data.filepath).parent
s=bpy.context.scene
r=bpy.data.objects["Heroine_Rebuild_GameSkeleton"]
s.frame_set(120)
def point(n):
    return r.matrix_world @ r.pose.bones[n].head
w,m,i,k=[point(n) for n in ("hand_r","middle_01_r","index_01_r","pinky_01_r")]
y=(m-w).normalized()
x=i-k
x=(x-y*x.dot(y)).normalized()
z=x.cross(y).normalized()
curl=point("middle_03_r")-m
if z.dot(curl)<0:
    x.negate()
    z.negate()
orientation=Matrix((x,y,z)).transposed().to_4x4()
orientation.translation=(w+m)*.5+y*.025+z*.012
hand=r.matrix_world@r.pose.bones["hand_r"].matrix
offset=hand.inverted()@orientation
bpy.ops.mesh.primitive_cube_add(size=1)
cube=bpy.context.object
cube.name="Phone_Portrait_ReviewCube"
cube.scale=(.065,.13,.008)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
cube.color=(.12,.28,.5,1)
for f in range(1,s.frame_end+1):
    s.frame_set(f)
    cube.matrix_world=r.matrix_world@r.pose.bones["hand_r"].matrix@offset
    cube.rotation_mode="QUATERNION"
    for channel in ("location","rotation_quaternion","scale"):
        cube.keyframe_insert(channel,frame=f)
    cube.hide_render=not 31<=f<=245
    cube.keyframe_insert("hide_render",frame=f)
s.frame_set(120)
bpy.ops.wm.save_as_mainfile(filepath=str(p/"Heroine_Mixamo_OneHand_Cube01.blend"))
(p/"cube_review.json").write_text(json.dumps({
    "dimensions_m":[.065,.13,.008],
    "hand":"hand_r",
    "attachment_reference_frame":120,
    "visibility_frames":[31,245],
    "status":"Provisional geometry and pocket timing; visual verification required",
    "offset":[list(row) for row in offset]
},indent=2))
