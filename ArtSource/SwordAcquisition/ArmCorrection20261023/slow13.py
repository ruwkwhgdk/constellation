import bpy
from pathlib import Path
P=Path(__file__).parent;D=P/'VideoFrames13';files=sorted(D.glob('*_hand.png'));s=bpy.context.scene;s.sequence_editor_create();strip=s.sequence_editor.strips.new_image('Hands',str(files[0]),channel=1,frame_start=1)
for f in files[1:]:strip.elements.append(f.name)
s.frame_start=1;s.frame_end=len(files);s.render.fps=15;s.render.fps_base=2;s.render.resolution_x=512;s.render.resolution_y=512;s.render.resolution_percentage=100;s.render.image_settings.media_type='VIDEO';s.render.image_settings.file_format='FFMPEG';s.render.ffmpeg.format='MPEG4';s.render.ffmpeg.codec='H264';s.render.ffmpeg.constant_rate_factor='HIGH';s.view_settings.view_transform='Standard';s.view_settings.look='None';s.render.filepath=str(P/'Delivery/blender_hand_half_speed.mp4');bpy.ops.render.render(animation=True)
