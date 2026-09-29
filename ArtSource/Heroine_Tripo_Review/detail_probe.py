import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(R/'Corrected/Heroine_Tripo_Corrected.blend'))
o=bpy.data.objects['Heroine_Tripo_Corrected']
eyeids={v for p in o.data.polygons if o.data.materials[p.material_index].name=='M_Eyes' for v in p.vertices}
points=[list(o.data.vertices[i].co) for i in eyeids]
(R/'eye_points.json').write_text(json.dumps(points))
print('EYE_BOUNDS',[(min(p[i] for p in points),max(p[i] for p in points)) for i in range(3)])
sc=bpy.context.scene;sc.cycles.samples=24;cam=sc.camera
cam.location=(-.034,-3,.9);target=Vector((-.034,0,.9));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.085
sc.render.resolution_x=1000;sc.render.resolution_y=800;sc.render.filepath=str(R/'eye_probe.png');bpy.ops.render.render(write_still=True)
