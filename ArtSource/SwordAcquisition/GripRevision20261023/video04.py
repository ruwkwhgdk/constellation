import bpy,json,sys,os
from pathlib import Path
from mathutils import Vector
P=Path(__file__).parent
file=os.environ.get('SWORD_CANDIDATE','Heroine_Sword_RightUpper04.blend')
bpy.ops.wm.open_mainfile(filepath=str(P/file));s=bpy.context.scene
r=bpy.data.objects['Heroine_Rebuild_GameSkeleton'];sw=bpy.data.objects['Sword_proxy']
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.render.resolution_x=512;s.render.resolution_y=512;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.world.color=(.25,.25,.25)
for o in s.objects:
 if o.type=='LIGHT':o.hide_render=True
for name,loc,power,size in [('Key',(1,-3,4),700,4),('Fill',(-3,-1,2),450,3),('Rim',(0,3,3),650,3)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.012));ground=bpy.context.object
mat=bpy.data.materials.new('AuditFloor');mat.diffuse_color=(.11,.13,.15,1);ground.data.materials.append(mat)
cam=s.camera;cam.data.type='ORTHO';D=P/'VideoFrames04';D.mkdir(exist_ok=True)
rows=[]
frames=[f for a,b in [(1,100),(100,172),(244,355),(415,457),(457,523),(523,595),(667,739)] for f in range(a,b,2)]
if os.environ.get('SWORD_FRAMES'):frames=[int(x) for x in os.environ['SWORD_FRAMES'].split(',')]
for idx,f in enumerate(frames):
 s.frame_set(f)
 row={'f':f,'hands':{},'sword':list(sw.matrix_world.translation)}
 for side in ['r','l']:
  w=r.matrix_world@r.pose.bones['hand_'+side].matrix
  row['hands'][side]=list(w.translation)
 rows.append(row)
 for view,offset in [('front',(1,-4,.3)),('side',(4,0,.3)),('hand',(.4,-2,.35))]:
  center=Vector((0,0,1.25)) if view!='hand' else (r.matrix_world@r.pose.bones['hand_r'].head)+Vector((0,0,.03))
  cam.location=center+Vector(offset);cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=2.9 if view!='hand' else .65
  s.render.filepath=str(D/f'{idx:04}_{view}.png');bpy.ops.render.render(write_still=True)
(D/'positions.json').write_text(json.dumps(rows,indent=2))


count=len(frames);exports={};Dout=P/'Delivery04';Dout.mkdir(exist_ok=True)
for view in ['front','side','hand']:
 files=[D/f'{i:04}_{view}.png' for i in range(count)]
 bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.sequence_editor_create();strip=s.sequence_editor.strips.new_image(view,str(files[0]),channel=1,frame_start=1)
 for f in files[1:]:strip.elements.append(f.name)
 s.frame_start=1;s.frame_end=count;s.render.fps=15;s.render.resolution_x=512;s.render.resolution_y=512;s.render.resolution_percentage=100;s.render.image_settings.media_type='VIDEO';s.render.image_settings.file_format='FFMPEG';s.render.ffmpeg.format='MPEG4';s.render.ffmpeg.codec='H264';s.render.ffmpeg.constant_rate_factor='HIGH';s.view_settings.view_transform='Standard';s.view_settings.look='None';s.render.filepath=str(Dout/f'blender_{view}.mp4');bpy.ops.render.render(animation=True)
 exports[view]={'frames':count,'fps':15,'duration':count/15}
(Dout/'videos.json').write_text(json.dumps(exports,indent=2));print('VIDEOS_DONE',flush=True)
