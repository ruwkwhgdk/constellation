import bpy,sys,json
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import barycentric_transform
import numpy as np
R=Path(__file__).resolve().parent;O=R/'DetailFinish2';sys.path.insert(0,str(R));from surface_retouch_utils import Surface
bpy.ops.wm.open_mainfile(filepath=str(O/'lidblend_candidate.blend'));bpy.context.preferences.filepaths.save_version=0;body=bpy.data.objects['Heroine_DetailFinish2'];s=Surface(body);fixed=0
for t in s.tris:
 name=body.data.materials[t.material_index].name;c=sum((s.coords[i] for i in t.vertices),Vector())/3
 if name!='M_Shirt' or not(.806<c.z<.825 and c.y<0 and .034<abs(c.x)<.045):continue
 data=s.raster(t)
 if data is None:continue
 name,yy,xx,valid,xyz,rgb=data;px=xyz[:,:,0]/.23*1000+500;py=500-(xyz[:,:,2]-.765)/.23*1000;ax=np.abs(px-500)
 mask=valid&(ax>169)&(ax<185)&(py>245)&(py<316)&(rgb[:,:,0]>rgb[:,:,2]*1.04)
 for iy,ix in zip(*np.where(mask)):
  p=xyz[iy,ix];h,n,i,d=s.tree.ray_cast(Vector((float(p[0]),-1,float(p[2]))),Vector((0,1,0)))
  if h is None or abs(h.y-float(p[1]))>.0002:continue
  h,n,i,d=s.tree.ray_cast(Vector((.036 if p[0]>0 else -.036,-1,float(p[2]))),Vector((0,1,0)))
  if h is None:continue
  donor=s.tris[i];dn=body.data.materials[donor.material_index].name
  if dn not in s.sources:continue
  im=s.sources[dn];uv=barycentric_transform(h,*(s.coords[j] for j in donor.vertices),*(Vector((*body.data.uv_layers.active.data[l].uv,0)) for l in donor.loops));col=s.arrays[im.name][int(uv.y*im.size[1])%im.size[1],int(uv.x*im.size[0])%im.size[0],:3]
  if col.mean()<.5 or abs(col[0]-col[2])>.065:continue
  s.paint(name,int(yy[iy,ix]),int(xx[iy,ix]),col);fixed+=1
s.save(O/'textures','T_CollarEdgeFinal');(O/'collar_edge_changes.json').write_text(json.dumps({'fixed_texels':fixed}));bpy.ops.wm.save_as_mainfile(filepath=str(O/'polished_stage.blend'));sc=bpy.context.scene;sc.cycles.samples=20;cam=sc.camera;cam.location=(0,-3,.765);cam.rotation_euler=(Vector((0,0,.765))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.23;sc.render.resolution_x=sc.render.resolution_y=1000;sc.render.filepath=str(O/'renders/collar_final.png');bpy.ops.render.render(write_still=True);print('COLLAR_EDGE',fixed,flush=True)
