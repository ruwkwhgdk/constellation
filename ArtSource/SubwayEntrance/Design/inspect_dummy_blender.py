import bpy,json
from pathlib import Path
from mathutils import Vector
p=Path(__file__).parent
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.fbx(filepath=str(p/'existing_dummy.fbx'))
objs=[o for o in bpy.context.scene.objects if o.type=='MESH']
points=[o.matrix_world@v.co for o in objs for v in o.data.vertices]
lo=Vector(tuple(min(v[i] for v in points) for i in range(3)));hi=Vector(tuple(max(v[i] for v in points) for i in range(3)))
center=(lo+hi)/2;span=max(hi-lo)
mat=bpy.data.materials.new('neutral');mat.diffuse_color=(.5,.6,.65,1)
for o in objs:o.data.materials.clear();o.data.materials.append(mat)
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_shadows=True;s.display.shading.show_cavity=True
s.render.resolution_x=1000;s.render.resolution_y=850;s.render.resolution_percentage=100
s.world.color=(.6,.6,.6)
for name,direction in [('front',(1,-2,1.1)),('back',(-1,2,1.1)),('top',(0,0,3))]:
    bpy.ops.object.camera_add(location=center+Vector(direction)*span)
    c=bpy.context.object;c.rotation_euler=(center-c.location).to_track_quat('-Z','Y').to_euler();c.data.type='ORTHO';c.data.ortho_scale=span*1.25;s.camera=c
    s.render.filepath=str(p/('dummy_'+name+'.png'));bpy.ops.render.render(write_still=True)
(p/'dummy_bounds_blender.json').write_text(json.dumps(dict(min=list(lo),max=list(hi))),encoding='utf-8')
