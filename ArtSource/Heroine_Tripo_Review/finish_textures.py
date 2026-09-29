import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
R=Path(__file__).resolve().parent;O=R/'DetailFinish'
bpy.ops.wm.open_mainfile(filepath=str(O/'stage1.blend'));bpy.context.preferences.filepaths.save_version=0
body=bpy.data.objects['Heroine_DetailFinish'];me=body.data;me.calc_loop_triangles()
def base(m):return next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
report={}
for names,tag in [(['M_Ribbon','M_Shirt','M_Skirt'],'Cloth'),(['M_Hair'],'Hair')]:
 source=base(me.materials[names[0]]).inputs['Base Color'].links[0].from_node.image
 W,H=source.size;src=np.array(source.pixels[:],np.float32).reshape(H,W,4);dst=src.copy()
 for name in names:
  good={};bad={}
  for t in me.loop_triangles:
   if me.materials[t.material_index].name!=name:continue
   cs=np.array([me.vertices[i].co[:] for i in t.vertices]);c=cs.mean(0)
   if name=='M_Hair' and not(c[0]>-.005 and c[1]<0 and .85<c[2]<.91):continue
   if name=='M_Shirt' and not(.71<c[2]<.83 and abs(c[0])<.09):continue
   if name=='M_Skirt' and c[2]>.51:continue
   uv=np.array([me.uv_layers.active.data[l].uv[:] for l in t.loops])*[W,H]-.5
   lo=np.maximum(np.floor(uv.min(0)).astype(int),0);hi=np.minimum(np.ceil(uv.max(0)).astype(int),[W-1,H-1])
   if np.any(hi<lo):continue
   yy,xx=np.mgrid[lo[1]:hi[1]+1,lo[0]:hi[0]+1];a=uv[1]-uv[0];b=uv[2]-uv[0];det=a[0]*b[1]-a[1]*b[0]
   if abs(det)<1e-8:continue
   dx=xx-uv[0,0];dy=yy-uv[0,1];u=(dx*b[1]-dy*b[0])/det;v=(a[0]*dy-a[1]*dx)/det
   valid=(u>=0)&(v>=0)&(u+v<=1);rgb=src[yy,xx,:3];r,g,bl=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2]
   if name in ['M_Ribbon','M_Skirt']:
    reject=(r>bl*.98)&(r>.28);accept=(bl>r*1.12)&(r<.4)
   elif name=='M_Shirt':
    reject=(r>bl*1.10)&(r>g*1.025);accept=(np.abs(r-bl)<.025)&(r>.42)
   else:
    reject=(r>.24)&(r>bl*.99);accept=(bl>r*1.015)&(r<.23)&(r>.05)
   xyz=cs[0]+u[:,:,None]*(cs[1]-cs[0])+v[:,:,None]*(cs[2]-cs[0])
   for iy,ix in zip(*np.where(valid&accept)):good[(int(yy[iy,ix]),int(xx[iy,ix]))]=xyz[iy,ix]
   for iy,ix in zip(*np.where(valid&reject)):bad[(int(yy[iy,ix]),int(xx[iy,ix]))]=xyz[iy,ix]
  entries=list(good.items());kd=KDTree(len(entries))
  for i,(p,xyz) in enumerate(entries):kd.insert(Vector(xyz),i)
  kd.balance();fixed=0
  for (y,x),xyz in bad.items():
   near=kd.find_n(Vector(xyz),4)
   if not near or near[0][2]>.009:continue
   colors=[src[entries[i][0]][:3] for co,i,d in near];dst[y,x,:3]=np.mean(colors,0);fixed+=1
  report[name]={'changed_texels':fixed,'candidates':len(bad)}
 im=bpy.data.images.new('T_DetailFinish_'+tag,W,H);im.pixels.foreach_set(dst.ravel());im.filepath_raw=str(O/'textures'/('T_DetailFinish_'+tag+'.png'));im.file_format='PNG';im.save();im.pack()
 for name in names:
  m=me.materials[name];nt=m.node_tree;n=nt.nodes.new('ShaderNodeTexImage');n.image=im;nt.links.new(n.outputs['Color'],base(m).inputs['Base Color'])
(O/'texture_changes.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(O/'stage2.blend'));print('TEXTURE_DONE',report,flush=True)
