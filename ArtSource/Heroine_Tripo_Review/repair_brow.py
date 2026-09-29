import bpy,bmesh,math,json
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform,delaunay_2d_cdt
R=Path(__file__).resolve().parent;O=R/'ContourRepair';(O/'textures').mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'BoundaryLocal/Heroine_BoundaryLocal.blend'))
bpy.context.preferences.filepaths.save_version=0
body=bpy.data.objects['Heroine_BoundaryLocal'];body.name='Heroine_ContourRepair';me=body.data
oldnorm=[n.vector.copy() for n in me.corner_normals]
normdict={tuple(round(c,8) for c in me.vertices[l.vertex_index].co):oldnorm[i] for i,l in enumerate(me.loops)}
d=json.loads((O/'diagnostics/mesh.json').read_text());cs=d['components']
skin=me.materials['M_Skin'];tex=next(n.image for n in skin.node_tree.nodes if n.type=='TEX_IMAGE');pix=np.array(tex.pixels[:],dtype=np.float32).reshape(tex.size[1],tex.size[0],4)
me.calc_loop_triangles();tris=[t for t in me.loop_triangles if cs[t.vertices[0]]==14];verts=[v.co.copy() for v in me.vertices]
tree=BVHTree.FromPolygons(verts,[t.vertices[:] for t in tris],all_triangles=True)
uvs=[[Vector((*me.uv_layers.active.data[l].uv,0)) for l in t.loops] for t in tris]
def sample(x,z):
 hit,n,i,dist=tree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
 if hit is None:return np.array([.72,.62,.58,1])
 uv=barycentric_transform(hit,*(verts[j] for j in tris[i].vertices),*uvs[i]);u=float(uv.x)*tex.size[0]-.5;v=float(uv.y)*tex.size[1]-.5;a=math.floor(u);b=math.floor(v);fu=u-a;fv=v-b
 return pix[b%tex.size[1],a%tex.size[0]]*(1-fu)*(1-fv)+pix[b%tex.size[1],(a+1)%tex.size[0]]*fu*(1-fv)+pix[(b+1)%tex.size[1],a%tex.size[0]]*(1-fu)*fv+pix[(b+1)%tex.size[1],(a+1)%tex.size[0]]*fu*fv
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();uvl=bm.loops.layers.uv.active
cut=[f for f in bm.faces if cs[f.verts[0].index]==14 and -.054<f.calc_center_median().x<-.009 and .912<f.calc_center_median().z<.929 and f.calc_center_median().y<-.03]
cutset=set(cut);edges=set(e for f in cut for e in f.edges if len(e.link_faces)==1 or any(g not in cutset for g in e.link_faces));adj={}
for e in edges:
 for v in e.verts:adj.setdefault(v,[]).append(e.other_vert(v))
assert all(len(ns)==2 for ns in adj.values()),'Non-simple patch perimeter'
start=next(iter(adj));per=[start];prev=None;cur=start
while True:
 nxt=next(v for v in adj[cur] if v!=prev)
 if nxt==start:break
 assert nxt not in per
 per.append(nxt);prev,cur=cur,nxt
if len(per)!=len(adj):
 rings=[per];seen=set(per)
 while len(seen)<len(adj):
  st=next(v for v in adj if v not in seen);ring=[st];pr=None;cur=st
  while True:
   nxt=next(v for v in adj[cur] if v!=pr)
   if nxt==st:break
   ring.append(nxt);pr,cur=cur,nxt
  seen.update(ring);rings.append(ring)
 print('PATCH_RINGS',[(len(r),[[min(v.co[k] for v in r),max(v.co[k] for v in r)] for k in range(3)]) for r in rings],flush=True)
 per=max(rings,key=lambda r:abs(sum(r[i].co.x*r[(i+1)%len(r)].co.z-r[(i+1)%len(r)].co.x*r[i].co.z for i in range(len(r)))))
bound=np.array([[v.co.x,v.co.z] for v in per]);xmin,zmin=bound.min(axis=0)-.0002;xmax,zmax=bound.max(axis=0)+.0002
def inside(x,z):
 result=False
 for i in range(len(bound)):
  a,b=bound[i],bound[(i+1)%len(bound)]
  if (a[1]>z)!=(b[1]>z) and x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]:result=not result
 return result
cut=list(set(cut)|{f for f in bm.faces if cs[f.verts[0].index]==14 and f.calc_center_median().y<-.025 and inside(f.calc_center_median().x,f.calc_center_median().z)})
# Preserve the existing painted eyebrow by resampling its exact original surface color.
N=768;out=np.ones((N,N,4),np.float32)
for j in range(N):
 z=zmin+(j+.5)/N*(zmax-zmin)
 for i in range(N):out[j,i]=sample(xmin+(i+.5)/N*(xmax-xmin),z)
