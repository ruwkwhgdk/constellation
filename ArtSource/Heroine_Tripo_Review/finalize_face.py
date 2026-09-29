import bpy,bmesh,json,math,shutil
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;O=R/'FaceClean'
bpy.ops.wm.open_mainfile(filepath=str(O/'Heroine_FaceClean.blend'))
bpy.context.preferences.filepaths.save_version=0
body=bpy.data.objects['Heroine_FaceClean']
# Collapse the sub-pixel central iris fan and leave ordinary nondegenerate triangles.
for ob in bpy.context.scene.objects:
 if ob.type=='MESH' and ob.name.startswith('Iris_Clean'):
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=2e-7)
  bad=[f for f in bm.faces if f.calc_area()<1e-14]
  if bad:bmesh.ops.delete(bm,geom=bad,context='FACES')
  bm.to_mesh(ob.data);bm.free()
sc=bpy.context.scene;sc.view_layers[0].material_override=None;sc.cycles.samples=32;cam=sc.camera
def render(name,loc,target,scale,res=(1100,1100)):
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.resolution_x,sc.render.resolution_y=res;sc.render.filepath=str(O/'renders'/f'{name}.png');bpy.ops.render.render(write_still=True)
render('face',(0,-3,.862),(0,0,.862),.30)
render('angle',(-1.3,-3,.882),(0,0,.882),.25)
render('side',(-2.7,-3,.882),(0,0,.882),.25)
render('front',(0,-3,.5),(0,0,.5),1.25,(900,1100))
# Expose a useful front face view on opening the Blender source.
cam.location=(0,-3,.862);cam.rotation_euler=(Vector((0,0,.862))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.30;sc.render.resolution_x=sc.render.resolution_y=1100
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
def stats():
 obs=[o for o in bpy.context.scene.objects if o.type=='MESH']
 return {'triangles':sum(len(p.vertices)-2 for o in obs for p in o.data.polygons),'mesh_objects':len(obs),'finite_coordinates':all(math.isfinite(c) for o in obs for v in o.data.vertices for c in v.co),'missing_uv':[o.name for o in obs if not o.data.uv_layers],'missing_images':[i.name for i in bpy.data.images if i.source=='FILE' and i.size[0]==0]}
report={'blend':stats()}
bm=bmesh.new();bm.from_mesh(body.data)
face_edges=[e for e in bm.edges if len(e.link_faces)>0 and all(body.data.materials[f.material_index].name in ['Face_Skin_Clean','Lash_Clean','Lid_Waterline'] for f in e.link_faces) and all(.875<v.co.z<.93 and v.co.y<-.013 and .005<abs(v.co.x)<.061 for v in e.verts)]
report['skin_region_edges_over_two_faces']=sum(len(e.link_faces)>2 for e in face_edges)
report['skin_region_boundary_edges']=sum(e.is_boundary for e in face_edges)
bm.free()
# Keep texture files alongside the packed Blender and embedded FBX assets.
(O/'textures').mkdir(exist_ok=True)
for im in bpy.data.images:
 if im.users and im.type=='IMAGE' and im.size[0]>0 and im.name not in ['Render Result','Viewer Node']:
  try:
   dst=O/'textures'/(bpy.path.clean_name(im.name)+'.png');im.filepath_raw=str(dst);im.file_format='PNG';im.save();im.pack()
  except RuntimeError:pass
bpy.ops.object.select_all(action='DESELECT')
for ob in meshes:ob.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.fbx(filepath=str(O/'Heroine_FaceClean.fbx'),use_selection=True,object_types={'MESH'},bake_anim=False,path_mode='COPY',embed_textures=True,axis_forward='-Z',axis_up='Y')
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Heroine_FaceClean.blend'))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(O/'Heroine_FaceClean.fbx'));report['fbx']=stats()
report['pass']=report['blend']['triangles']==report['fbx']['triangles'] and all(x['finite_coordinates'] and not x['missing_uv'] and not x['missing_images'] for x in [report['blend'],report['fbx']]) and report['skin_region_edges_over_two_faces']==0
(O/'validation.json').write_text(json.dumps(report,indent=2));print('FACE_VALIDATION',json.dumps(report))
