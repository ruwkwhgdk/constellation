import bpy,json,hashlib,shutil
from pathlib import Path
R=Path(__file__).resolve().parent;O=R/'NeutralExpression';(O/'textures').mkdir(exist_ok=True)
def mesh_state(ob):
 me=ob.data
 return {'coords':[tuple(v.co) for v in me.vertices],'faces':[tuple(p.vertices) for p in me.polygons],'uv':[[tuple(d.uv) for d in u.data] for u in me.uv_layers]}
bpy.ops.wm.open_mainfile(filepath=str(R/'ContourRepair/Delivery/Heroine_ContourRepair.blend'));source={o.name:mesh_state(o) for o in bpy.context.scene.objects if o.type=='MESH'}
bpy.ops.wm.open_mainfile(filepath=str(O/'Heroine_NeutralExpression.blend'));bpy.context.preferences.filepaths.save_version=0
body=bpy.data.objects['Heroine_NeutralExpression'];old=source['Heroine_ContourRepair'];new=mesh_state(body);changed=[i for i,(a,b) in enumerate(zip(old['coords'],new['coords'])) if a!=b]
report={'body_topology_unchanged':old['faces']==new['faces'],'body_uv_unchanged':old['uv']==new['uv'],'mouth_width_unchanged':all(a[0]==b[0] for a,b in zip(old['coords'],new['coords'])),'changes_confined_to_mouth':all(abs(old['coords'][i][0])<.024 and .847<old['coords'][i][2]<.873 and old['coords'][i][1]<-.01 for i in changed),'other_objects_unchanged':all(mesh_state(bpy.data.objects[n])==v for n,v in source.items() if n!='Heroine_ContourRepair'),'modified_vertices':len(changed)}
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];report['triangles']=sum(len(p.vertices)-2 for o in meshes for p in o.data.polygons)
materials=set(m for o in meshes for m in o.data.materials if m);images=set(n.image for m in materials if m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
for im in images:
 src=Path(bpy.path.abspath(im.filepath));dest=O/'textures'/src.name
 if src.is_file():shutil.copy2(src,dest);im.filepath=str(dest)
 im.pack()
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.fbx(filepath=str(O/'Heroine_NeutralExpression.fbx'),use_selection=True,object_types={'MESH'},bake_anim=False,path_mode='COPY',embed_textures=True,axis_forward='-Z',axis_up='Y')
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Heroine_NeutralExpression.blend'))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(O/'Heroine_NeutralExpression.fbx'))
report['fbx_triangles']=sum(len(p.vertices)-2 for o in bpy.context.scene.objects if o.type=='MESH' for p in o.data.polygons);report['missing_images']=[im.name for im in bpy.data.images if im.source=='FILE' and im.size[0]==0]
report['pass']=all(report[k] for k in ['body_topology_unchanged','body_uv_unchanged','mouth_width_unchanged','changes_confined_to_mouth','other_objects_unchanged']) and report['triangles']==report['fbx_triangles'] and not report['missing_images']
(O/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
