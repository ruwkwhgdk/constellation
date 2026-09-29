import bpy,bmesh,json,numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Tripo_Source_Inspection.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH')
bpy.context.view_layer.objects.active=o
bpy.ops.object.select_all(action='DESELECT');o.select_set(True)
bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
m=o.data.materials[0];p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
print('SHADER',[(s.name,str(s.default_value)) for s in p.inputs if s.name in ['Roughness','Metallic','Specular IOR Level','Alpha','Emission Strength']])
print('NORMAL_MAP',[(n.inputs['Color'].default_value[:],n.inputs['Strength'].default_value) for n in m.node_tree.nodes if n.type=='NORMAL_MAP'])
bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();seen=set();parts=[]
for v in bm.verts:
    if v.index in seen:continue
    todo=[v];seen.add(v.index);vs=[];fs=set()
    while todo:
        q=todo.pop();vs.append(q);fs.update(q.link_faces)
        for e in q.link_edges:
            n=e.other_vert(q)
            if n.index not in seen:seen.add(n.index);todo.append(n)
    parts.append({'vertices':len(vs),'faces':len(fs),'area':sum(f.calc_area() for f in fs),'bounds':[[round(min(v.co[i] for v in vs),5),round(max(v.co[i] for v in vs),5)] for i in range(3)]})
parts.sort(key=lambda p:-p['vertices']);(ROOT/'components.json').write_text(json.dumps(parts,indent=2));print('PARTS',json.dumps(parts));bm.free()
sc=bpy.context.scene;cam=sc.camera;target=Vector((0,0,.862));cam.location=target+Vector((0,-3,0));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.30
sc.render.resolution_x=1100;sc.render.resolution_y=1100;sc.cycles.samples=24
clay=bpy.data.materials.new('Diagnostic_Clay');clay.use_nodes=True
s=next(n for n in clay.node_tree.nodes if n.type=='BSDF_PRINCIPLED');s.inputs['Base Color'].default_value=(.45,.45,.45,1);s.inputs['Roughness'].default_value=.85
sc.view_layers[0].material_override=clay;sc.render.filepath=str(ROOT/'renders/diagnostic_face_clay.png');bpy.ops.render.render(write_still=True)
sc.view_layers[0].material_override=None
# Texture-only reference exposes baked marks without studio highlights.
out=next(n for n in m.node_tree.nodes if n.type=='OUTPUT_MATERIAL');tex=next(n for n in m.node_tree.nodes if n.type=='TEX_IMAGE')
em=m.node_tree.nodes.new('ShaderNodeEmission');m.node_tree.links.new(tex.outputs['Color'],em.inputs['Color']);m.node_tree.links.new(em.outputs[0],out.inputs['Surface'])
sc.render.filepath=str(ROOT/'renders/diagnostic_face_texture.png');bpy.ops.render.render(write_still=True)
