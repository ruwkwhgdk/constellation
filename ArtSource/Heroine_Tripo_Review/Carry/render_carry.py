import bpy, math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent
scene=bpy.context.scene; scene.render.engine='CYCLES'; scene.cycles.samples=16
scene.render.resolution_x=640; scene.render.resolution_y=800; scene.render.resolution_percentage=100
scene.render.use_border=False; scene.render.use_crop_to_border=False
camera=scene.camera
if not camera:
    data=bpy.data.cameras.new('CarryReviewCamera'); camera=bpy.data.objects.new('CarryReviewCamera',data); scene.collection.objects.link(camera); scene.camera=camera
camera.data.type='ORTHO'; camera.data.ortho_scale=1.9
camera.location=(2.4,-4.5,1.8); camera.rotation_euler=(Vector((0,-.05,.80))-camera.location).to_track_quat('-Z','Y').to_euler()
if not any(o.type=='LIGHT' for o in scene.objects):
    data=bpy.data.lights.new('CarryKey','AREA'); data.energy=500; data.shape='DISK'; data.size=4
    light=bpy.data.objects.new('CarryKey',data); scene.collection.objects.link(light); light.location=(2,-3,4)
    light.rotation_euler=(Vector((0,0,.9))-light.location).to_track_quat('-Z','Y').to_euler()
scene.world.color=(.15,.15,.15)
name=Path(bpy.data.filepath).stem.removeprefix('Heroine_Carry_')
for frame in [1,round((scene.frame_end-1)*.4)+1,round((scene.frame_end-1)*.7)+1,scene.frame_end]:
    scene.frame_set(frame); scene.render.filepath=str(P/f'{name}_{frame:03}.png'); bpy.ops.render.render(write_still=True)
print('CARRY_REVIEW_FRAMES_RENDERED',name)
