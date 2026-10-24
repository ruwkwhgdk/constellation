"""Closed decorative underside candidates, metre modelling / centimetre FBX."""
import bpy, bmesh, math, json, random
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'ArtSource/SchoolOpening/WetFloor/ClosedLedge'
OUT.mkdir(parents=True,exist_ok=True)
assert not (OUT/'ClosedLedge.blend').exists(), 'Preserve prior source; review before regenerating.'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
mat=bpy.data.materials.new('PreviewStone');mat.diffuse_color=(.12,.16,.17,1)
mat.use_nodes=True
bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.12,.16,.17,1);bs.inputs['Roughness'].default_value=.85
report=[];objects=[]
for index in range(3):
 rng=random.Random(711+index);verts=[];faces=[];segments=16
 for i in range(segments+1):
  x=-6+12*i/segments
  depth=.75+(.28*math.sin(i*1.35+index)+.12*rng.random()) if i not in (0,segments) else .85
  front=.4 if i in (0,segments) else .4+.045*math.sin(i*1.8+index)
  # Constant flat top; shallow bevel shoulder; asymmetrical fractured underside.
  ring=[(x,-.4,0),(x,front,0),(x,front-.025,-.24),
        (x,front-.12,-depth),(x,-.24,-depth-.09),(x,-.4,-.37)]
  verts.extend(ring)
  if i:
   a=(i-1)*6;b=i*6
   for j in range(6):faces.append((a+j,a+(j+1)%6,b+(j+1)%6,b+j))
 faces.append(tuple(reversed(range(6))))
 faces.append(tuple(segments*6+j for j in range(6)))
 mesh=bpy.data.meshes.new('ClosedLedgeMesh');mesh.from_pydata(verts,[],faces);mesh.update()
 obj=bpy.data.objects.new('SM_S0_ClosedLedge_'+chr(65+index),mesh);scene.collection.objects.link(obj)
 bpy.context.view_layer.objects.active=obj;obj.select_set(True)
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(mesh);bm.free()
 bevel=obj.modifiers.new('Small worn edges','BEVEL');bevel.width=.018;bevel.segments=2
 bpy.ops.object.modifier_apply(modifier=bevel.name)
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.02);bpy.ops.object.mode_set(mode='OBJECT')
 obj.data.materials.append(mat)
 bm=bmesh.new();bm.from_mesh(obj.data)
 boundary=sum(e.is_boundary for e in bm.edges);nonmanifold=sum(not e.is_manifold for e in bm.edges)
 volume=bm.calc_volume(signed=True);bm.free()
 obj.data.calc_loop_triangles();tris=len(obj.data.loop_triangles)
 assert boundary==0 and nonmanifold==0 and volume>0
 assert all(math.isfinite(v) for p in obj.data.vertices for v in p.co)
 bpy.ops.export_scene.fbx(filepath=str(OUT/(obj.name+'.fbx')),use_selection=True,object_types={'MESH'},apply_unit_scale=True,add_leaf_bones=False,axis_forward='-Y',axis_up='Z')
 report.append(dict(name=obj.name,triangles=tris,boundary_edges=boundary,nonmanifold_edges=nonmanifold,volume_m3=volume,dimensions_m=list(obj.dimensions),top_z_m=max(v.co.z for v in obj.data.vertices)))
 obj.select_set(False);objects.append(obj)
 # Presentation offset only; exported FBX above uses the source origin.
 obj.location.y=index*1.8

bpy.ops.object.camera_add(location=(11,-13,8))
camera=bpy.context.object;camera.rotation_euler=(Vector((0,1.8,-.5))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=16;scene.camera=camera
for position,power,size in [((0,-4,8),2200,8),((-5,7,5),1600,7)]:
 bpy.ops.object.light_add(type='AREA',location=position);light=bpy.context.object;light.data.energy=power;light.data.shape='DISK';light.data.size=size;light.rotation_euler=(Vector((0,1.8,0))-light.location).to_track_quat('-Z','Y').to_euler()
scene.world.color=(.15,.15,.15)
scene.render.engine='CYCLES';scene.cycles.samples=32
scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100
scene.render.filepath=str(OUT/'Preview.png')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'ClosedLedge.blend'))
(OUT/'audit.json').write_text(json.dumps(report,indent=2))
bpy.ops.render.render(write_still=True)
