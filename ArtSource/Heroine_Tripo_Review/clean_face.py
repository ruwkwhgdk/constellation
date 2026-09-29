"""Rebuild eye sockets with stitched skin topology; eliminate generated floating eyelid fragments."""
import bpy,bmesh,math,json
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parent;O=R/'FaceClean';O.mkdir(exist_ok=True);(O/'renders').mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'Refined/Heroine_Refined.blend'))
bpy.context.preferences.filepaths.save_version=0
body=bpy.data.objects['Heroine_Refined'];body.name='Heroine_FaceClean'
# Preserve imported corner normals on all untouched geometry.
source_normals={}
for poly in body.data.polygons:
 for loop in poly.loop_indices:
  vertex=body.data.vertices[body.data.loops[loop].vertex_index];key=tuple(round(c,8) for c in vertex.co);source_normals.setdefault(key,[]).append(body.data.corner_normals[loop].vector.copy())
source_normals={k:sum(v,Vector()).normalized() for k,v in source_normals.items()}
for ob in list(bpy.context.scene.objects):
 if ob.type=='MESH' and ob!=body and ob.name!='Heroine_Pearl_Bracelet':bpy.data.objects.remove(ob,do_unlink=True)
def mat(name,col,rough=.7):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Roughness'].default_value=rough;p.inputs['Specular IOR Level'].default_value=.23;return m
hair=body.data.materials['M_Hair'];hp=hair.node_tree.nodes.get('Principled BSDF')
for link in list(hp.inputs['Base Color'].links):hair.node_tree.links.remove(link)
hp.inputs['Base Color'].default_value=(.013,.010,.020,1);hp.inputs['Roughness'].default_value=.56
skin=mat('Face_Skin_Clean',(.56,.405,.35),.74)
lash=mat('Lash_Clean',(.023,.008,.013),.76);lower=mat('Lid_Waterline',(.27,.11,.10),.76)
white=mat('Sclera_Clean',(.68,.60,.55),.51)
iris=bpy.data.materials['Ruby_Iris'];brow=mat('Brow_Clean',(.055,.026,.035),.81)
for m in [skin,lash,lower]:body.data.materials.append(m)
si=body.data.materials.find(skin.name);li=body.data.materials.find(lash.name);lli=body.data.materials.find(lower.name)
bm=bmesh.new();bm.from_mesh(body.data);bm.verts.ensure_lookup_table();uvlayer=bm.loops.layers.uv.active
seen=set();comps=[]
for v in bm.verts:
 if v in seen:continue
 stack=[v];seen.add(v);vs=[];fs=set()
 while stack:
  a=stack.pop();vs.append(a);fs.update(a.link_faces)
  for e in a.link_edges:
   b=e.other_vert(a)
   if b not in seen:seen.add(b);stack.append(b)
 comps.append((vs,fs))
