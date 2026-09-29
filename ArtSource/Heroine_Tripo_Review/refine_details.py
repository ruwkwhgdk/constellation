import bpy,bmesh,math,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;O=R/'Refined';O.mkdir(exist_ok=True)
(O/'renders').mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'Corrected/Heroine_Tripo_Corrected.blend'))
bpy.context.preferences.filepaths.save_version=0
body=bpy.data.objects['Heroine_Tripo_Corrected'];body.name='Heroine_Refined'
def mat(name,col,rough=.65):
 m=bpy.data.materials.new(name);m.diffuse_color=(*col,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Roughness'].default_value=rough;p.inputs['Specular IOR Level'].default_value=.23;return m
white=mat('Eye_Sclera',(.63,.52,.48));rim=mat('Lower_Lid',(.20,.075,.075));iris=mat('Ruby_Iris',(.16,.025,.04),.45)
def mesh(name,vs,fs,m):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);me.materials.append(m)
 for p in me.polygons:p.use_smooth=True
 uv=me.uv_layers.new(name='UVMap')
 for p in me.polygons:
  for li in p.loop_indices:
   v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=((v.x+.06)/.12,(v.z-.88)/.04)
 return ob
def tube(name,pts,radii,m):
 vs=[];fs=[]
 for i,p in enumerate(pts):
  tangent=(Vector(pts[min(i+1,len(pts)-1)])-Vector(pts[max(0,i-1)])).normalized();a=tangent.cross(Vector((0,1,0))).normalized();b=tangent.cross(a).normalized()
  for j in range(8):vs.append(Vector(p)+radii[i]*(a*math.cos(j*math.tau/8)+b*math.sin(j*math.tau/8)))
 for i in range(len(pts)-1):
  for j in range(8):a=i*8+j;b=i*8+(j+1)%8;fs.append((a,b,b+8,a+8))
 fs.extend([tuple(reversed(range(8))),tuple((len(pts)-1)*8+j for j in range(8))]);return mesh(name,vs,fs,m)
import numpy as np
n=512;yy,xx=np.mgrid[0:n,0:n];u=(xx+.5)/n*2-1;v=(yy+.5)/n*2-1;r=np.sqrt(u*u+v*v);a=np.arctan2(v,u)
light=np.clip((1-v)*.5,0,1);fiber=(np.sin(a*71+r*19)+np.sin(a*113-r*27))*.018
col=np.zeros((n,n,4),dtype=np.float32);col[:,:,:3]=np.stack([.24+.38*light+fiber,.045+.10*light+fiber*.2,.065+.10*light+fiber*.3],axis=-1)
edge=np.clip((r-.79)/.19,0,1);col[:,:,:3]*=(1-edge[:,:,None]*.84)
pupil=np.clip((r-.25)/.085,0,1);col[:,:,:3]=col[:,:,:3]*pupil[:,:,None]+np.array([.014,.007,.015])*(1-pupil[:,:,None])
shade=np.clip((v-.12)*.65,0,.6);col[:,:,:3]*=1-shade[:,:,None]
for cx,cy,rx,ry in [(-.30,.43,.13,.17),(.29,-.37,.045,.06)]:
 h=np.clip((1-((u-cx)/rx)**2-((v-cy)/ry)**2)*9,0,1);col[:,:,:3]=col[:,:,:3]*(1-h[:,:,None])+np.array([.9,.83,.8])*h[:,:,None]
