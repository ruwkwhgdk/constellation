import bpy,math
from pathlib import Path
from mathutils import Vector
p=Path('C:/Users/User/Documents/UnrealProjects/Constellation/ArtSource/Heroine_Tripo_Review/PhoneMenu01/UnrealApply01')
bpy.ops.wm.open_mainfile(filepath=str(p.parent/'OneHandReview04/Heroine_Mixamo_OneHand_Cube08.blend'))
s=bpy.context.scene;s.frame_set(80);bpy.context.view_layer.update()
if not s.camera:bpy.ops.object.camera_add();s.camera=bpy.context.object
s.camera.data.type='PERSP';s.camera.data.angle=math.radians(65);s.camera.data.clip_start=.01
s.camera.location=(.28,-.05,1.32)
yaw=math.radians(80);pitch=math.radians(-45)
d=Vector((-math.cos(pitch)*math.sin(yaw),-math.cos(pitch)*math.cos(yaw),math.sin(pitch)))
s.camera.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
s.render.engine='BLENDER_WORKBENCH';s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.63,.65,.68);s.display.shading.light='STUDIO';s.display.shading.show_cavity=True;s.display.shading.show_shadows=False
s.render.resolution_x=1280;s.render.resolution_y=640;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.filepath=str(p/'source-camera80.png');bpy.ops.render.render(write_still=True)
