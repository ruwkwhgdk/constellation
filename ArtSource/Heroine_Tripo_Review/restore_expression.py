"""Restore the user's preferred Refined appearance; retain texture, UV, topology and materials."""
import bpy,math,json,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;O=R/'DetailPreserved';O.mkdir(exist_ok=True);(O/'renders').mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'Refined/Heroine_Refined.blend'))
bpy.context.preferences.filepaths.save_version=0
body=bpy.data.objects['Heroine_Refined'];me=body.data
def signature():
 return {'polygons':[list(p.vertices) for p in me.polygons],'uv':[[list(d.uv) for d in uv.data] for uv in me.uv_layers],'materials':[m.name for m in me.materials],'material_indices':[p.material_index for p in me.polygons]}
before=signature();original=[v.co.copy() for v in me.vertices]
adj=[[] for v in me.vertices];vm=[set() for v in me.vertices]
for e in me.edges:
 a,b=e.vertices;adj[a].append(b);adj[b].append(a)
for p in me.polygons:
 for vi in p.vertices:vm[vi].add(me.materials[p.material_index].name)
eligible=[]
for v in me.vertices:
 x,y,z=v.co
 # Confine geometric relaxation to the existing eyebrows and upper lash relief.
 if .012<abs(x)<.049 and y<-.041 and (.903<z<.9085 or .914<z<.921):
  if vm[v.index].issubset({'M_Details','M_Skin'}):eligible.append(v.index)
for iteration in range(2):
 changes=[]
 for i in eligible:
  if not adj[i]:continue
  avg=sum((me.vertices[j].co for j in adj[i]),Vector())/len(adj[i]);delta=(avg-me.vertices[i].co)*.045
  # Keep the drawn outline fixed in front view; relax depth only.
  desired=me.vertices[i].co.copy();desired.y+=delta.y;desired.y=max(original[i].y-.00006,min(original[i].y+.00006,desired.y));changes.append((i,desired))
 for i,p in changes:me.vertices[i].co=p
me.update();after=signature()
report={'baseline':'Refined/Heroine_Refined.blend','topology_unchanged':before['polygons']==after['polygons'],'uv_unchanged':before['uv']==after['uv'],'materials_unchanged':before['materials']==after['materials'] and before['material_indices']==after['material_indices'],'texture_edits':False,'new_geometry':False,'modified_vertices':sum((v.co-original[i]).length>1e-10 for i,v in enumerate(me.vertices)),'max_vertex_displacement':max((v.co-original[i]).length for i,v in enumerate(me.vertices)),'projected_eye_outline_unchanged':all(v.co.x==original[i].x and v.co.z==original[i].z for i,v in enumerate(me.vertices))}
body.name='Heroine_DetailPreserved'
sc=bpy.context.scene;sc.view_layers[0].material_override=None;sc.cycles.samples=32;cam=sc.camera
def render(name,loc,target,scale):
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.resolution_x=sc.render.resolution_y=1100;sc.render.filepath=str(O/'renders'/f'{name}.png');bpy.ops.render.render(write_still=True)
render('eye',(-.034,-3,.902),(-.034,0,.902),.10)
render('face',(0,-3,.862),(0,0,.862),.30)
render('angle',(-1,-3,.862),(0,0,.862),.30)
cam.location=(0,-3,.862);cam.rotation_euler=(Vector((0,0,.862))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.30
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];report['blend_triangles']=sum(len(p.vertices)-2 for o in meshes for p in o.data.polygons)
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.fbx(filepath=str(O/'Heroine_DetailPreserved.fbx'),use_selection=True,object_types={'MESH'},bake_anim=False,path_mode='COPY',embed_textures=True,axis_forward='-Z',axis_up='Y')
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Heroine_DetailPreserved.blend'))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(O/'Heroine_DetailPreserved.fbx'))
report['fbx_triangles']=sum(len(p.vertices)-2 for o in bpy.context.scene.objects if o.type=='MESH' for p in o.data.polygons)
report['missing_images']=[i.name for i in bpy.data.images if i.source=='FILE' and i.size[0]==0]
report['pass']=report['topology_unchanged'] and report['uv_unchanged'] and report['materials_unchanged'] and report['projected_eye_outline_unchanged'] and report['blend_triangles']==report['fbx_triangles'] and not report['missing_images']
(O/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
