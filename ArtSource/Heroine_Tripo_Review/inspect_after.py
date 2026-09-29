import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;O=R/'ContourRepair';O.mkdir(exist_ok=True);(O/'diagnostics').mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(O/'Heroine_ContourRepair_OverlapFixed.blend'))
sc=bpy.context.scene;cam=sc.camera;cam.location=(-.034,-3,.902);cam.rotation_euler=(Vector((-.034,0,.902))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.10;sc.render.resolution_x=sc.render.resolution_y=1100;sc.cycles.samples=16
clay=bpy.data.materials.new('AuditClay');clay.use_nodes=True;bs=clay.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.4,.4,.4,1);bs.inputs['Roughness'].default_value=.8
sc.view_layers[0].material_override=clay;sc.render.filepath=str(O/'diagnostics/clay_after.png');bpy.ops.render.render(write_still=True);sc.view_layers[0].material_override=None
for m in bpy.data.materials:
 if not m.use_nodes:continue
 nt=m.node_tree;bs=nt.nodes.get('Principled BSDF');out=next((n for n in nt.nodes if n.type=='OUTPUT_MATERIAL'),None)
 if not bs or not out:continue
 em=nt.nodes.new('ShaderNodeEmission')
 if bs.inputs['Base Color'].links:nt.links.new(bs.inputs['Base Color'].links[0].from_socket,em.inputs['Color'])
 else:em.inputs['Color'].default_value=bs.inputs['Base Color'].default_value
 nt.links.new(em.outputs[0],out.inputs['Surface'])
sc.render.filepath=str(O/'diagnostics/albedo_after.png');bpy.ops.render.render(write_still=True)
