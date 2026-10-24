import bpy,json
from pathlib import Path
P=Path(__file__).parent;D=P/'Delivery06';F=P/'VideoFrames06Hand';files=[F/f'{i:04}_hand.png' for i in range(50)]
bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.sequence_editor_create();strip=s.sequence_editor.strips.new_image('approach',str(files[0]),channel=1,frame_start=1)
for f in files[1:]:strip.elements.append(f.name)
s.frame_start=1;s.frame_end=50;s.render.fps=15;s.render.resolution_x=512;s.render.resolution_y=512;s.render.resolution_percentage=100;s.render.image_settings.media_type='VIDEO';s.render.image_settings.file_format='FFMPEG';s.render.ffmpeg.format='MPEG4';s.render.ffmpeg.codec='H264';s.render.ffmpeg.constant_rate_factor='HIGH';s.view_settings.view_transform='Standard';s.view_settings.look='None';s.render.filepath=str(D/'blender_approach_hand.mp4');bpy.ops.render.render(animation=True)
(D/'videos.json').write_text(json.dumps({'approach_hand':{'frames':50,'fps':15,'duration':50/15,'source':'Heroine_Sword_RightUpper06.blend','coverage':'Approach only; later phases provided as saved-model key pose images. Full sequence video was interrupted by external disk exhaustion.'}},indent=2));print('APPROACH_VIDEO_SAVED',flush=True)
