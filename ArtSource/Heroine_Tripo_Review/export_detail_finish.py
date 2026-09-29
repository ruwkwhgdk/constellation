import bpy,json,hashlib,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;O=R/'DetailFinish';D=O/'Delivery';D.mkdir(exist_ok=True);(D/'textures').mkdir(exist_ok=True);(D/'renders').mkdir(exist_ok=True)
S=R/'NeutralExpression/Heroine_NeutralExpression.blend';sourcehash=hashlib.sha256(S.read_bytes()).hexdigest()
def state(o):
 m=o.data;return {'coords':[tuple(v.co) for v in m.vertices],'faces':[tuple(p.vertices) for p in m.polygons],'uv':[[tuple(d.uv) for d in u.data] for u in m.uv_layers]}
bpy.ops.wm.open_mainfile(filepath=str(S));before={o.name:state(o) for o in bpy.context.scene.objects if o.type=='MESH'}
bpy.ops.wm.open_mainfile(filepath=str(O/'rim_candidate.blend'));bpy.context.preferences.filepaths.save_version=0
if '--accessory-finish' in sys.argv:
 bracelet=bpy.data.objects['Heroine_Pearl_Bracelet'];bpy.context.view_layer.objects.active=bracelet
 modifier=bracelet.modifiers.new('Pearl_surface_finish','SUBSURF');modifier.levels=1;modifier.render_levels=1
 bpy.ops.object.modifier_apply(modifier=modifier.name)
body=bpy.data.objects['Heroine_DetailFinish'];after=state(body);old=before['Heroine_NeutralExpression']
protected=['Iris_Surface_-1','Iris_Surface_1','Sclera_-1','Sclera_1','Lower_Eyelid_-1','Lower_Eyelid_1','Lower_Lid_Skin_1']
changed=[i for i,(a,b) in enumerate(zip(old['coords'],after['coords'])) if a!=b]
report={'source_sha256':sourcehash,'body_topology_unchanged':old['faces']==after['faces'],'body_uv_unchanged':old['uv']==after['uv'],'protected_eye_meshes_unchanged':all(before[n]==state(bpy.data.objects[n]) for n in protected),'mouth_extreme_corners_unchanged':all(a==b for a,b in zip(old['coords'],after['coords']) if .0106<abs(a[0])<.02 and .851<a[2]<.87),'body_modified_vertices':len(changed)}
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];report['triangles']=sum(len(p.vertices)-2 for o in meshes for p in o.data.polygons)
materials=set(m for o in meshes for m in o.data.materials if m)
for m in materials:
 if m.use_nodes:
  for n in list(m.node_tree.nodes):
   if n.type=='TEX_IMAGE' and not any(s.is_linked for s in n.outputs):m.node_tree.nodes.remove(n)
images=set(n.image for m in materials if m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
for im in images:
 im.filepath_raw=str(D/'textures'/(im.name+'.png'));im.file_format='PNG';im.save();im.pack()
sc=bpy.context.scene;sc.cycles.samples=24;sc.render.use_border=False;sc.render.use_crop_to_border=False
def render(name,loc,target,scale,res=(1000,1000)):
 unchanged=['face','angle','eye','mouth','full_back'] if '--accessory-finish' in sys.argv else ['mouth','full_back','hand_top','hand_palm']
 if name in unchanged and (D/'renders'/f'{name}.png').is_file():return
 cam=sc.camera;cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.resolution_x,sc.render.resolution_y=res;sc.render.filepath=str(D/'renders'/f'{name}.png');bpy.ops.render.render(write_still=True);print('FINAL_RENDER',name,flush=True)
render('face',(0,-3,.862),(0,0,.862),.30)
render('angle',(-.9,-3,.878),(0,0,.878),.25)
render('eye',(-.034,-3,.902),(-.034,0,.902),.10)
render('mouth',(0,-3,.859),(0,0,.859),.055,(1000,650))
render('full_front',(0,-3,.5),(0,0,.5),1.13,(1100,1200))
render('full_back',(0,3,.5),(0,0,.5),1.13,(1100,1200))
render('hand_top',(-.4,-.3,3),(-.4,0,.785),.135)
render('hand_palm',(-.4,-.3,-3),(-.4,0,.785),.135)
cam=sc.camera;cam.location=(0,-3,.862);cam.rotation_euler=(Vector((0,0,.862))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.30;sc.render.resolution_x=sc.render.resolution_y=1000
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.fbx(filepath=str(D/'Heroine_DetailFinish.fbx'),use_selection=True,object_types={'MESH'},bake_anim=False,path_mode='COPY',embed_textures=True,axis_forward='-Z',axis_up='Y')
bpy.ops.wm.save_as_mainfile(filepath=str(D/'Heroine_DetailFinish.blend'))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(D/'Heroine_DetailFinish.fbx'))
report['fbx_triangles']=sum(len(p.vertices)-2 for o in bpy.context.scene.objects if o.type=='MESH' for p in o.data.polygons);report['missing_images']=[im.name for im in bpy.data.images if im.source=='FILE' and im.size[0]==0];report['source_unchanged']=hashlib.sha256(S.read_bytes()).hexdigest()==sourcehash
report['pass']=all(report[k] for k in ['body_topology_unchanged','body_uv_unchanged','protected_eye_meshes_unchanged','mouth_extreme_corners_unchanged','source_unchanged']) and report['triangles']==report['fbx_triangles'] and not report['missing_images']
(D/'validation.json').write_text(json.dumps(report,indent=2));print('DELIVERY_VALIDATION',json.dumps(report),flush=True)
