import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
R=Path(__file__).resolve().parent;O=R/'DetailFinish2'
bpy.ops.wm.open_mainfile(filepath=str(R/'DetailFinish/Delivery/Heroine_DetailFinish.blend'));bpy.context.preferences.filepaths.save_version=0
ob=bpy.data.objects['Heroine_DetailFinish'];me=ob.data;me.calc_loop_triangles();ts=list(me.loop_triangles);cs=[v.co.copy() for v in me.vertices];cid=json.loads((O/'components.json').read_text())['ids']
def bs(m):return next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
arrays={};sources={};outputs={}
for m in me.materials:
 s=bs(m).inputs['Base Color']
 if not s.is_linked or s.links[0].from_node.type!='TEX_IMAGE':continue
 im=s.links[0].from_node.image;sources[m.name]=im
 if im.name not in arrays:
  buf=np.empty(len(im.pixels),np.float32);im.pixels.foreach_get(buf);arrays[im.name]=buf.reshape(im.size[1],im.size[0],4)
tree=BVHTree.FromPolygons(cs,[t.vertices[:] for t in ts],all_triangles=True)
def sample(x,z):
 h,n,i,d=tree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
 if h is None:return None
 t=ts[i];name=me.materials[t.material_index].name
 if name not in sources:return None
 im=sources[name];w,hgt=im.size;uv=barycentric_transform(h,*(cs[j] for j in t.vertices),*(Vector((*me.uv_layers.active.data[l].uv,0)) for l in t.loops));return arrays[im.name][int(uv.y*hgt)%hgt,int(uv.x*w)%w,:3]
def raster(t):
 name=me.materials[t.material_index].name;im=sources[name];w,h=im.size;uv=np.array([me.uv_layers.active.data[l].uv[:] for l in t.loops])*[w,h]-.5;lo=np.maximum(np.floor(uv.min(0)).astype(int),0);hi=np.minimum(np.ceil(uv.max(0)).astype(int),[w-1,h-1]);yy,xx=np.mgrid[lo[1]:hi[1]+1,lo[0]:hi[0]+1];a=uv[1]-uv[0];b=uv[2]-uv[0];det=a[0]*b[1]-a[1]*b[0]
 if abs(det)<1e-8:return None
 dx=xx-uv[0,0];dy=yy-uv[0,1];u=(dx*b[1]-dy*b[0])/det;v=(a[0]*dy-a[1]*dx)/det;valid=(u>=0)&(v>=0)&(u+v<=1);p=np.array([cs[i][:] for i in t.vertices]);xyz=p[0]+u[:,:,None]*(p[1]-p[0])+v[:,:,None]*(p[2]-p[0]);return yy,xx,valid,xyz
def paint(name,y,x,color):
 if name not in outputs:outputs[name]=arrays[sources[name].name].copy()
 outputs[name][y,x,:3]=color
counts={}
# Existing ribbon pieces provide the geometric mask; preserve stripes, replace only low-chroma contamination.
for component in [11,13,16]:
 good={};bad={}
 for t in ts:
  if cid[t.vertices[0]]!=component:continue
  name=me.materials[t.material_index].name
  if name not in sources:continue
  data=raster(t)
  if data is None:continue
  yy,xx,valid,xyz=data;rgb=arrays[sources[name].name][yy,xx,:3];r,g,b=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2]
  reject=valid&(r>.235)&(b<r*1.32);accept=valid&(b>r*1.48)&(r>.10)&(r<.42)
  for iy,ix in zip(*np.where(accept)):good[(name,int(yy[iy,ix]),int(xx[iy,ix]))]=(xyz[iy,ix],rgb[iy,ix])
  for iy,ix in zip(*np.where(reject)):bad[(name,int(yy[iy,ix]),int(xx[iy,ix]))]=xyz[iy,ix]
 entries=list(good.values());kd=KDTree(len(entries))
 for i,(p,col) in enumerate(entries):kd.insert(Vector(p),i)
 kd.balance();fixed=0
 for (name,y,x),p in bad.items():
  near=kd.find_n(Vector(p),4)
  if not near or near[0][2]>.012:continue
  paint(name,y,x,np.mean([entries[i][1] for c,i,d in near],0));fixed+=1
 counts['ribbon_'+str(component)]=fixed
# Define only the original eyelash's upper border; clone adjacent original skin/lash gradients.
curveX=np.array([-.048,-.043,-.038,-.033,-.028,-.023,-.018,-.015])
curveZ=np.array([.9050,.9065,.9071,.9072,.9073,.9067,.9053,.9040])
for t in ts:
 name=me.materials[t.material_index].name;c=sum((cs[i] for i in t.vertices),Vector())/3
 if name not in sources or cid[t.vertices[0]] not in [14,21] or not(-.052<c.x<-.012 and .902<c.z<.912 and c.y<-.035):continue
 data=raster(t)
 if data is None:continue
 yy,xx,valid,xyz=data;x=xyz[:,:,0];z=xyz[:,:,2];edge=np.interp(x,curveX,curveZ);signed=z-edge;mask=valid&(x>-.047)&(x<-.016)&(signed>-.00035)&(signed<.00085)
 for iy,ix in zip(*np.where(mask)):
  wx,wz=float(x[iy,ix]),float(z[iy,ix]);sd=float(signed[iy,ix]);above=sample(wx,float(edge[iy,ix])+.003);below=sample(wx,float(edge[iy,ix])-.0014)
  if above is None or below is None or above.mean()<.45 or below.mean()>.4:continue
  tval=min(1,max(0,(sd+.00010)/.00020));tval=tval*tval*(3-2*tval);col=below*(1-tval)+above*tval
  fade=min(1,(.00085-sd)/.00025,(sd+.00035)/.00015);fade=max(0,fade);old=arrays[sources[name].name][yy[iy,ix],xx[iy,ix],:3];paint(name,int(yy[iy,ix]),int(xx[iy,ix]),old*(1-fade)+col*fade);counts['lash_border']=counts.get('lash_border',0)+1
for name,dst in outputs.items():
 src=sources[name];im=bpy.data.images.new('T_LocalFinish2_'+name,src.size[0],src.size[1]);im.pixels.foreach_set(dst.ravel());im.filepath_raw=str(O/'textures'/(im.name+'.png'));im.file_format='PNG';im.save();im.pack();m=me.materials[name];n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=im;m.node_tree.links.new(n.outputs['Color'],bs(m).inputs['Base Color'])
ob.name='Heroine_DetailFinish2';bpy.ops.wm.save_as_mainfile(filepath=str(O/'texture_stage.blend'));(O/'texture_changes.json').write_text(json.dumps(counts,indent=2))
sc=bpy.context.scene;sc.cycles.samples=20
for name,x,z,scale in [('collar',0,.765,.23),('eye',-.034,.902,.10)]:
 cam=sc.camera;cam.location=(x,-3,z);cam.rotation_euler=(Vector((x,0,z))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.resolution_x=sc.render.resolution_y=1000;sc.render.filepath=str(O/'renders'/f'{name}.png');bpy.ops.render.render(write_still=True)
print('TEXTURES_DONE',counts,flush=True)
