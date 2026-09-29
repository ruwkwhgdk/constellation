"""Prepare a dimensioned review copy; keep the downloaded GLB unchanged."""
import bpy, bmesh, json, math
from pathlib import Path
from mathutils import Vector, Matrix
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Models'/'14_Door'
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(OUT/'door14_raw_v001.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
assert meshes, 'No imported meshes'
def bounds():
    pts=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]),Vector([max(p[i] for p in pts) for i in range(3)])
def stats(o):
    o.data.calc_loop_triangles()
    bm=bmesh.new(); bm.from_mesh(o.data)
    row=dict(name=o.name,triangles=len(o.data.loop_triangles),vertices=len(o.data.vertices),boundary_edges=sum(e.is_boundary for e in bm.edges),nonmanifold_edges=sum(not e.is_manifold for e in bm.edges),uv_layers=len(o.data.uv_layers),material_slots=len(o.material_slots))
    bm.free(); return row
report={'source':'door14_raw_v001.glb','status':'awaiting_user_review','triangle_limit':3000}
report['raw_objects']=[stats(o) for o in meshes]
report['raw_triangles']=sum(r['triangles'] for r in report['raw_objects'])
low,high=bounds(); report['raw_dimensions_m']=list(high-low)
for o in meshes:
    world=o.matrix_world.copy(); o.parent=None; o.matrix_world=world
axis=max(range(3),key=lambda i:(high-low)[i])
rot=Matrix.Identity(4)
if axis==1: rot=Matrix.Rotation(math.pi/2,4,'X')
if axis==0: rot=Matrix.Rotation(-math.pi/2,4,'Y')
for o in meshes: o.matrix_world=rot@o.matrix_world
bpy.context.view_layer.update(); low,high=bounds()
scale=2.1/(high.z-low.z)
transform=Matrix.Scale(scale,4)@Matrix.Translation(-(low+high)/2)
for o in meshes: o.matrix_world=transform@o.matrix_world
bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')
for o in meshes: o.select_set(True)
bpy.context.view_layer.objects.active=meshes[0]
bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
for i,o in enumerate(meshes):
    o.name=f'SM_Stairwell_Door14_Part{i:02d}'
    bm=bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001)
    bm.to_mesh(o.data); bm.free(); o.data.update()
total=sum(stats(o)['triangles'] for o in meshes)
if total>3000:
    for o in meshes:
        bpy.context.view_layer.objects.active=o
        mod=o.modifiers.new('Review_Budget_3000','DECIMATE'); mod.ratio=2950/total
        bpy.ops.object.modifier_apply(modifier=mod.name)
report['review_objects']=[stats(o) for o in meshes]
report['review_triangles']=sum(r['triangles'] for r in report['review_objects'])
assert report['review_triangles']<=3000,report['review_triangles']
low,high=bounds(); report['review_dimensions_cm']=[round(v*100,3) for v in high-low]
report['scale_policy']='Uniform 210cm review height; width and thickness retained from generation. Final opening fit and hinge pivot pending.'
report['materials']=[]
for m in {s.material for o in meshes for s in o.material_slots if s.material}:
    report['materials'].append({'name':m.name,'textures':[{'name':n.image.name,'size':list(n.image.size),'colorspace':n.image.colorspace_settings.name} for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image] if m.node_tree else []})
report['not_done']=['Human appearance review','Exact door frame fit and hinge pivot','Collision','Unreal import']
scene=bpy.context.scene; scene.name='Door14_Review'; scene.unit_settings.system='METRIC'
scene.world.use_nodes=True
bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND'); bg.inputs[0].default_value=(.18,.20,.23,1); bg.inputs[1].default_value=.5
for loc,energy in [((1,-3,3),450),((-2,2,3),350),((0,3,0),200)]:
    d=bpy.data.lights.new('ReviewSoftbox','AREA'); d.energy=energy; d.size=3
    o=bpy.data.objects.new('ReviewSoftbox',d); scene.collection.objects.link(o); o.location=loc
    o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('ReviewCamera'); cam=bpy.data.objects.new('ReviewCamera',cd); scene.collection.objects.link(cam)
scene.camera=cam; cd.type='ORTHO'; cd.ortho_scale=2.65
scene.render.engine='CYCLES'; scene.cycles.samples=24; scene.cycles.use_denoising=True
scene.render.resolution_x=850; scene.render.resolution_y=1100; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
for name,loc in [('door14_view_a.png',(1,-4,1)),('door14_view_b.png',(-1,4,1))]:
    cam.location=loc; cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(OUT/name); bpy.ops.render.render(write_still=True)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'door14_review_v001.blend'))
(OUT/'inspection_v001.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('DOOR14_REVIEW_READY',json.dumps(report))
