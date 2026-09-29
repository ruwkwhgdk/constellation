import bpy,sys,json
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R));from surface_retouch_utils import Surface
O=R/'DetailFinish2';bpy.ops.wm.open_mainfile(filepath=str(O/'geometry_stage.blend'));bpy.context.preferences.filepaths.save_version=0;ob=bpy.data.objects['Heroine_DetailFinish2'];s=Surface(ob);me=ob.data;cid=json.loads((O/'components.json').read_text())['ids']
original_names=[me.materials[t.material_index].name for t in s.tris];original_uvs=[[Vector((*me.uv_layers.active.data[l].uv,0)) for l in t.loops] for t in s.tris]
curveX=np.array([-.050,-.047,-.043,-.038,-.033,-.028,-.023,-.018,-.015]);curveZ=np.array([.9045,.9055,.9065,.9071,.9072,.9073,.9067,.9053,.9040]);report={};saveduv={}
for component in [14,21]:
 faces=[p for p in me.polygons if cid[p.vertices[0]]==component and -.051<p.center.x<-.014 and .903<p.center.z<.912 and p.center.y<-.035]
 if not faces:continue
 ids={p.index for p in faces};selected=[t for t in s.tris if t.polygon_index in ids];verts=[s.coords[i] for p in faces for i in p.vertices];xmin=min(v.x for v in verts)-.00001;xmax=max(v.x for v in verts)+.00001;zmin=min(v.z for v in verts)-.00001;zmax=max(v.z for v in verts)+.00001;W,H=1024,512;atlas=np.zeros((H,W,4),np.float32);atlas[:,:,3]=1;depth=np.full((H,W),np.inf);coverage=np.zeros((H,W),bool)
 for t in selected:
  name=me.materials[t.material_index].name;im=s.sources[name];src=s.arrays[im.name];p=np.array([s.coords[i][:] for i in t.vertices]);uv=np.array([me.uv_layers.active.data[l].uv[:] for l in t.loops]);proj=(p[:,[0,2]]-[xmin,zmin])/[xmax-xmin,zmax-zmin]*[W,H]-.5;lo=np.maximum(np.floor(proj.min(0)).astype(int),0);hi=np.minimum(np.ceil(proj.max(0)).astype(int),[W-1,H-1]);yy,xx=np.mgrid[lo[1]:hi[1]+1,lo[0]:hi[0]+1];a=proj[1]-proj[0];b=proj[2]-proj[0];det=a[0]*b[1]-a[1]*b[0]
  if abs(det)<1e-9:continue
  dx=xx-proj[0,0];dy=yy-proj[0,1];u=(dx*b[1]-dy*b[0])/det;v=(a[0]*dy-a[1]*dx)/det;valid=(u>=-.002)&(v>=-.002)&(u+v<=1.002);y=p[0,1]+u*(p[1,1]-p[0,1])+v*(p[2,1]-p[0,1]);valid&=y<depth[yy,xx]
  tex=uv[0]+u[:,:,None]*(uv[1]-uv[0])+v[:,:,None]*(uv[2]-uv[0]);tx=tex[:,:,0]*im.size[0]-.5;ty=tex[:,:,1]*im.size[1]-.5;ix=np.floor(tx).astype(int);iy=np.floor(ty).astype(int);fx=(tx-ix)[:,:,None];fy=(ty-iy)[:,:,None];colors=src[iy%im.size[1],ix%im.size[0]]*(1-fx)*(1-fy)+src[iy%im.size[1],(ix+1)%im.size[0]]*fx*(1-fy)+src[(iy+1)%im.size[1],ix%im.size[0]]*(1-fx)*fy+src[(iy+1)%im.size[1],(ix+1)%im.size[0]]*fx*fy
  atlas[yy[valid],xx[valid]]=colors[valid];depth[yy[valid],xx[valid]]=y[valid];coverage[yy[valid],xx[valid]]=True
 # Fill a few padding pixels from neighbors, avoiding seams at the selected face edges.
 for step in range(6):
  sums=np.zeros_like(atlas);n=np.zeros((H,W),np.float32)
  for dy,dx in [(0,1),(0,-1),(1,0),(-1,0)]:
   valid=np.roll(coverage,(dy,dx),(0,1));sums+=np.roll(atlas,(dy,dx),(0,1))*valid[:,:,None];n+=valid
  fill=(~coverage)&(n>0);atlas[fill]=sums[fill]/n[fill,None];coverage|=fill
 # Use original nearby face / lash colors, retaining their variation along x.
 from mathutils.geometry import barycentric_transform
 def sample(x,z):
  hit,n,i,d=s.tree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
  if hit is None:return None
  t=s.tris[i];name=original_names[i]
  if name not in s.sources:return None
  im=s.sources[name];uv=barycentric_transform(hit,*(s.coords[j] for j in t.vertices),*original_uvs[i]);return s.arrays[im.name][int(uv.y*im.size[1])%im.size[1],int(uv.x*im.size[0])%im.size[0],:3]
 changed=0
 for xpix in range(W):
  x=xmin+(xpix+.5)/W*(xmax-xmin)
  if not -.048<x<-.016:continue
  edge=float(np.interp(x,curveX,curveZ));skin=sample(x,edge+.0033);lash=sample(x,edge-.0015)
  if skin is None or lash is None or skin.mean()<.43 or lash.mean()>.42:continue
  for ypix in range(H):
   z=zmin+(ypix+.5)/H*(zmax-zmin);sd=z-edge
   if not -.0006<sd<.0022 or not coverage[ypix,xpix]:continue
   a=min(1,max(0,(sd+.00004)/.00008));a=a*a*(3-2*a);target=lash*(1-a)+skin*a;fade=min(1,(sd+.0006)/.00025,(.0022-sd)/.0005,(x+.048)/.001,(-.016-x)/.001);fade=max(0,fade);atlas[ypix,xpix,:3]=atlas[ypix,xpix,:3]*(1-fade)+target*fade;changed+=1
 im=bpy.data.images.new('T_EyelidPreserved_'+str(component),W,H);im.pixels.foreach_set(atlas.ravel());im.filepath_raw=str(O/'textures'/(im.name+'.png'));im.file_format='PNG';im.save();im.pack();newmats={}
 for p in faces:
  oldmi=p.material_index
  if oldmi not in newmats:
   m=me.materials[oldmi].copy();m.name='M_EyelidPatch_'+str(component)+'_'+str(oldmi);nt=m.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');n=nt.nodes.new('ShaderNodeTexImage');n.image=im;nt.links.new(n.outputs['Color'],bs.inputs['Base Color']);me.materials.append(m);newmats[oldmi]=len(me.materials)-1
  p.material_index=newmats[oldmi]
  for li in p.loop_indices:
   saveduv[li]=list(me.uv_layers.active.data[li].uv);v=me.vertices[me.loops[li].vertex_index].co;me.uv_layers.active.data[li].uv=((v.x-xmin)/(xmax-xmin),(v.z-zmin)/(zmax-zmin))
 report[str(component)]={'faces':len(faces),'changed_pixels':changed,'bounds':[xmin,xmax,zmin,zmax]}
(O/'eyelid_patch_changes.json').write_text(json.dumps({'patches':report,'original_uv_by_loop':saveduv},indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(O/'eyepatch_stage.blend'))
sc=bpy.context.scene;sc.cycles.samples=24;cam=sc.camera;cam.location=(-.034,-3,.902);cam.rotation_euler=(Vector((-.034,0,.902))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.10;sc.render.resolution_x=sc.render.resolution_y=1000;sc.render.filepath=str(O/'renders/eye_patch.png');bpy.ops.render.render(write_still=True);print('EYE_PATCH_DONE',report,flush=True)
