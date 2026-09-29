import bpy,json,hashlib,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;O=R/'DetailFinish2';D=O/'Delivery';D.mkdir(exist_ok=True);(D/'renders').mkdir(exist_ok=True);(D/'textures').mkdir(exist_ok=True)
S=R/'DetailFinish/Delivery/Heroine_DetailFinish.blend';sourcehash=hashlib.sha256(S.read_bytes()).hexdigest()
def state(o):
 m=o.data;return {'coords':[tuple(v.co) for v in m.vertices],'faces':[tuple(p.vertices) for p in m.polygons],'uv':[[tuple(d.uv) for d in u.data] for u in m.uv_layers]}
bpy.ops.wm.open_mainfile(filepath=str(S));before={o.name:state(o) for o in bpy.context.scene.objects if o.type=='MESH'}
stage='polished_stage.blend' if '--polished' in sys.argv else 'lidblend_candidate.blend' if '--use-lidblend' in sys.argv else 'safe_stage.blend';bpy.ops.wm.open_mainfile(filepath=str(O/stage));bpy.context.preferences.filepaths.save_version=0;body=bpy.data.objects['Heroine_DetailFinish2'];after=state(body);old=before['Heroine_DetailFinish']
protected=['Iris_Surface_-1','Iris_Surface_1','Sclera_-1','Sclera_1','Lower_Eyelid_-1','Lower_Eyelid_1','Lower_Lid_Skin_1','Heroine_Pearl_Bracelet']
report={'source_sha256':sourcehash,'selected_stage':stage,'protected_meshes_unchanged':all(before[n]==state(bpy.data.objects[n]) for n in protected),'mouth_vertices_unchanged':all(a==b for a,b in zip(old['coords'],after['coords']) if abs(a[0])<.024 and .847<a[2]<.873),'body_vertices_before':len(old['coords']),'body_vertices_after':len(after['coords']),'body_faces_before':len(old['faces']),'body_faces_after':len(after['faces'])}
# Match original face identities to ensure UV edits stay in the declared eyelid patches or added pocket faces.
oldmap={};li=0
for face in old['faces']:oldmap[face]=old['uv'][0][li:li+len(face)];li+=len(face)
unexpected=[]
for p in body.data.polygons:
 key=tuple(p.vertices)
 if key not in oldmap:continue
 newuv=[tuple(body.data.uv_layers.active.data[l].uv) for l in p.loop_indices]
 if newuv!=oldmap[key] and not body.data.materials[p.material_index].name.startswith('M_EyelidPatch'):unexpected.append(p.index)
report['unexpected_uv_changed_faces']=unexpected
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];report['triangles']=sum(len(p.vertices)-2 for o in meshes for p in o.data.polygons)
materials=set(m for o in meshes for m in o.data.materials if m)
for m in materials:
 if not m.use_nodes:continue
 for n in list(m.node_tree.nodes):
  if n.type=='TEX_IMAGE' and not any(s.is_linked for s in n.outputs):m.node_tree.nodes.remove(n)
images=set(n.image for m in materials if m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
for im in images:im.filepath_raw=str(D/'textures'/(im.name+'.png'));im.file_format='PNG';im.save();im.pack()
sc=bpy.context.scene;sc.cycles.samples=24;sc.render.use_border=False;sc.render.use_crop_to_border=False
views=[('eye',(-.034,-3,.902),(-.034,0,.902),.10),('face',(0,-3,.862),(0,0,.862),.30),('angle',(-.9,-3,.878),(0,0,.878),.25),('opposite',(.7,-3,.878),(0,0,.878),.25),('collar',(0,-3,.765),(0,0,.765),.23),('skirt',(0,-3,.505),(0,0,.505),.34),('head_back',(0,3,.89),(0,0,.89),.28),('full_front',(0,-3,.5),(0,0,.5),1.13),('full_back',(0,3,.5),(0,0,.5),1.13)]
for name,loc,target,scale in views:
 if '--polished' in sys.argv and name in ['eye','skirt','head_back','full_back'] and (D/'renders'/f'{name}.png').is_file():continue
 cam=sc.camera;cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.resolution_x=1000;sc.render.resolution_y=1100 if name.startswith('full') else 1000;sc.render.filepath=str(D/'renders'/f'{name}.png');bpy.ops.render.render(write_still=True);print('VERIFIED_RENDER',name,flush=True)
cam=sc.camera;cam.location=(0,-3,.862);cam.rotation_euler=(Vector((0,0,.862))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.3;sc.render.resolution_x=sc.render.resolution_y=1000
bpy.ops.object.select_all(action='DESELECT')
for ob in meshes:ob.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.export_scene.fbx(filepath=str(D/'Heroine_DetailFinish2.fbx'),use_selection=True,object_types={'MESH'},bake_anim=False,path_mode='COPY',embed_textures=True,axis_forward='-Z',axis_up='Y');bpy.ops.wm.save_as_mainfile(filepath=str(D/'Heroine_DetailFinish2.blend'))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(D/'Heroine_DetailFinish2.fbx'));report['fbx_triangles']=sum(len(p.vertices)-2 for o in bpy.context.scene.objects if o.type=='MESH' for p in o.data.polygons);report['missing_images']=[im.name for im in bpy.data.images if im.source=='FILE' and im.size[0]==0];report['source_unchanged']=hashlib.sha256(S.read_bytes()).hexdigest()==sourcehash
report['pass']=report['protected_meshes_unchanged'] and report['mouth_vertices_unchanged'] and not unexpected and not report['missing_images'] and report['source_unchanged'] and report['triangles']==report['fbx_triangles'];(D/'validation.json').write_text(json.dumps(report,indent=2));print('VALIDATION',json.dumps(report),flush=True)
