import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;O=R/'Refined'
bpy.ops.wm.open_mainfile(filepath=str(O/'Heroine_Refined.blend'))
bpy.context.preferences.filepaths.save_version=0
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
for o in meshes:
 if o.name.startswith(('Sclera','Iris_Surface','Lower_Lid_Skin')):
  bm=bmesh.new();bm.from_mesh(o.data)
  bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
  bm.normal_update()
  for f in bm.faces:
   if f.normal.y>0:f.normal_flip()
  bm.to_mesh(o.data);bm.free();o.data.update()
def stats():
 return {'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in bpy.context.scene.objects if o.type=='MESH'),'mesh_objects':sum(o.type=='MESH' for o in bpy.context.scene.objects),'missing_uv':[o.name for o in bpy.context.scene.objects if o.type=='MESH' and not o.data.uv_layers],'missing_images':[im.name for im in bpy.data.images if im.source=='FILE' and not im.size[0]],'finite':all(math.isfinite(c) for o in bpy.context.scene.objects if o.type=='MESH' for v in o.data.vertices for c in v.co)}
report={'blend':stats()}
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=bpy.data.objects['Heroine_Refined']
bpy.ops.export_scene.fbx(filepath=str(O/'Heroine_Refined.fbx'),use_selection=True,object_types={'MESH'},bake_anim=False,path_mode='COPY',embed_textures=True,axis_forward='-Z',axis_up='Y')
sc=bpy.context.scene;cam=sc.camera;cam.location=(0,-3,.5);target=Vector((0,0,.5));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.25;sc.render.resolution_x=900;sc.render.resolution_y=1100
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Heroine_Refined.blend'))
sc.render.filepath=str(O/'renders/front.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(O/'Heroine_Refined.fbx'))
report['fbx']=stats();report['pass']=report['blend']['triangles']==report['fbx']['triangles'] and all(x['finite'] and not x['missing_uv'] and not x['missing_images'] for x in [report['blend'],report['fbx']])
(O/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
