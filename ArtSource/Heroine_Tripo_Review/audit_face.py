import bpy,bmesh,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;O=R/'FaceClean';O.mkdir(exist_ok=True);(O/'diagnostics').mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'Refined/Heroine_Refined.blend'))
body=bpy.data.objects['Heroine_Refined'];bm=bmesh.new();bm.from_mesh(body.data);bm.verts.ensure_lookup_table();seen=set();comps=[]
for v in bm.verts:
 if v in seen:continue
 stack=[v];seen.add(v);vs=[];fs=set()
 while stack:
  a=stack.pop();vs.append(a);fs.update(a.link_faces)
  for e in a.link_edges:
   b=e.other_vert(a)
   if b not in seen:seen.add(b);stack.append(b)
 comps.append((vs,fs))
comps.sort(key=lambda p:-len(p[0]));report=[]
for i,(vs,fs) in enumerate(comps):
 report.append({'id':i,'verts':len(vs),'faces':len(fs),'bounds':[[min(v.co[j] for v in vs),max(v.co[j] for v in vs)] for j in range(3)],'materials':list(set(body.data.materials[f.material_index].name for f in fs))})
(O/'diagnostics/components.json').write_text(json.dumps(report,indent=2))
bm.free()
sc=bpy.context.scene;sc.cycles.samples=24;cam=sc.camera;cam.location=(-.034,-3,.902);target=Vector((-.034,0,.902));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.10;sc.render.resolution_x=1100;sc.render.resolution_y=1100
clay=bpy.data.materials.new('Diagnostic_Clay');clay.use_nodes=True;p=clay.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.35,.35,.35,1);p.inputs['Roughness'].default_value=.8
sc.view_layers[0].material_override=clay;sc.render.filepath=str(O/'diagnostics/eye_clay_before.png');bpy.ops.render.render(write_still=True)
sc.view_layers[0].material_override=None
sc.render.filepath=str(O/'diagnostics/eye_before.png');bpy.ops.render.render(write_still=True)
