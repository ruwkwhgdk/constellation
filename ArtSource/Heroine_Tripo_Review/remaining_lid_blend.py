import bpy,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import barycentric_transform
R=Path(__file__).resolve().parent;O=R/'DetailFinish2';sys.path.insert(0,str(R));from surface_retouch_utils import Surface
bpy.ops.wm.open_mainfile(filepath=str(O/'lidfit_candidate.blend'));bpy.context.preferences.filepaths.save_version=0;body=bpy.data.objects['Heroine_DetailFinish2'];s=Surface(body);band=bpy.data.objects['Lower_Lid_Skin_-1'];norms=[]
def hit(x,z):
 h,n,i,d=s.tree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
 if h is None:return None
 t=s.tris[i];name=body.data.materials[t.material_index].name
 if name not in s.sources:return None
 uv=barycentric_transform(h,*(s.coords[j] for j in t.vertices),*(Vector((*body.data.uv_layers.active.data[l].uv,0)) for l in t.loops));im=s.sources[name];col=s.arrays[im.name][int(uv.y*im.size[1])%im.size[1],int(uv.x*im.size[0])%im.size[0]];return h,n,col
for v in band.data.vertices:
 row,k=divmod(v.index,4)
 if k==3:
  sample=hit(v.co.x,v.co.z)
  if sample and -.07<sample[0].y<-.03:v.co.y=sample[0].y+.00015
band.data.update()
for l in band.data.loops:
 v=band.data.vertices[l.vertex_index];row,k=divmod(v.index,4);sample=hit(v.co.x,v.co.z);n=v.normal.copy()
 if sample:n=n.lerp(sample[1],(k/3)**2).normalized()
 norms.append(n)
band.data.normals_split_custom_set(norms);W,H=512,64;pixels=np.ones((H,W,4),np.float32)
for ix in range(W):
 r=ix/(W-1)*48;row=min(47,int(r));f=r-row
 for iy in range(H):
  kf=iy/(H-1)*3;k=min(2,int(kf));g=kf-k;p0=band.data.vertices[row*4+k].co.lerp(band.data.vertices[(row+1)*4+k].co,f);p1=band.data.vertices[row*4+k+1].co.lerp(band.data.vertices[(row+1)*4+k+1].co,f);p=p0.lerp(p1,g);actual=hit(p.x,p.z);clean=hit(p.x,p.z-.005)
  ca=actual[2] if actual else np.array([.81,.72,.69,1]);cc=clean[2] if clean and clean[2][:3].mean()>.4 else ca;w=(iy/(H-1))**4;pixels[iy,ix]=cc*(1-w)+ca*w
im=bpy.data.images.new('T_Lid_Transition',W,H);im.pixels.foreach_set(pixels.ravel());im.filepath_raw=str(O/'textures'/(im.name+'.png'));im.file_format='PNG';im.save();im.pack();m=band.data.materials[0].copy();m.name='M_Lid_Transition';nt=m.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');tex=nt.nodes.new('ShaderNodeTexImage');tex.image=im;nt.links.new(tex.outputs['Color'],bs.inputs['Base Color']);band.data.materials[0]=m
for p in band.data.polygons:
 for li in p.loop_indices:
  row,k=divmod(band.data.loops[li].vertex_index,4);band.data.uv_layers.active.data[li].uv=(row/48,k/3)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'lidblend_candidate.blend'));sc=bpy.context.scene;sc.cycles.samples=24;sc.render.filepath=str(O/'renders/lidblend_candidate.png');bpy.ops.render.render(write_still=True);print('LIDBLEND_DONE',flush=True)
