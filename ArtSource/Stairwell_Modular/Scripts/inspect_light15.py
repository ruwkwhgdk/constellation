"""Import and inspect generated light; retain original GLB and normalize review copy."""
import bpy, bmesh, json, math
from pathlib import Path
from mathutils import Vector, Matrix
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Models'/'15_Light'
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(OUT/'light15_raw_v001.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
assert meshes, 'No mesh imported'
report={'source':'light15_raw_v001.glb','requested_face_limit':3000,'objects':[],'status':'awaiting_user_review'}
def bounds():
    pts=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
    low=Vector([min(p[i] for p in pts) for i in range(3)])
    high=Vector([max(p[i] for p in pts) for i in range(3)])
    return low,high
low,high=bounds(); report['import_dimensions_m']=list(high-low)
for o in meshes:
    world=o.matrix_world.copy(); o.parent=None; o.matrix_world=world
axis=max(range(3),key=lambda i:(high-low)[i])
rot=Matrix.Identity(4)
if axis==1: rot=Matrix.Rotation(-math.pi/2,4,'Z')
if axis==2: rot=Matrix.Rotation(math.pi/2,4,'Y')
for o in meshes: o.matrix_world=rot@o.matrix_world
bpy.context.view_layer.update(); low,high=bounds()
scale=1.2/max(high-low); center=(high+low)/2
transform=Matrix.Scale(scale,4)@Matrix.Translation(-center)
for o in meshes: o.matrix_world=transform@o.matrix_world
bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')
for o in meshes: o.select_set(True)
bpy.context.view_layer.objects.active=meshes[0]
bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
total=0
for idx,o in enumerate(meshes):
    o.name=f'SM_Stairwell_Light15_Part{idx:02d}'
    o.data.calc_loop_triangles(); tris=len(o.data.loop_triangles); total+=tris
    bm=bmesh.new(); bm.from_mesh(o.data)
    row={'name':o.name,'vertices':len(o.data.vertices),'triangles':tris,'material_slots':len(o.material_slots),
         'uv_layers':len(o.data.uv_layers),'boundary_edges':sum(e.is_boundary for e in bm.edges),
         'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges)}
    bm.free(); report['objects'].append(row)
low,high=bounds(); report['review_dimensions_cm']=[round(v*100,3) for v in high-low]
report['triangles']=total; report['face_limit_pass']=total<=3000
report['scale_policy']='Review copy uniformly scaled to 120cm maximum dimension; not source-measured size.'
report['materials']=[]
for m in {s.material for o in meshes for s in o.material_slots if s.material}:
    row={'name':m.name,'textures':[]}
    if m.node_tree:
        for n in m.node_tree.nodes:
            if n.type=='TEX_IMAGE' and n.image:
                row['textures'].append({'image':n.image.name,'size':list(n.image.size),'colorspace':n.image.colorspace_settings.name})
    report['materials'].append(row)
report['limitations']=['Not approved for import','No Unreal collision or lighting setup','No automatic emission split','No full kit generation yet','Original GLB retained unchanged']
scene=bpy.context.scene; scene.name='Light15_Review'; scene.unit_settings.system='METRIC'
scene.world.use_nodes=True
bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND'); bg.inputs[0].default_value=(.18,.20,.23,1); bg.inputs[1].default_value=.5
for loc,energy in [((0,-2,3),220),((0,2,2),170),((1,0,-2),150)]:
    d=bpy.data.lights.new('ReviewSoftbox','AREA'); d.energy=energy; d.size=2
    o=bpy.data.objects.new('ReviewSoftbox',d); scene.collection.objects.link(o); o.location=loc
    o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('ReviewCamera'); cam=bpy.data.objects.new('ReviewCamera',cd); scene.collection.objects.link(cam)
scene.camera=cam; cd.type='ORTHO'; cd.ortho_scale=1.65
scene.render.engine='CYCLES'; scene.cycles.samples=32; scene.cycles.use_denoising=True
scene.render.resolution_x=1400; scene.render.resolution_y=850; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.render.film_transparent=False
for name,loc in [('light15_view_a.png',(1.25,-1.75,1.25)),('light15_view_b.png',(-1.25,1.75,-1.25))]:
    cam.location=loc; cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(OUT/name); bpy.ops.render.render(write_still=True)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'light15_review_v001.blend'))
(OUT/'inspection_v001.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('LIGHT15_INSPECTED',json.dumps({'triangles':total,'face_limit_pass':total<=3000,'dimensions_cm':report['review_dimensions_cm']}))
