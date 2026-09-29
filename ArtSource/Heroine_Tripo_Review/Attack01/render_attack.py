import bpy,sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(P/'Heroine_Attack01.blend'))
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=8;s.render.resolution_x=640;s.render.resolution_y=640;s.render.resolution_percentage=100;s.render.use_border=False;s.render.use_crop_to_border=False;s.render.use_persistent_data=True
c=s.camera;c.location=(2.8,-5,1.6);c.rotation_euler=(Vector((0,0,.8))-c.location).to_track_quat('-Z','Y').to_euler();c.data.type='ORTHO';c.data.ortho_scale=2.6
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.002));floor=bpy.context.object;floor.name='AttackPreview_Floor';mat=bpy.data.materials.new('AttackPreview_Floor');mat.diffuse_color=(.13,.15,.18,1);floor.data.materials.append(mat)
all_frames='--' in sys.argv and sys.argv[-1]=='all';out=P/('frames' if all_frames else 'keys');out.mkdir(exist_ok=True)
for f in (range(1,61,2) if all_frames else [1,9,17,25,31,39,49,61]):
 s.frame_set(f);s.render.filepath=str(out/f'{f:03}.png');bpy.ops.render.render(write_still=True)
