import bpy
from pathlib import Path
OUT=Path(__file__).resolve().parents[1]/'Bird/Tripo_Rig_v001'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'pigeon_rig.blend'))
scene=bpy.context.scene; scene.camera.data.ortho_scale=1.02
bpy.context.preferences.filepaths.save_version=0
scene.render.resolution_x=600; scene.render.resolution_y=500; scene.cycles.samples=10
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'pigeon_rig.blend'))
frames=OUT/'preview_frames'; frames.mkdir(exist_ok=True)
for frame in range(1,25):
    scene.frame_set(frame); scene.render.filepath=str(frames/('%03d.png'%frame)); bpy.ops.render.render(write_still=True)
    if frame in [1,7,13,19]: bpy.data.images['Render Result'].save_render(str(OUT/('fly_%02d.png'%frame)))
