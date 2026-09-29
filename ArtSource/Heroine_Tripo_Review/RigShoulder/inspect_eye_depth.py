import bpy,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'rig_bound.blend'));s=bpy.context.scene;s.cycles.samples=16;s.render.resolution_x=s.render.resolution_y=800;s.render.resolution_percentage=100
for name,x,y in [('eye_front',0,-3),('eye_oblique',-2,-3),('eye_side',-3,-.4)]:
 c=s.camera;c.location=(x,y,.901);c.rotation_euler=(Vector((-.018,0,.901))-c.location).to_track_quat('-Z','Y').to_euler();c.data.ortho_scale=.16;s.render.filepath=str(P/'renders'/f'{name}.png');bpy.ops.render.render(write_still=True)
print(json.dumps({o.name:[[min((o.matrix_world@v.co)[i] for v in o.data.vertices),max((o.matrix_world@v.co)[i] for v in o.data.vertices)] for i in range(3)] for o in s.objects if o.type=='MESH' and o.name.startswith(('Iris','Sclera','Lower'))}))
