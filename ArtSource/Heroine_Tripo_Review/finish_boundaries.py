import bpy,json
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
R=Path(__file__).resolve().parent;O=R/'DetailFinish'
bpy.ops.wm.open_mainfile(filepath=str(O/'stage3.blend'));bpy.context.preferences.filepaths.save_version=0
ob=bpy.data.objects['Heroine_DetailFinish'];me=ob.data;me.calc_loop_triangles()
def bs(m):return next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
# Restore original shirt map: some beige areas intentionally depict adjacent cardigan.
m=me.materials['M_Shirt'];n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images['T_Heroine_BaseColor_Corrected'];m.node_tree.links.new(n.outputs['Color'],bs(m).inputs['Base Color'])
tris=list(me.loop_triangles);co=[v.co.copy() for v in me.vertices];tree=BVHTree.FromPolygons(co,[t.vertices[:] for t in tris],all_triangles=True)
sources={};arrays={};outputs={}
for m in me.materials:
 s=bs(m).inputs['Base Color']
 if not s.is_linked or s.links[0].from_node.type!='TEX_IMAGE':continue
 im=s.links[0].from_node.image;sources[m.name]=im
 if im.name not in arrays:arrays[im.name]=np.array(im.pixels[:],np.float32).reshape(im.size[1],im.size[0],4)
 outputs[m.name]=arrays[im.name].copy()
def sample(x,z):
 hit,n,i,d=tree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
 if hit is None:return None
 t=tris[i];name=me.materials[t.material_index].name
 if name not in sources:return None
 im=sources[name];w,h=im.size;uv=barycentric_transform(hit,*(co[j] for j in t.vertices),*(Vector((*me.uv_layers.active.data[l].uv,0)) for l in t.loops))
 return arrays[im.name][int(uv.y*h)%h,int(uv.x*w)%w,:3]
def poly(x,y,pts):
 inside=np.zeros(x.shape,bool)
 for a,b in zip(pts,pts[1:]+pts[:1]):inside^=((a[1]>y)!=(b[1]>y))&(x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1]+1e-20)+a[0])
 return inside
counts={};seen=set()
for t in tris:
 name=me.materials[t.material_index].name
 if name not in outputs or name=='M_Brow_SurfacePreserved':continue
 cs=np.array([co[i][:] for i in t.vertices]);c=cs.mean(0)
 if c[1]>.005:continue
 region='eye' if -.053<c[0]<-.015 and .902<c[2]<.911 else 'collar' if name=='M_Shirt' and .805<c[2]<.825 else 'ribbon' if name in ['M_Ribbon','M_Details'] and abs(c[0])<.045 and .735<c[2]<.81 else 'hem' if name in ['M_Skirt','M_Details'] and abs(c[0])<.11 and .459<c[2]<.49 else None
 if not region:continue
 im=sources[name];w,h=im.size;src=arrays[im.name];dst=outputs[name]
 uv=np.array([me.uv_layers.active.data[l].uv[:] for l in t.loops])*[w,h]-.5;lo=np.maximum(np.floor(uv.min(0)).astype(int),0);hi=np.minimum(np.ceil(uv.max(0)).astype(int),[w-1,h-1]);yy,xx=np.mgrid[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
 a=uv[1]-uv[0];b=uv[2]-uv[0];det=a[0]*b[1]-a[1]*b[0]
 if abs(det)<1e-8:continue
 dx=xx-uv[0,0];dy=yy-uv[0,1];u=(dx*b[1]-dy*b[0])/det;v=(a[0]*dy-a[1]*dx)/det;valid=(u>=0)&(v>=0)&(u+v<=1)
 xyz=cs[0]+u[:,:,None]*(cs[1]-cs[0])+v[:,:,None]*(cs[2]-cs[0]);x=xyz[:,:,0];z=xyz[:,:,2];rgb=src[yy,xx,:3]
 if region=='eye':
  px=(x+.034)/.1*1000+500;py=500-(z-.902)/.1*1000
  mask=valid&poly(px,py,[(428,440),(553,437),(590,442),(640,454),(692,477),(686,485),(637,464),(587,451),(553,448),(427,451)])&(rgb.mean(2)>.39)
 elif region=='collar':
  px=x/.23*1000+500;py=500-(z-.765)/.23*1000
  mask=valid&(np.abs(px-500)>164)&(np.abs(px-500)<181)&(py>259)&(py<305)&(rgb[:,:,0]>rgb[:,:,2]*1.06)
 elif region=='ribbon':
  px=x/.23*1000+500;py=500-(z-.765)/.23*1000
  mask=np.zeros(valid.shape,bool)
  for pts in [[(646,367),(659,372),(645,444),(635,449)],[(585,527),(638,548),(635,566),(589,545)],[(364,494),(383,491),(407,578),(396,586),(369,555)],[(479,443),(508,443),(508,486),(489,486)]]:mask|=poly(px,py,pts)
  mask&=valid&(rgb[:,:,0]>.28)&(rgb[:,:,0]>rgb[:,:,2]*.95)
 else:
  hem=.464+.017*(np.abs(x)/.10)**1.5;mask=valid&(np.abs(z-hem)<.0028)&(rgb.mean(2)>.23)&(rgb[:,:,0]>rgb[:,:,2]*.84)
 for iy,ix in zip(*np.where(mask)):
  row,col=int(yy[iy,ix]),int(xx[iy,ix]);key=(name,row,col)
  if key in seen:continue
  seen.add(key);wx,wz=float(x[iy,ix]),float(z[iy,ix])
  tx,tz=(wx,wz+.003) if region=='eye' else (wx*.94,wz) if region=='collar' else (wx*.92,wz+.0028) if region=='ribbon' else (wx,wz+.004)
  color=sample(tx,tz)
  if color is None:continue
  if region=='eye' and color.mean()<.40:continue
  if region=='collar' and (abs(color[0]-color[2])>.04 or color.mean()<.45):continue
  if region in ['ribbon','hem'] and (color[2]<color[0]*1.07 or color.mean()>.42):continue
  dst[row,col,:3]=color;counts[region]=counts.get(region,0)+1
for name,dst in outputs.items():
 im=sources[name]
 if np.array_equal(dst,arrays[im.name]):continue
 new=bpy.data.images.new('T_Finish_'+name,im.size[0],im.size[1]);new.pixels.foreach_set(dst.ravel());new.filepath_raw=str(O/'textures'/('T_Finish_'+name+'.png'));new.file_format='PNG';new.save();new.pack();m=me.materials[name];n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=new;m.node_tree.links.new(n.outputs['Color'],bs(m).inputs['Base Color'])
(O/'boundary_changes.json').write_text(json.dumps(counts,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(O/'stage4.blend'))
sc=bpy.context.scene;sc.cycles.samples=24
def render(name,x,z,scale):
 cam=sc.camera;cam.location=(x,-3,z);cam.rotation_euler=(Vector((x,0,z))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.resolution_x=sc.render.resolution_y=1000;sc.render.filepath=str(O/'renders'/f'{name}.png');bpy.ops.render.render(write_still=True)
render('eye',-.034,.902,.10);render('collar',0,.765,.23);render('skirt',0,.505,.34)
print('BOUNDARIES_DONE',counts,flush=True)