comps.sort(key=lambda p:-len(p[0]));headvs,headfs=comps[2]
# Remove separate generated eyebrow/lash fragments instead of covering them.
bad=[f for vs,fs in comps for f in fs if len(vs)<100 and min(v.co.z for v in vs)>.88 and max(v.co.z for v in vs)<.93]
bmesh.ops.delete(bm,geom=bad,context='FACES')
headfs=[f for f in headfs if f.is_valid];headvs=[v for v in headvs if v.is_valid]
# Use a clean skin material for the head: its old atlas contains painted duplicate eyelids.
for f in headfs:f.material_index=si
report={'removed_floating_faces':len(bad),'sockets':[]}
inners={};rim_vertices=set()
for side in [-1,1]:
 # Delete the damaged socket, upper lid and brow together, preserving the perimeter.
 cut=[f for f in headfs if f.is_valid and .007<side*f.calc_center_median().x<.056 and .879<f.calc_center_median().z<.928 and f.calc_center_median().y<-.024]
 cutset=set(cut);edges=[e for f in cut for e in f.edges if any(g not in cutset for g in e.link_faces)]
 edges=set(edges)
 bmesh.ops.delete(bm,geom=cut,context='FACES_ONLY')
 wires=[e for e in bm.edges if not e.link_faces]
 if wires:bmesh.ops.delete(bm,geom=wires,context='EDGES')
 bmesh.ops.subdivide_edges(bm,edges=list(edges),cuts=2,use_grid_fill=False)
 # Follow the actual boundary cycle; angle sorting would tear concave perimeter sections.
 boundary=[e for e in bm.edges if e.is_boundary and e.link_faces[0].material_index==si and all(.001<side*v.co.x<.061 and .873<v.co.z<.935 and v.co.y<-.012 for v in e.verts)]
 adj={}
 for e in boundary:
  for v in e.verts:adj.setdefault(v,[]).append(e.other_vert(v))
 start=max(adj,key=lambda v:side*v.co.x);perim=[start];prev=None;cur=start
 while True:
  ns=[v for v in adj[cur] if v!=prev]
  if not ns:break
  nxt=ns[0]
  if nxt==start:break
  if nxt in perim:raise RuntimeError('Socket boundary is not a simple cycle')
  perim.append(nxt);prev,cur=cur,nxt
 n=len(perim)
 area=sum(side*perim[i].co.x*perim[(i+1)%n].co.z-side*perim[(i+1)%n].co.x*perim[i].co.z for i in range(n))
 if area<0:perim=list(reversed(perim))
 cx=side*.0305;cz=.8985
 first=math.atan2((perim[0].co.z-cz)/.020,(side*perim[0].co.x-.0305)/.024)
 distances=[0]
 for i in range(n):
  delta=perim[(i+1)%n].co-perim[i].co;distances.append(distances[-1]+math.hypot(delta.x/.024,delta.z/.020))
 angles={v:first+math.tau*distances[i]/distances[-1] for i,v in enumerate(perim)}
 def angle(v):return angles[v]
 # Quadratic depth estimate from the untouched perimeter sets socket projection.
 A=np.array([[1,side*v.co.x-.0305,v.co.z-cz,(side*v.co.x-.0305)**2,(v.co.z-cz)**2,(side*v.co.x-.0305)*(v.co.z-cz)] for v in perim]);Y=np.array([v.co.y for v in perim]);coeff=np.linalg.lstsq(A,Y,rcond=None)[0];linearcoeff=np.linalg.lstsq(A[:,:3],Y,rcond=None)[0]
 def depth(x,z):
  x=side*x-.0305;z=z-cz;return float(np.dot(coeff,[1,x,z,x*x,z*z,x*z]))
 def inner(a):
  x=side*(.0305+.0165*math.cos(a));z=.8985+.001*math.cos(a)+(.0055 if math.sin(a)>=0 else .0115)*math.sin(a)
  # Clean edge follows the fitted facial surface, slightly recessed into the socket.
  y=float(np.dot(linearcoeff,[1,side*x-.0305,z-cz]))+.0004
  return Vector((x,y,z))
 steps=[0,.015,.05,.13,.25,.42,.62,.82,1];rings=[]
 for j,t in enumerate(steps):
  if j==len(steps)-1:rings.append(perim);continue
  ring=[]
  for ov in perim:
   a=angle(ov);iv=inner(a);pos=iv.lerp(ov.co,t)
   # Follow fitted facial curvature, corrected to meet exact original perimeter depth.
   fit=depth(pos.x,pos.z);outererr=ov.co.y-depth(ov.co.x,ov.co.z)
   plane=float(np.dot(linearcoeff,[1,side*pos.x-.0305,pos.z-cz]));pos.y=fit+(plane-fit+.0004)*(1-t)**2+outererr*t*t*(3-2*t)
   ring.append(bm.verts.new(pos))
  rings.append(ring)
 for j in range(len(rings)-1):
  for k in range(n):
   kn=(k+1)%n;f=bm.faces.new((rings[j][k],rings[j][kn],rings[j+1][kn],rings[j+1][k]));f.material_index=si
   amid=angle(perim[k]);upper=math.sin(amid)>0
   if j==0:f.material_index=li if upper else lli
   if j==1 and upper:f.material_index=li
   f.normal_update()
   if f.normal.y>0:f.normal_flip()
   for l in f.loops:l[uvlayer].uv=(.5,.5)
 rim_vertices.update(rings[0]);rim_vertices.update(rings[1])
 inners[side]=[(angle(v),inner(angle(v))) for v in perim]
 report['sockets'].append({'side':side,'removed_faces':len(cut),'perimeter_vertices':n,'depth_range':[min(p.y for a,p in inners[side]),max(p.y for a,p in inners[side])]})
