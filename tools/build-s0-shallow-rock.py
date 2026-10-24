"""Shallow fractured wall outcrops, authored at actual depth (metres)."""
import bpy,bmesh,math,json,random
from pathlib import Path
from mathutils import Vector,noise
R=Path(__file__).resolve().parents[1];O=R/'ArtSource/SchoolOpening/WetFloor/ShallowRock'
O.mkdir(parents=True,exist_ok=True)
assert not (O/'ShallowRock.blend').exists()
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC'
mat=bpy.data.materials.new('NeutralRockReview');mat.diffuse_color=(.18,.21,.22,1);mat.use_nodes=True
bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.18,.21,.22,1);bs.inputs['Roughness'].default_value=.85
report=[]
for k,(width,height) in enumerate([(14.8,11.5),(13.3,8)]):
 rng=random.Random(924+k);nx=32;nz=24;verts=[];faces=[]
 for row in range(nz+1):
  v=row/nz
  for col in range(nx+1):
   t=col/nx
   xx=(t-.5)*width
   if 0<col<nx:xx+=rng.uniform(-.12,.12)
   top=height*(.70+.18*math.sin(t*3.7+k*.8)+.08*math.sin(t*13+k))
   z=v*top
   if 0<row<nz:z+=rng.uniform(-.10,.10)
   x=xx+(v*.35)*math.sin(v*7+k)
   # Nonperiodic diagonal fractures, no horizontal stepped shelves.
   broad=noise.noise_vector(Vector((x*.39,z*.39,k+4)))
   fine=noise.noise_vector(Vector((x*1.8,z*1.8,k+7)))
   fissure=math.exp(-((x*.33-z*.18+.5*math.sin(z*.7+k))%1.7-.85)**2/.012)
   depth=.55+.32*broad.x+.12*fine.y-.24*fissure
   edge=min(t*8,(1-t)*8,1)
   y=-.10-max(.08,depth)*max(.25,edge)
   verts.append((x,y,z))
 for row in range(nz):
  for col in range(nx):
   a=row*(nx+1)+col;b=a+1;c=a+nx+2;d=a+nx+1
   if (row+col)%2:faces.extend([(a,b,d),(b,c,d)])
   else:faces.extend([(a,b,c),(a,c,d)])
 # Matching rear perimeter closes the mesh without covering front details.
 boundary=list(range(nx+1))+[r*(nx+1)+nx for r in range(1,nz+1)]+[nz*(nx+1)+c for c in range(nx-1,-1,-1)]+[r*(nx+1) for r in range(nz-1,0,-1)]
 rear=[]
 for idx in boundary:
  x,y,z=verts[idx];rear.append(len(verts));verts.append((x,.45,z))
 for i,a in enumerate(boundary):j=(i+1)%len(boundary);faces.append((a,boundary[j],rear[j],rear[i]))
 faces.append(tuple(reversed(rear)))
 mesh=bpy.data.meshes.new('FracturedWall');mesh.from_pydata(verts,[],faces);mesh.update()
 obj=bpy.data.objects.new('SM_S0_ShallowRock_'+str(k),mesh);scene.collection.objects.link(obj);bpy.context.view_layer.objects.active=obj;obj.select_set(True)
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(mesh);bm.free()
 # Actual metre texel scale, per-face dominant-plane UVs; no packed-island stretching.
 uv=mesh.uv_layers.new(name='RockMetres')
 for poly in mesh.polygons:
  axis=max(range(3),key=lambda i:abs(poly.normal[i]))
  for li in poly.loop_indices:
   p=mesh.vertices[mesh.loops[li].vertex_index].co
   uv.data[li].uv=(p.y,p.z) if axis==0 else ((p.x,p.z) if axis==1 else (p.x,p.y))
  poly.use_smooth=True
 mesh.materials.append(mat)
 bm=bmesh.new();bm.from_mesh(mesh);mesh.calc_loop_triangles()
 row=dict(name=obj.name,triangles=len(mesh.loop_triangles),boundary_edges=sum(e.is_boundary for e in bm.edges),nonmanifold_edges=sum(not e.is_manifold for e in bm.edges),volume=bm.calc_volume(signed=True),dimensions_m=list(obj.dimensions),uv_layers=len(mesh.uv_layers))
 bm.free();assert row['boundary_edges']==row['nonmanifold_edges']==0 and row['volume']>0
 bpy.ops.export_scene.fbx(filepath=str(O/(obj.name+'.fbx')),use_selection=True,object_types={'MESH'},apply_unit_scale=True,add_leaf_bones=False,axis_forward='-Y',axis_up='Z')
 report.append(row);obj.select_set(False);obj.location.x=(k-.5)*16
bpy.ops.object.camera_add(location=(19,-35,18));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,5))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=36;scene.camera=cam
for pos,power,size in [((-10,-9,20),5500,10),((15,-5,12),3500,8)]:
 bpy.ops.object.light_add(type='AREA',location=pos);a=bpy.context.object;a.data.energy=power;a.data.size=size;a.rotation_euler=(Vector((0,0,4))-a.location).to_track_quat('-Z','Y').to_euler()
scene.world.color=(.15,.15,.15);scene.render.engine='CYCLES';scene.cycles.samples=32
scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100;scene.render.filepath=str(O/'Preview.png')
bpy.ops.wm.save_as_mainfile(filepath=str(O/'ShallowRock.blend'));(O/'audit.json').write_text(json.dumps(report,indent=2));bpy.ops.render.render(write_still=True)
