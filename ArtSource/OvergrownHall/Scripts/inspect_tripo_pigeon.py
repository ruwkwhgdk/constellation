import bpy,json,math
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parents[1]/'Bird/Tripo_v001'
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.import_scene.gltf(filepath=str(OUT/'OH_Pigeon_Tripo_v001.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
points=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
lo=Vector([min(p[i] for p in points) for i in range(3)]); hi=Vector([max(p[i] for p in points) for i in range(3)])
center=(lo+hi)/2; size=max(hi-lo)
report=dict(status='downloaded_and_opened',source='Tripo web H3.1',triangles=sum(len(p.vertices)-2 for o in meshes for p in o.data.polygons),vertices=sum(len(o.data.vertices) for o in meshes),mesh_objects=len(meshes),material_slots=sum(len(o.data.materials) for o in meshes),uv_layers=[len(o.data.uv_layers) for o in meshes],images=[dict(name=i.name,size=list(i.size)) for i in bpy.data.images if i.size[0]],bounds_source_units=list(hi-lo),finite_vertices=all(math.isfinite(v) for p in points for v in p),has_armature=any(o.type=='ARMATURE' for o in bpy.context.scene.objects),rigging_status='not_started',appearance='awaiting user adoption',pose='raised wings; neutral-pose adjustment required before reusing old motion')
assert report['triangles']<=20000,report
(OUT/'inspection.json').write_text(json.dumps(report,indent=2))
scene=bpy.context.scene; scene.render.engine='CYCLES'; scene.cycles.samples=24
scene.render.resolution_x=900; scene.render.resolution_y=800; scene.render.resolution_percentage=100
scene.world.use_nodes=True; scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.18,.20,.22,1); scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5
for offset,power in [((1,-2,3),600),((-2,1,2),450)]:
    pos=center+Vector(offset)*size
    bpy.ops.object.light_add(type='AREA',location=pos); light=bpy.context.object; light.data.energy=power*size*size; light.data.size=size*2
    light.rotation_euler=(center-pos).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(); cam=bpy.context.object; cam.data.type='ORTHO'; cam.data.ortho_scale=size*1.25; scene.camera=cam
for name,offset in [('front',(0,-3,.5)),('three_quarter',(2,-3,1))]:
    cam.location=center+Vector(offset)*size; cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(OUT/(name+'.png')); bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'tripo_pigeon_review.blend'))
print('TRIPO_PIGEON_INSPECTED',json.dumps(report))
