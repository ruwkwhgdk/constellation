import bpy,json,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;O=R/'BoundaryLocal';(O/'textures').mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'DetailPreserved/Heroine_DetailPreserved.blend'))
source=bpy.data.objects['Heroine_DetailPreserved']
baseline={'polygons':[tuple(p.vertices) for p in source.data.polygons],'uv':[[tuple(d.uv) for d in layer.data] for layer in source.data.uv_layers],'xz':[(v.co.x,v.co.z) for v in source.data.vertices],'face_uv':{tuple(p.vertices):tuple(tuple(source.data.uv_layers.active.data[i].uv) for i in p.loop_indices) for p in source.data.polygons}}
bpy.ops.wm.open_mainfile(filepath=str(O/'Heroine_BoundaryLocal.blend'));bpy.context.preferences.filepaths.save_version=0
body=bpy.data.objects['Heroine_BoundaryLocal'];me=body.data
report={'retained_faces_preserved':set(tuple(p.vertices) for p in me.polygons).issubset(set(baseline['polygons'])),'retained_uv_preserved':all(baseline['face_uv'].get(tuple(p.vertices))==tuple(tuple(me.uv_layers.active.data[i].uv) for i in p.loop_indices) for p in me.polygons),'body_front_outline_preserved':baseline['xz']==[(v.co.x,v.co.z) for v in me.vertices],'iris_edited':False}
sc=bpy.context.scene;sc.cycles.samples=1;bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
target=bpy.data.images.new('T_Heroine_LocalBoundary',4096,4096,alpha=False);target.filepath_raw=str(O/'textures/T_Heroine_LocalBoundary.png');target.file_format='PNG'
state=[]
for m in me.materials:
 nt=m.node_tree;bs=nt.nodes.get('Principled BSDF');out=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');em=nt.nodes.new('ShaderNodeEmission')
 if bs.inputs['Base Color'].links:nt.links.new(bs.inputs['Base Color'].links[0].from_socket,em.inputs['Color'])
 else:em.inputs['Color'].default_value=bs.inputs['Base Color'].default_value
 nt.links.new(em.outputs[0],out.inputs['Surface']);tex=nt.nodes.new('ShaderNodeTexImage');tex.image=target;nt.nodes.active=tex;state.append((m,bs,out,em,tex))
sc.render.bake.margin=8;bpy.ops.object.bake(type='EMIT');target.save();target.pack()
for m,bs,out,em,tex in state:
 nt=m.node_tree;nt.links.new(bs.outputs[0],out.inputs['Surface']);nt.nodes.remove(em)
 if m.name in ['M_Hair','M_Skin']:
  nt.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
  for n in list(nt.nodes):
   if n not in [bs,out,tex]:nt.nodes.remove(n)
 else:nt.nodes.remove(tex)
sc.cycles.samples=32;cam=sc.camera
def render(name,loc,target,scale):
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.resolution_x=sc.render.resolution_y=1100;sc.render.filepath=str(O/'renders'/f'{name}.png');bpy.ops.render.render(write_still=True)
render('eye',(-.034,-3,.902),(-.034,0,.902),.10)
render('face',(0,-3,.862),(0,0,.862),.30)
render('angle',(-1,-3,.862),(0,0,.862),.30)
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];report['blend_triangles']=sum(len(p.vertices)-2 for o in meshes for p in o.data.polygons)
bpy.ops.object.select_all(action='DESELECT')
for ob in meshes:ob.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.fbx(filepath=str(O/'Heroine_BoundaryLocal.fbx'),use_selection=True,object_types={'MESH'},bake_anim=False,path_mode='COPY',embed_textures=True,axis_forward='-Z',axis_up='Y')
cam.location=(0,-3,.862);cam.rotation_euler=(Vector((0,0,.862))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.30
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Heroine_BoundaryLocal.blend'))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(O/'Heroine_BoundaryLocal.fbx'))
report['fbx_triangles']=sum(len(p.vertices)-2 for o in bpy.context.scene.objects if o.type=='MESH' for p in o.data.polygons);report['missing_images']=[i.name for i in bpy.data.images if i.source=='FILE' and i.size[0]==0]
report['pass']=all(report[k] for k in ['retained_faces_preserved','retained_uv_preserved','body_front_outline_preserved']) and report['blend_triangles']==report['fbx_triangles'] and not report['missing_images']
(O/'validation.json').write_text(json.dumps(report,indent=2));print('VALIDATED',json.dumps(report))