# Explicit triangulation prevents nonplanar perimeter n-gons from shading as diagonal creases.
head_faces=[f for f in bm.faces if f.material_index in [si,li,lli]]
bmesh.ops.triangulate(bm,faces=head_faces,quad_method='BEAUTY',ngon_method='BEAUTY')
# Retriangulate the narrow concave cheek transition where the generated source folds over itself.
for side in [-1,1]:
 repair=[f for f in bm.faces if f.material_index==si and .016<side*f.calc_center_median().x<.034 and .873<f.calc_center_median().z<.886 and f.calc_center_median().y<-.012 and not any(v in rim_vertices for v in f.verts)]
 repairset=set(repair);border=set(e for f in repair for e in f.edges if any(g not in repairset for g in e.link_faces))
 bmesh.ops.delete(bm,geom=repair,context='FACES_ONLY')
 wires=[e for e in bm.edges if not e.link_faces]
 if wires:bmesh.ops.delete(bm,geom=wires,context='EDGES')
 caps=bmesh.ops.holes_fill(bm,edges=[e for e in border if e.is_valid and e.is_boundary],sides=0)['faces']
 for f in caps:
  f.material_index=si;f.normal_update()
  if f.normal.y>0:f.normal_flip()
  for l in f.loops:l[uvlayer].uv=(.5,.5)
 bmesh.ops.triangulate(bm,faces=caps)
# Blend socket/perimeter curvature on the connected skin, fixing the seam itself.
for it in range(65):
 updates=[]
 for v in bm.verts:
  if v in rim_vertices or not v.link_faces or not all(f.material_index in [si,li,lli] for f in v.link_faces):continue
  x,y,z=v.co
  if not (.872<z<.939 and .004<abs(x)<.061 and y<-.013):continue
  neighbors=[e.other_vert(v) for e in v.link_edges if e.link_faces]
  if not neighbors:continue
  # Inverse edge length weights preserve the original projected facial proportions.
  weights=[1/max((a.co-v.co).length,1e-5) for a in neighbors]
  avg=sum(a.co.y*w for a,w in zip(neighbors,weights))/sum(weights)
  fade=min(1,(z-.872)/.006,(.939-z)/.006,(abs(x)-.004)/.004,(.061-abs(x))/.004)
  updates.append((v,y+(avg-y)*.4*fade))
 for v,y in updates:v.co.y=y
# Spatial quadratic fitting removes an irregular triangulation's diagonal shading ridge.
sv=[v for v in bm.verts if v.link_faces and all(f.material_index in [si,li,lli] for f in v.link_faces) and v.co.y<-.01 and .865<v.co.z<.947]
xyz=np.array([list(v.co) for v in sv]);updates=[]
for i,v in enumerate(sv):
 if v in rim_vertices:continue
 x,y,z=v.co
 if not (.871<z<.940 and .005<abs(x)<.061):continue
 d=xyz[:,[0,2]]-np.array([x,z]);ds=(d*d).sum(axis=1);ids=ds<.014**2
 if ids.sum()<10:continue
 dd=d[ids];w=np.exp(-ds[ids]/(.006**2));A=np.column_stack([np.ones(len(dd)),dd[:,0],dd[:,1],dd[:,0]**2,dd[:,1]**2,dd[:,0]*dd[:,1]])
 c=np.linalg.lstsq(A*np.sqrt(w[:,None]),xyz[ids,1]*np.sqrt(w),rcond=None)[0]
 fade=max(0,min(1,(z-.871)/.005,(.940-z)/.005,(abs(x)-.005)/.005,(.061-abs(x))/.005))
 updates.append((v,y+(float(c[0])-y)*fade))
for v,y in updates:v.co.y=y
# Refresh socket rim after skin relaxation.
for side in inners:
 pass
# Relax the old clip embossing within the hair, preserving strand outlines.
for it in range(16):
 updates=[]
 for v in bm.verts:
  x,y,z=v.co
  if -.064<x<-.033 and .912<z<.958 and y<-.045 and not v.is_boundary and all(body.data.materials[f.material_index].name=='M_Hair' for f in v.link_faces):
   avg=sum(e.other_vert(v).co.y for e in v.link_edges)/len(v.link_edges);updates.append((v,y+(avg-y)*.3))
 for v,y in updates:v.co.y=y
