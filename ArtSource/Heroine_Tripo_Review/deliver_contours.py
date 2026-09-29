import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;O=R/'ContourRepair';D=O/'Delivery';D.mkdir(exist_ok=True);(D/'renders').mkdir(exist_ok=True);(D/'textures').mkdir(exist_ok=True)
def signature(ob):
 me=ob.data
 return hashlib.sha256(repr(([tuple(v.co) for v in me.vertices],[tuple(p.vertices) for p in me.polygons],[[tuple(d.uv) for d in u.data] for u in me.uv_layers])).encode()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(R/'BoundaryLocal/Heroine_BoundaryLocal.blend'))
protected={o.name:signature(o) for o in bpy.context.scene.objects if o.type=='MESH' and o.name!='Heroine_BoundaryLocal' and o.name!='Lower_Lid_Skin_-1'}
base=bpy.data.objects['Heroine_BoundaryLocal'];baseverts=[tuple(v.co) for v in base.data.vertices]
bpy.ops.wm.open_mainfile(filepath=str(O/'Heroine_ContourRepair_ReadyPaint.blend'));bpy.context.preferences.filepaths.save_version=0
body=bpy.data.objects['Heroine_ContourRepair']
# Remove disconnected shader experiments; keep the actual final base-color source.
for m in body.data.materials:
 if not m.use_nodes:continue
 nt=m.node_tree;needed=set()
 def collect(node):
  if node in needed:return
  needed.add(node)
  for inp in node.inputs:
   for link in inp.links:collect(link.from_node)
 for n in nt.nodes:
  if n.type=='OUTPUT_MATERIAL':collect(n)
 for n in list(nt.nodes):
  if n not in needed:nt.nodes.remove(n)
bpy.data.orphans_purge(do_recursive=True)
scene_materials=set(m for ob in bpy.context.scene.objects if ob.type=='MESH' for m in ob.data.materials if m)
used_images=set(n.image for m in scene_materials if m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
for im in used_images:
 if im.size[0]==0:raise RuntimeError('Missing texture '+im.name)
 im.filepath_raw=str(D/'textures'/(Path(im.name).stem+'.png'));im.file_format='PNG';im.save();im.pack()
sc=bpy.context.scene;sc.cycles.samples=40;sc.render.use_border=False;sc.render.use_crop_to_border=False;cam=sc.camera
def render(name,loc,target,scale):
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.resolution_x=sc.render.resolution_y=1100;sc.render.filepath=str(D/'renders'/f'{name}.png');bpy.ops.render.render(write_still=True)
render('eye',(-.034,-3,.902),(-.034,0,.902),.10)
render('face',(0,-3,.862),(0,0,.862),.30)
render('angle',(-.9,-3,.878),(0,0,.878),.25)
render('opposite_angle',(.65,-3,.878),(0,0,.878),.25)
cam.location=(0,-3,.862);cam.rotation_euler=(Vector((0,0,.862))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.30
meshes=[o for o in sc.objects if o.type=='MESH'];report={'protected_objects_unchanged':{n:signature(bpy.data.objects[n])==s for n,s in protected.items()},'blend_triangles':sum(len(p.vertices)-2 for o in meshes for p in o.data.polygons),'mesh_objects':len(meshes),'source_version':'BoundaryLocal','scope':'local forehead topology, marked corner sculpt, local hair/skin texture retouch, lower lid band end fitting'}
bpy.ops.object.select_all(action='DESELECT')
for ob in meshes:ob.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.fbx(filepath=str(D/'Heroine_ContourRepair.fbx'),use_selection=True,object_types={'MESH'},bake_anim=False,path_mode='COPY',embed_textures=True,axis_forward='-Z',axis_up='Y')
bpy.ops.wm.save_as_mainfile(filepath=str(D/'Heroine_ContourRepair.blend'))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(D/'Heroine_ContourRepair.fbx'))
report['fbx_triangles']=sum(len(p.vertices)-2 for o in bpy.context.scene.objects if o.type=='MESH' for p in o.data.polygons);report['missing_images']=[im.name for im in bpy.data.images if im.source=='FILE' and im.size[0]==0];report['data_checks_pass']=all(report['protected_objects_unchanged'].values()) and report['blend_triangles']==report['fbx_triangles'] and not report['missing_images']
(D/'validation.json').write_text(json.dumps(report,indent=2));print('VALIDATION',json.dumps(report),flush=True)
