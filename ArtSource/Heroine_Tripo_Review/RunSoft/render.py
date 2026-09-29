import bpy,sys,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'Heroine_Run_Soft.blend'))
sc=bpy.context.scene;rig=bpy.data.objects['Heroine_AnimationRig']
sc.render.engine='CYCLES';sc.cycles.samples=8
sc.render.resolution_x=640;sc.render.resolution_y=800;sc.render.resolution_percentage=100
sc.render.use_border=False;sc.render.use_crop_to_border=False
sc.render.use_persistent_data=True
cam=sc.camera;cam.location=(2.3,-4.2,1.4);cam.rotation_euler=(Vector((0,0,.83))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=1.85
sc.world.color=(.16,.16,.16)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.002));floor=bpy.context.object;floor.name='WalkPreview_Floor'
mat=bpy.data.materials.new('WalkPreview_Floor');mat.diffuse_color=(.12,.14,.17,1);floor.data.materials.append(mat)
mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'keys'
out=P/('frames' if mode=='all' else 'keys');out.mkdir(exist_ok=True)
if mode=='all':
 sc.cycles.samples=8;sc.render.resolution_x=480;sc.render.resolution_y=600
for f in (range(1,31) if mode=='all' else ([1,7,13,19] if mode=='first' else [1,4,7,10,13,16,19,22])):
 sc.frame_set(f);sc.render.filepath=str(out/f'{f:03}.png');bpy.ops.render.render(write_still=True)
print('WALK_RENDER_DONE')