# Smooth forehead residual relief outside the removed patch, retaining facial features.
for it in range(3):
 updates=[]
 for v in headvs:
  if v.is_valid and v.link_faces and v.co.y<-.025 and v.co.z>.926 and v.co.z<.95 and abs(v.co.x)<.055 and not v.is_boundary:
   avg=sum((e.other_vert(v).co for e in v.link_edges),Vector())/len(v.link_edges);updates.append((v,v.co.lerp(avg,.16)))
 for v,p in updates:v.co=p
loose=[v for v in bm.verts if not v.link_faces]
if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
bm.normal_update()
bm.to_mesh(body.data);bm.free()
for p in body.data.polygons:p.use_smooth=True
# Continuous fitted skin normals avoid isolated highlights on thin transition triangles.
body.data.update()
ids={vi for p in body.data.polygons if p.material_index==si for vi in p.vertices}
ids=[i for i in ids if body.data.vertices[i].co.y<-.01 and .865<body.data.vertices[i].co.z<.947]
coords=np.array([list(body.data.vertices[i].co) for i in ids]);normals=[source_normals.get(tuple(round(c,8) for c in v.co),v.normal.copy()) for v in body.data.vertices]
for vi in ids:
 v=body.data.vertices[vi];x,y,z=v.co
 if not (.871<z<.940 and .005<abs(x)<.061):continue
 d=coords[:,[0,2]]-np.array([x,z]);ds=(d*d).sum(axis=1);sel=ds<.012**2
 if sel.sum()<10:continue
 dd=d[sel];w=np.exp(-ds[sel]/(.005**2));A=np.column_stack([np.ones(len(dd)),dd[:,0],dd[:,1],dd[:,0]**2,dd[:,1]**2,dd[:,0]*dd[:,1]])
 c=np.linalg.lstsq(A*np.sqrt(w[:,None]),coords[sel,1]*np.sqrt(w),rcond=None)[0]
 target=Vector((float(c[1]),-1,float(c[2]))).normalized();fade=max(0,min(1,(z-.871)/.005,(.940-z)/.005,(abs(x)-.005)/.005,(.061-abs(x))/.005));normals[vi]=normals[vi].lerp(target,fade).normalized()
body.data.normals_split_custom_set_from_vertices(normals)
def mesh(name,vs,fs,m,uvs=None):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);me.materials.append(m)
 uv=me.uv_layers.new(name='UVMap')
 for p in me.polygons:
  p.use_smooth=True
  for l in p.loop_indices:uv.data[l].uv=uvs[me.loops[l].vertex_index] if uvs else (.5,.5)
 bm=bmesh.new();bm.from_mesh(me);bm.normal_update()
 for f in bm.faces:
  if f.normal.y>0:f.normal_flip()
 bm.to_mesh(me);bm.free();return ob
# Fill each socket with a shallow convex eye surface, sharing the exact rim contour.
for side in [-1,1]:
 ps=inners[side];n=len(ps);center=Vector((side*.0305,0,.8985));B=np.array([[1,p.x,p.z] for a,p in ps]);C=np.linalg.lstsq(B,np.array([p.y for a,p in ps]),rcond=None)[0];center.y=float(np.dot(C,[1,center.x,center.z]))-.003
 vs=[center];uvs=[(.5,.5)];fs=[];nr=10
 for j in range(1,nr+1):
  t=j/nr
  for a,p in ps:
   q=center.lerp(p,t);q.y=float(np.dot(C,[1,q.x,q.z]))-.003*(1-t*t);vs.append(q);uvs.append((.5+.5*t*math.cos(a),.5+.5*t*math.sin(a)))
 for k in range(n):fs.append((0,1+k,1+(k+1)%n))
 for j in range(nr-1):
  for k in range(n):a=1+j*n+k;b=1+j*n+(k+1)%n;fs.append((a,b,b+n,a+n))
 scl=mesh('Eye_Surface_'+str(side),vs,fs,white,uvs)
 temp=bmesh.new();temp.from_mesh(scl.data);bmesh.ops.triangulate(temp,faces=list(temp.faces));temp.to_mesh(scl.data);temp.free()
 # Project the iris onto the eye's own surface so there is no thick disk seam.
 tree=BVHTree.FromPolygons([v.co for v in scl.data.vertices],[tuple(p.vertices) for p in scl.data.polygons])
 vs=[];uvs=[];fs=[];nseg=64;nr=12
 for j in range(nr+1):
  t=max(.00001,j/nr)
  for k in range(nseg):
   a=k*math.tau/nseg;x=side*(.027+.0065*t*math.cos(a));z=.8958+.0079*t*math.sin(a)
   cosine=max(-1,min(1,(abs(x)-.0305)/.0165));top=.8985+.001*cosine+.0055*math.sqrt(max(0,1-cosine*cosine));z=min(z,top-.00018)
   hit,normal,idx,dist=tree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
   y=hit.y-.00018 if hit else center.y+.0005
   vs.append((x,y,z));uvs.append((.5+.5*t*math.cos(a),.5+.5*t*math.sin(a)))
 for j in range(nr):
  for k in range(nseg):a=j*nseg+k;b=j*nseg+(k+1)%nseg;fs.append((a,b,b+nseg,a+nseg))
 mesh('Iris_Clean_'+str(side),vs,fs,iris,uvs)