col[:,:,3]=1
im=bpy.data.images.new('T_Ruby_Iris_Refined',n,n);im.pixels.foreach_set(col.ravel());im.filepath_raw=str(O/'T_Ruby_Iris_Refined.png');im.file_format='PNG';im.save();im.pack()
t=iris.node_tree.nodes.new('ShaderNodeTexImage');t.image=im;iris.node_tree.links.new(t.outputs['Color'],iris.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
skintris=[];skuv=[]
for p in body.data.polygons:
 if body.data.materials[p.material_index].name!='M_Skin':continue
 for j in range(1,len(p.vertices)-1):
  ls=[p.loop_indices[k] for k in [0,j,j+1]]
  skintris.append([body.data.vertices[body.data.loops[l].vertex_index].co.copy() for l in ls]);skuv.append([Vector((*body.data.uv_layers.active.data[l].uv,0)) for l in ls])
bvh=BVHTree.FromPolygons([v for tr in skintris for v in tr],[(i*3,i*3+1,i*3+2) for i in range(len(skintris))],all_triangles=True)
# A continuous scleral patch and tapered lower lid bridge the generated eye gap.
for side in [-1,1]:
 vs=[];fs=[];N=48;K=12
 for i in range(N+1):
  t=i/N;x=.047-.033*t;baseline=.900-.002*t
  lo=baseline-.012*math.sin(math.pi*t)**.8;hi=baseline+.004*math.sin(math.pi*t)
  for j in range(K+1):
   v=j/K;z=lo+(hi-lo)*v;y=-.046-.006*v-.003*math.sin(math.pi*t)*math.sin(math.pi*v)
   vs.append((side*x,y,z))
 for i in range(N):
  for j in range(K):a=i*(K+1)+j;fs.append((a,a+1,a+K+2,a+K+1))
 mesh('Sclera_'+str(side),vs,fs,white)
 pts=[];rs=[]
 for i in range(49):
  t=i/48;x=.047-.033*t;z=.900-.002*t-.012*math.sin(math.pi*t)**.8
  pts.append((side*x,-.0463,z));rs.append(.00008+.00016*math.sin(math.pi*t)**.7)
 tube('Lower_Eyelid_'+str(side),pts,rs,rim)
 # A narrow skin transition closes the lower socket seam against the cheek.
 band=[];banduv=[];bf=[]
 for i in range(49):
  t=i/48;x=side*(.047-.033*t);z=.900-.002*t-.012*math.sin(math.pi*t)**.8
  dz=.0028*math.sin(math.pi*t)**.5+.0001
  hit,normal,idx,dist=bvh.ray_cast(Vector((x,-1,z-dz)),Vector((0,1,0)))
  if hit is None:hit=Vector((x,-.043,z-dz));idx=0
  uv=barycentric_transform(hit,*skintris[idx],*skuv[idx]).to_2d()
  for k in range(4):
   v=k/3;y=(-.0461)*(1-v)+hit.y*v;band.append((x,y,z-dz*v));banduv.append(uv)
 for i in range(48):
  for k in range(3):a=i*4+k;bf.append((a,a+1,a+5,a+4))
 ob=mesh('Lower_Lid_Skin_'+str(side),band,bf,body.data.materials['M_Skin'])
 for p in ob.data.polygons:
  for l in p.loop_indices:ob.data.uv_layers.active.data[l].uv=banduv[len(banduv)//2]
 # Continuous ruby iris with a clean limbal edge, matching the reference hue.
 vs=[];fs=[];uvcoords=[];nr=12;ns=64
 for r in range(nr+1):
  rho=max(.0001,r/nr)
  for j in range(ns):
   a=j*math.tau/ns;x=side*(.027+.0065*rho*math.cos(a));z=.896+.008*rho*math.sin(a)
   t=(.047-abs(x))/.033;base=.900-.002*t;lo=base-.012*math.sin(math.pi*t)**.8;hi=base+.004*math.sin(math.pi*t)
   v=max(0,min(1,(z-lo)/(hi-lo)));y=-.046-.006*v-.003*math.sin(math.pi*t)*math.sin(math.pi*v)-.00025
   vs.append((x,y,z));uvcoords.append((.5+.5*rho*math.cos(a),.5+.5*rho*math.sin(a)))
 for r in range(nr):
  for j in range(ns):a=r*ns+j;b=r*ns+(j+1)%ns;fs.append((a,b,b+ns,a+ns))
 ob=mesh('Iris_Surface_'+str(side),vs,fs,iris)
 for p in ob.data.polygons:
  for li in p.loop_indices:ob.data.uv_layers.active.data[li].uv=uvcoords[ob.data.loops[li].vertex_index]
# Relax tiny generated surface ripples on the shoe and hand interiors, keeping boundaries.
bm=bmesh.new();bm.from_mesh(body.data);changes=0
bmesh.ops.delete(bm,geom=[f for f in bm.faces if body.data.materials[f.material_index].name=='M_Eyes'],context='FACES')
for iteration in range(3):
 updates=[]
 for v in bm.verts:
  x,y,z=v.co
  region=(z<.055) or (abs(x)>.368 and .74<z<.83) or (any(body.data.materials[f.material_index].name=='M_Hair' for f in v.link_faces) and z<.867)
  if region and not v.is_boundary and all(e.is_manifold for e in v.link_edges):
   avg=sum((e.other_vert(v).co for e in v.link_edges),Vector())/len(v.link_edges);d=(avg-v.co)*.16
   if d.length>.0003:d=d.normalized()*.0003
   updates.append((v,v.co+d))
 for v,p in updates:v.co=p
 changes+=len(updates)
bm.to_mesh(body.data);bm.free()
sc=bpy.context.scene;sc.cycles.samples=32;cam=sc.camera
def render(name,loc,target,scale,res):
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.resolution_x,sc.render.resolution_y=res;sc.render.filepath=str(O/'renders'/f'{name}.png');bpy.ops.render.render(write_still=True)
render('eye',(-.034,-3,.9),(-.034,0,.9),.085,(1000,800))
render('face',(0,-3,.862),(0,0,.862),.30,(1100,1100))
render('angle',(-1,-3,.862),(0,0,.862),.30,(1100,1100))
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Heroine_Refined.blend'))
print('REFINED',changes)
