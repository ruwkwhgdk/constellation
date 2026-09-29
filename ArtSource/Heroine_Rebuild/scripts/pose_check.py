import bpy,math,json
from pathlib import Path
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Heroine_Rebuild.blend'))
rig=bpy.data.objects['Heroine_OriginalSkeleton']
for name,angle,world_axis in [('mixamorig:LeftUpLeg',-24,(1,0,0)),('mixamorig:LeftLeg',38,(1,0,0)),('mixamorig:RightUpLeg',10,(1,0,0)),('mixamorig:RightLeg',12,(1,0,0)),('mixamorig:LeftForeArm',20,(0,1,0))]:
    p=rig.pose.bones[name];p.rotation_mode='QUATERNION'
    axis=(rig.matrix_world@p.bone.matrix_local).to_quaternion().inverted()@Vector(world_axis)
    p.rotation_quaternion=Quaternion(axis,math.radians(angle))
sc=bpy.context.scene;cam=sc.camera;cam.location=(2.4,-4,.2)
cam.rotation_euler=(Vector((0,0,.03))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=2.16
sc.cycles.samples=24;sc.render.resolution_x=800;sc.render.resolution_y=1100
sc.render.filepath=str(ROOT/'renders/pose_check.png');bpy.ops.render.render(write_still=True)
print('Pose check rendered; production .blend was not modified.')