im=bpy.data.images.new('T_Brow_SurfacePreserved',N,N);im.pixels.foreach_set(out.ravel());im.filepath_raw=str(O/'textures/T_Brow_SurfacePreserved.png');im.file_format='PNG';im.save();im.pack()
mat=skin.copy();mat.name='M_Brow_SurfacePreserved';nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF');t=nt.nodes.new('ShaderNodeTexImage');t.image=im;nt.links.new(t.outputs['Color'],bs.inputs['Base Color']);me.materials.append(mat);mi=len(me.materials)-1
# Reconnect the folded skin strip to its existing perimeter, using a constrained local fill.
coords=[Vector((v.co.x,v.co.z)) for v in per]
for z in np.arange(zmin,zmax,.001):
 for x in np.arange(xmin,xmax,.001):coords.append(Vector((x,z)))
res=delaunay_2d_cdt(coords,[(i,(i+1)%len(per)) for i in range(len(per))],[list(range(len(per)))],1,1e-8)
rv,re,rf,ov,oe,of=res
A=np.array([[1,v.co.x+.03,v.co.z-.921,(v.co.x+.03)**2,(v.co.z-.921)**2,(v.co.x+.03)*(v.co.z-.921)] for v in per]);Y=np.array([v.co.y for v in per]);c=np.linalg.lstsq(A,Y,rcond=None)[0]
def depth(x,z):
 u=x+.03;v=z-.921;return float(np.dot(c,[1,u,v,u*u,v*v,u*v]))
anchors=[];values=[]
for v in per:
 n=normdict.get(tuple(round(a,8) for a in v.co),Vector((0,-1,0)))
 gx=-n.x/n.y if abs(n.y)>.2 else 0;gz=-n.z/n.y if abs(n.y)>.2 else 0
 for dx,dz in [(0,0),(.0003,0),(-.0003,0),(0,.0003),(0,-.0003)]:
  anchors.append(((v.co.x+dx+.03)/.02,(v.co.z+dz-.921)/.02));values.append(v.co.y+dx*gx+dz*gz)
anchors=np.array(anchors);values=np.array(values)
def kernel(r2):return .5*r2*np.log(np.maximum(r2,1e-16))
r2=((anchors[:,None,:]-anchors[None,:,:])**2).sum(axis=2);K=kernel(r2);P=np.column_stack([np.ones(len(anchors)),anchors]);M=np.block([[K+np.eye(len(K))*1e-10,P],[P.T,np.zeros((3,3))]]);sol=np.linalg.solve(M,np.r_[values,np.zeros(3)])
def corrected_depth(x,z):
 p=np.array([(x+.03)/.02,(z-.921)/.02]);return float(kernel(((anchors-p)**2).sum(axis=1))@sol[:-3]+np.r_[1,p]@sol[-3:])
bmesh.ops.delete(bm,geom=cut,context='FACES_ONLY');mapping=[];newvs=[]
for p,origids in zip(rv,ov):
 old=next((idx for idx in origids if idx<len(per)),None)
 if old is not None:mapping.append(per[old])
 else:
  v=bm.verts.new((p.x,corrected_depth(p.x,p.y),p.y));mapping.append(v);newvs.append(v)
for face in rf:
 vs=[mapping[i] for i in face];f=bm.faces.new(vs);f.material_index=mi;f.smooth=True;f.normal_update()
 if f.normal.y>0:f.normal_flip()
 for l in f.loops:l[uvl].uv=((l.vert.co.x-xmin)/(xmax-xmin),(l.vert.co.z-zmin)/(zmax-zmin))
loose=[v for v in bm.verts if not v.link_faces]
if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
bm.normal_update();bm.to_mesh(me);bm.free();me.update()
normals=[]
for p in me.polygons:
 for li in p.loop_indices:
  v=me.vertices[me.loops[li].vertex_index]
  if p.material_index==mi:
   eps=.0001;dx=(corrected_depth(v.co.x+eps,v.co.z)-corrected_depth(v.co.x-eps,v.co.z))/(2*eps);dz=(corrected_depth(v.co.x,v.co.z+eps)-corrected_depth(v.co.x,v.co.z-eps))/(2*eps);n=Vector((dx,-1,dz)).normalized()
   old=normdict.get(tuple(round(a,8) for a in v.co))
   if old is not None:n=old
  else:n=normdict.get(tuple(round(a,8) for a in v.co),v.normal.copy())
  normals.append(n)
me.normals_split_custom_set(normals)
(O/'brow_patch.json').write_text(json.dumps({'removed_faces':len(cut),'local_patch_faces':len(rf),'perimeter_vertices':len(per),'bounds':[xmin,xmax,zmin,zmax],'appearance':'Original eyebrow surface color reprojected; no new eyebrow design.'},indent=2))
sc=bpy.context.scene;cam=sc.camera;cam.location=(-.034,-3,.902);cam.rotation_euler=(Vector((-.034,0,.902))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.10;sc.render.resolution_x=sc.render.resolution_y=1100;sc.cycles.samples=24
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Heroine_ContourRepair.blend'))
sc.render.filepath=str(O/'renders/brow.png');bpy.ops.render.render(write_still=True)
