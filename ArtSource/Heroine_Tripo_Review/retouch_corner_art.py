"""UV-space retouch limited by marked model-space polygons; retain original shading art."""
import bpy,math,json
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
R=Path(__file__).resolve().parent;O=R/'ContourRepair'
bpy.ops.wm.open_mainfile(filepath=str(O/'Heroine_ContourRepair_Sculpt.blend'));body=bpy.data.objects['Heroine_ContourRepair'];me=body.data
bpy.context.preferences.filepaths.save_version=0
source=me.materials['M_Hair'].node_tree.nodes.get('Principled BSDF').inputs['Base Color'].links[0].from_node.image;W,H=source.size;src=np.array(source.pixels[:],dtype=np.float32).reshape(H,W,4);dst=src.copy()
me.calc_loop_triangles();skintris=[t for t in me.loop_triangles if me.materials[t.material_index].name=='M_Skin'];coords=[v.co.copy() for v in me.vertices];tree=BVHTree.FromPolygons(coords,[t.vertices[:] for t in skintris],all_triangles=True)
uvs=[[Vector((*me.uv_layers.active.data[l].uv,0)) for l in t.loops] for t in skintris]
def sample_skin(x,z):
 hit,n,i,dist=tree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
 if hit is None:return np.array([.72,.62,.58,1])
 uv=barycentric_transform(hit,*(coords[j] for j in skintris[i].vertices),*uvs[i]);u=int(uv.x*W)%W;v=int(uv.y*H)%H;return src[v,u]
def polygon(x,y,points):
 inside=np.zeros(x.shape,bool)
 for i in range(len(points)):
  a,b=points[i],points[(i+1)%len(points)]
  inside^=((a[1]>y)!=(b[1]>y))&(x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1]+1e-20)+a[0])
 return inside
hairpolys=[[(698,64),(740,60),(802,582),(774,606),(725,245)],[(891,298),(930,290),(930,531),(891,525)],[(260,675),(332,747),(460,873),(592,953),(578,986),(470,970),(378,915),(305,815)],[(415,487),(487,418),(493,426),(426,496)],[(839,655),(917,671),(913,761),(819,769)]]
cheekpoly=[(430,744),(485,756),(589,805),(590,877),(584,957),(536,960),(498,889),(458,860)]
hairmask=np.zeros((H,W),bool);skinmask=np.zeros((H,W),bool);skinxyz={}
for t in me.loop_triangles:
 name=me.materials[t.material_index].name
 if name not in ['M_Hair','M_Skin']:continue
 cs=np.array([coords[i][:] for i in t.vertices]);center=cs.mean(axis=0)
 if center[1]>.03 or not .846<center[2]<.96 or not -.085<center[0]<.020:continue
 uv=np.array([me.uv_layers.active.data[l].uv[:] for l in t.loops])*np.array([W,H])-.5
 lo=np.maximum(np.floor(uv.min(axis=0)).astype(int),0);hi=np.minimum(np.ceil(uv.max(axis=0)).astype(int),[W-1,H-1])
 if np.any(hi<lo):continue
 yy,xx=np.mgrid[lo[1]:hi[1]+1,lo[0]:hi[0]+1];p=np.stack([xx-uv[0,0],yy-uv[0,1]],axis=-1);a=uv[1]-uv[0];b=uv[2]-uv[0];det=a[0]*b[1]-a[1]*b[0]
 if abs(det)<1e-8:continue
 u=(p[:,:,0]*b[1]-p[:,:,1]*b[0])/det;v=(a[0]*p[:,:,1]-a[1]*p[:,:,0])/det;valid=(u>=-.005)&(v>=-.005)&(u+v<=1.005)
 xyz=cs[0]+u[:,:,None]*(cs[1]-cs[0])+v[:,:,None]*(cs[2]-cs[0]);px=(xyz[:,:,0]+.034)/.1*1100+550;py=550-(xyz[:,:,2]-.902)/.1*1100
 if name=='M_Hair':
  region=np.zeros(valid.shape,bool)
  for poly in hairpolys:region|=polygon(px,py,poly)
  mask=valid&region;hairmask[yy[mask],xx[mask]]=True
 else:
  mask=valid&(polygon(px,py,cheekpoly)|polygon(px,py,[(752,583),(783,583),(795,669),(730,674),(729,644),(748,621)])|polygon(px,py,[(687,563),(723,562),(746,585),(741,600),(715,588)])|polygon(px,py,[(409,518),(433,523),(445,550),(419,567)]))
  for iy,ix in zip(*np.where(mask)):
   row,col=int(yy[iy,ix]),int(xx[iy,ix]);skinmask[row,col]=True;skinxyz[(row,col)]=xyz[iy,ix]
# Replace only the pale transfer specks with nearby dark/cool hair texels.
bad=hairmask&(src[:,:,0]>.19)&((src[:,:,0]>src[:,:,2]*.91)|(src[:,:,:3].min(axis=2)>.32))
ys,xs=np.where(bad);fixed=0
for y,x in zip(ys,xs):
 samples=[]
 for dy in [-28,-16,-8,0,8,16,28]:
  for dx in [-28,-16,-8,0,8,16,28]:
   c=src[(y+dy)%H,(x+dx)%W,:3]
   if .055<c.max()<.24 and c[2]>c[0]*1.015:samples.append(c)
 target=np.median(samples,axis=0) if samples else np.array([.13,.12,.16])
 dst[y,x,:3]=target;fixed+=1
painted=0
for (y,x),xyz in skinxyz.items():
 c=src[y,x,:3]
 px=(xyz[0]+.034)/.1*1100+550;py=550-(xyz[2]-.902)/.1*1100
 if (685<px<748 and 560<py<602) or (405<px<446 and 516<py<569):
  if c.mean()>.30:
   target=sample_skin(float(xyz[0]-.004 if px>600 else -.040),float(xyz[2]+.001 if px>600 else .9035));dst[y,x]=target
  continue
 # Clone from the adjoining clear cheek at the same height, preserving its vertical tone.
 candidates=[sample_skin(float(xyz[0]+dx),float(xyz[2])) for dx in ([.005,.007,.010] if px>700 else [.008,.011,.014])]
 good=[a for a in candidates if a[:3].mean()>.57]
 if not good:continue
 target=np.median(good,axis=0);alpha=float(np.clip((target[:3].mean()-c.mean()-.012)/.038,0,1));dst[y,x]=src[y,x]*(1-alpha)+target*alpha;painted+=1
im=bpy.data.images.new('T_Contour_FinalRetouch',W,H);im.pixels.foreach_set(dst.ravel());im.filepath_raw=str(O/'textures/T_Contour_FinalRetouch.png');im.file_format='PNG';im.save();im.pack()
for name in ['M_Hair','M_Skin']:
 m=me.materials[name];nt=m.node_tree;bs=nt.nodes.get('Principled BSDF');t=nt.nodes.new('ShaderNodeTexImage');t.image=im;nt.links.new(t.outputs['Color'],bs.inputs['Base Color'])
(O/'texture_final_changes.json').write_text(json.dumps({'hair_texels_repaired':fixed,'cheek_texels_repaired':painted,'original_texture_pixels':W*H},indent=2))
sc=bpy.context.scene;sc.cycles.samples=24;sc.render.filepath=str(O/'renders/final_retouch.png');bpy.ops.wm.save_as_mainfile(filepath=str(O/'Heroine_ContourRepair_Final.blend'));bpy.ops.render.render(write_still=True)
