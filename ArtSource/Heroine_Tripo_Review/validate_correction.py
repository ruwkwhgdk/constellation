import bpy,json,math,hashlib,zipfile
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'Corrected'
# Compare retained UV loops to the unmodified reference mesh, independently of rendering.
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Tripo_Source_Inspection.blend'))
src=next(o for o in bpy.context.scene.objects if o.type=='MESH')
source_bounds=[src.matrix_world@Vector(c) for c in src.bound_box]
def uv_signatures(o):
    uv=o.data.uv_layers.active
    return {tuple(sorted((tuple(round(float(c),6) for c in uv.data[li].uv) for li in p.loop_indices))) for p in o.data.polygons}
source_uv=uv_signatures(src)
bpy.ops.wm.open_mainfile(filepath=str(OUT/'Heroine_Tripo_Corrected.blend'))
body=bpy.data.objects['Heroine_Tripo_Corrected']
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
report={'blend_triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes),'retained_polygon_uvs_match_source':uv_signatures(body).issubset(source_uv),'finite_coordinates':all(math.isfinite(c) for o in meshes for v in o.data.vertices for c in v.co),'body_material_face_counts':{m.name:sum(p.material_index==i for p in body.data.polygons) for i,m in enumerate(body.data.materials)},'armatures':sum(o.type=='ARMATURE' for o in bpy.context.scene.objects)}
archive=Path('C:/Users/User/Downloads/anime character 3d model.zip')
with zipfile.ZipFile(archive) as z:
    for name in ['anime+character+3d+model.fbx','anime+character+3d+model.fbm/anime+character+3d+model_basecolor.jpg']:
        report['original_unchanged_'+Path(name).suffix]=hashlib.sha256(z.read(name)).hexdigest()==hashlib.sha256((ROOT/'source'/name).read_bytes()).hexdigest()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(OUT/'Heroine_Tripo_Corrected.fbx'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
report['fbx_meshes']=len(meshes);report['fbx_triangles']=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes)
report['fbx_missing_uv']=[o.name for o in meshes if not o.data.uv_layers]
report['missing_images']=[im.filepath for im in bpy.data.images if im.source=='FILE' and im.size[0]==0]
report['pass']=report['fbx_triangles']==report['blend_triangles'] and report['retained_polygon_uvs_match_source'] and report['finite_coordinates'] and not report['missing_images'] and not report['fbx_missing_uv'] and report['original_unchanged_.fbx'] and report['original_unchanged_.jpg']
(OUT/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
# Matching pre-correction facial render: same camera, lights, exposure, samples.
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Tripo_Source_Inspection.blend'))
sc=bpy.context.scene;sc.cycles.samples=32;cam=sc.camera;target=Vector((0,0,.862));cam.location=(0,-3,.862);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.30
sc.render.resolution_x=1100;sc.render.resolution_y=1100;sc.render.filepath=str(OUT/'renders/face_before.png');bpy.ops.render.render(write_still=True)
