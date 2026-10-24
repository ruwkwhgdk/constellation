import bpy,json,sys,os
from pathlib import Path
from mathutils import Vector
P=Path(__file__).parent
file='C:/Users/User/.codex/visualizations/2026/09/19/01a0ba3a-ca09-73e0-b9bd-7084c8f3096b/SwordPull_Heroine01/Heroine_Sword_Final03.blend'
bpy.ops.wm.open_mainfile(filepath=str(P/file));s=bpy.context.scene
r=bpy.data.objects['Heroine_Rebuild_GameSkeleton'];sw=bpy.data.objects['Sword_proxy']
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.render.resolution_x=640;s.render.resolution_y=640;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.world.color=(.25,.25,.25)
for o in s.objects:
 if o.type=='LIGHT':o.hide_render=True
for name,loc,power,size in [('Key',(1,-3,4),700,4),('Fill',(-3,-1,2),450,3),('Rim',(0,3,3),650,3)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.012));ground=bpy.context.object
mat=bpy.data.materials.new('AuditFloor');mat.diffuse_color=(.11,.13,.15,1);ground.data.materials.append(mat)
cam=s.camera;cam.data.type='ORTHO';D=P/'Before';D.mkdir(exist_ok=True)
rows=[];centers={row['f']:Vector(row['hands']['r']) for row in json.loads((P/'Heroine_Sword_RightUpper04/positions.json').read_text())}
frames=[49,100,280,330,355,430,457,490,523,739]
if os.environ.get('SWORD_FRAMES'):frames=[int(x) for x in os.environ['SWORD_FRAMES'].split(',')]
for f in frames:
 s.frame_set(f)
 row={'f':f,'hands':{},'sword':list(sw.matrix_world.translation)}
 for side in ['r','l']:
  w=r.matrix_world@r.pose.bones['hand_'+side].matrix
  row['hands'][side]=list(w.translation)
 rows.append(row)
 for view,offset in [('front',(1,-4,.3)),('side',(4,0,.3)),('hand',(.4,-2,.35))]:
  center=Vector((0,0,1.25)) if view!='hand' else centers[f]+Vector((0,0,.03))
  cam.location=center+Vector(offset);cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=2.9 if view!='hand' else .65
  s.render.filepath=str(D/f'{f:04}_{view}.png');bpy.ops.render.render(write_still=True)
(D/'positions.json').write_text(json.dumps(rows,indent=2))

