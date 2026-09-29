import bpy
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;O=R/'NeutralInspection';bpy.ops.wm.open_mainfile(filepath=str(R/'NeutralExpression/Heroine_NeutralExpression.blend'));sc=bpy.context.scene;sc.cycles.samples=16;cam=sc.camera
def render(name,loc,target,scale):
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.resolution_x=sc.render.resolution_y=1000;sc.render.filepath=str(O/'renders'/f'{name}.png');bpy.ops.render.render(write_still=True)
render('hand_top',(-.4,-.3,3),(-.4,0,.785),.135)
render('hand_palm',(-.4,-.3,-3),(-.4,0,.785),.135)
render('eye',(-.034,-3,.902),(-.034,0,.902),.10)
for m in bpy.data.materials:
 if not m.use_nodes:continue
 nt=m.node_tree;bs=nt.nodes.get('Principled BSDF');out=next((n for n in nt.nodes if n.type=='OUTPUT_MATERIAL'),None)
 if not bs or not out:continue
 em=nt.nodes.new('ShaderNodeEmission')
 if bs.inputs['Base Color'].links:nt.links.new(bs.inputs['Base Color'].links[0].from_socket,em.inputs['Color'])
 else:em.inputs['Color'].default_value=bs.inputs['Base Color'].default_value
 nt.links.new(em.outputs[0],out.inputs['Surface'])
render('shoes_albedo',(0,-3,.067),(0,0,.067),.24)
render('collar_albedo',(0,-3,.79),(0,0,.79),.20)