# Thin eyebrows follow the new forehead surface and taper at both ends.
skinpolys=[tuple(p.vertices) for p in body.data.polygons if p.material_index==si]
tree=BVHTree.FromPolygons([v.co for v in body.data.vertices],skinpolys)
for side in [-1,1]:
 vs=[];fs=[]
 for i in range(49):
  t=i/48;x=side*(.046-.031*t);z=.918+.002*math.sin(math.pi*t)-.001*t;w=.00003+.00065*math.sin(math.pi*t)**.6
  for s in [-1,1]:
   zz=z+s*w;hit,normal,idx,dist=tree.ray_cast(Vector((x,-1,zz)),Vector((0,1,0)));y=hit.y-.00010 if hit else -.051
   vs.append((x,y,zz))
  if i:fs.append(((i-1)*2,(i-1)*2+1,i*2+1,i*2))
 mesh('Eyebrow_'+str(side),vs,fs,brow)
# Replace painted/blurred clips with smooth geometric pins resting on the hair.
hairpolys=[tuple(p.vertices) for p in body.data.polygons if body.data.materials[p.material_index].name=='M_Hair']
htree=BVHTree.FromPolygons([v.co for v in body.data.vertices],hairpolys)
for name,a,b,col in [('Purple',(-.054,.946),(-.038,.931),(.22,.09,.34)),('Silver',(-.057,.940),(-.041,.925),(.57,.52,.64))]:
 pts=[]
 for i in range(17):
  t=i/16;x=a[0]*(1-t)+b[0]*t;z=a[1]*(1-t)+b[1]*t;hit,normal,idx,dist=htree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)));pts.append(Vector((x,(hit.y if hit else -.075)-.0007,z)))

 # A rigid pin bridges hair grooves; do not conform it to jagged source ridges.
 pin_y=min(p.y for p in pts)-.00015
 for point in pts:point.y=pin_y
 vs=[];fs=[];rr=.00085
 for i,p in enumerate(pts):
  tangent=(pts[min(i+1,16)]-pts[max(i-1,0)]).normalized();axis=tangent.cross(Vector((0,1,0))).normalized();normal=tangent.cross(axis).normalized()
  for j in range(8):vs.append(p+rr*(axis*math.cos(j*math.tau/8)+normal*.38*math.sin(j*math.tau/8)))
 for i in range(16):
  for j in range(8):a=i*8+j;b=i*8+(j+1)%8;fs.append((a,b,b+8,a+8))
 fs.extend([tuple(reversed(range(8))),tuple(16*8+j for j in range(8))]);mesh('Hairpin_'+name,vs,fs,mat('Pin_'+name,col,.38))
sc=bpy.context.scene;sc.cycles.samples=32;cam=sc.camera
def render(name,loc,target,scale,res=(1100,1100),clay=False):
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.resolution_x,sc.render.resolution_y=res;sc.render.filepath=str(O/'renders'/f'{name}.png')
 sc.view_layers[0].material_override=bpy.data.materials.get('Clay_Check') if clay else None;bpy.ops.render.render(write_still=True)
mat('Clay_Check',(.35,.35,.35),.8)
(O/'construction.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Heroine_FaceClean.blend'))
render('eye',(-.034,-3,.902),(-.034,0,.902),.10)
render('eye_clay',(-.034,-3,.902),(-.034,0,.902),.10,clay=True)
print('FACE_CLEAN',json.dumps(report))
