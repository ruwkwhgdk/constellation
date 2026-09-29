import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
class Surface:
 def __init__(self,ob):
  self.ob=ob;self.me=ob.data;self.me.calc_loop_triangles();self.tris=list(self.me.loop_triangles);self.coords=[v.co.copy() for v in self.me.vertices];self.tree=BVHTree.FromPolygons(self.coords,[t.vertices[:] for t in self.tris],all_triangles=True);self.sources={};self.arrays={};self.out={}
  for m in self.me.materials:
   bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');s=bs.inputs['Base Color']
   if s.is_linked and s.links[0].from_node.type=='TEX_IMAGE':
    im=s.links[0].from_node.image;self.sources[m.name]=im
    if im.name not in self.arrays:
     a=np.empty(len(im.pixels),np.float32);im.pixels.foreach_get(a);self.arrays[im.name]=a.reshape(im.size[1],im.size[0],4)
 def raster(self,t):
  name=self.me.materials[t.material_index].name
  if name not in self.sources:return None
  im=self.sources[name];w,h=im.size;uv=np.array([self.me.uv_layers.active.data[l].uv[:] for l in t.loops])*[w,h]-.5;lo=np.maximum(np.floor(uv.min(0)).astype(int),0);hi=np.minimum(np.ceil(uv.max(0)).astype(int),[w-1,h-1]);yy,xx=np.mgrid[lo[1]:hi[1]+1,lo[0]:hi[0]+1];a=uv[1]-uv[0];b=uv[2]-uv[0];det=a[0]*b[1]-a[1]*b[0]
  if abs(det)<1e-8:return None
  dx=xx-uv[0,0];dy=yy-uv[0,1];u=(dx*b[1]-dy*b[0])/det;v=(a[0]*dy-a[1]*dx)/det;valid=(u>=0)&(v>=0)&(u+v<=1);cs=np.array([self.coords[i][:] for i in t.vertices]);xyz=cs[0]+u[:,:,None]*(cs[1]-cs[0])+v[:,:,None]*(cs[2]-cs[0]);return name,yy,xx,valid,xyz,self.arrays[im.name][yy,xx,:3]
 def paint(self,name,y,x,col):
  if name not in self.out:self.out[name]=self.arrays[self.sources[name].name].copy()
  self.out[name][y,x,:3]=col
 def save(self,path,tag):
  for name,a in self.out.items():
   src=self.sources[name];im=bpy.data.images.new(tag+'_'+name,src.size[0],src.size[1]);im.pixels.foreach_set(a.ravel());im.filepath_raw=str(path/(im.name+'.png'));im.file_format='PNG';im.save();im.pack();m=self.me.materials[name];bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=im;m.node_tree.links.new(n.outputs['Color'],bs.inputs['Base Color'])
def inside(x,y,points):
 mask=np.zeros(x.shape,bool)
 for a,b in zip(points,points[1:]+points[:1]):mask^=((a[1]>y)!=(b[1]>y))&(x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1]+1e-20)+a[0])
 return mask
