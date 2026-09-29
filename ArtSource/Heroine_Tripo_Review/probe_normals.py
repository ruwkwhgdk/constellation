import bpy
from pathlib import Path
R=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(R/'FaceClean/Heroine_FaceClean.blend'))
o=bpy.data.objects['Heroine_FaceClean'];print('CUSTOM',o.data.has_custom_normals)
print('SHARP',sum(e.use_edge_sharp for e in o.data.edges))
for v in o.data.vertices:
 if abs(v.co.x+.026)<.002 and abs(v.co.z-.878)<.002:print('VERT',v.index,list(v.co),list(v.normal))
for e in o.data.edges:e.use_edge_sharp=False
if o.data.has_custom_normals:o.data.normals_split_custom_set([(0,0,0)]*len(o.data.loops))
from mathutils import Vector
sc=bpy.context.scene;cam=sc.camera;cam.location=(-.034,-3,.902);cam.rotation_euler=(Vector((-.034,0,.902))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.10;sc.render.resolution_x=1100;sc.render.resolution_y=1100;sc.render.filepath=str(R/'FaceClean/diagnostics/normal_reset.png');bpy.ops.render.render(write_still=True)
