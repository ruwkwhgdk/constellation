import bpy,bmesh,sys,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import barycentric_transform
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R));from surface_retouch_utils import Surface
O=R/'DetailFinish2';bpy.ops.wm.open_mainfile(filepath=str(O/'eyepatch_stage.blend'));bpy.context.preferences.filepaths.save_version=0;body=bpy.data.objects['Heroine_DetailFinish2'];s=Surface(body);me=body.data;cid=json.loads((O/'components.json').read_text())['ids'];norms=[n.vector.copy() for n in me.corner_normals]
def source_sample(x,z):
 h,n,i,d=s.tree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
 if h is None:return None
 t=s.tris[i];name=me.materials[t.material_index].name
 if name not in s.sources:return None
 uv=barycentric_transform(h,*(s.coords[j] for j in t.vertices),*(Vector((*me.uv_layers.active.data[l].uv,0)) for l in t.loops));im=s.sources[name];col=s.arrays[im.name][int(uv.y*im.size[1])%im.size[1],int(uv.x*im.size[0])%im.size[0]];return uv,col,name
# Lower-lid skin seam: match cheek color while keeping the separate eyeliner and iris intact.
band=bpy.data.objects['Lower_Lid_Skin_-1'];W,H=512,64;pixels=np.ones((H,W,4),np.float32)
for u in range(W):
 t=u/(W-1)*48;row=min(47,int(t));f=t-row;v0=band.data.vertices[row*4].co;v1=band.data.vertices[(row+1)*4].co;p=v0.lerp(v1,f);sample=source_sample(p.x,p.z-.006)
 col=sample[1] if sample and sample[1][:3].mean()>.4 else np.array([.81,.72,.69,1]);pixels[:,u]=col
im=bpy.data.images.new('T_LowerLidSkinMatched',W,H);im.pixels.foreach_set(pixels.ravel());im.filepath_raw=str(O/'textures'/(im.name+'.png'));im.file_format='PNG';im.save();im.pack();mat=band.data.materials[0].copy();mat.name='M_LowerLidSkinMatched';nt=mat.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');tex=nt.nodes.new('ShaderNodeTexImage');tex.image=im;nt.links.new(tex.outputs['Color'],bs.inputs['Base Color']);band.data.materials[0]=mat
for p in band.data.polygons:
 for li in p.loop_indices:
  row,k=divmod(band.data.loops[li].vertex_index,4);band.data.uv_layers.active.data[li].uv=(row/48,.1+.8*k/3)
band.data.normals_split_custom_set([Vector((-.25,-1,.22)).normalized() for l in band.data.loops])
normalcount=0
for li,l in enumerate(me.loops):
 v=me.vertices[l.vertex_index];x,y,z=v.co
 if cid[v.index]==14 and y<-.035:
  r2=((x+.021)/.009)**2+((z-.891)/.010)**2
  if r2<1:norms[li]=norms[li].lerp(Vector((-.28,-1,.23)).normalized(),.65*(1-r2)).normalized();normalcount+=1
me.normals_split_custom_set(norms)
# Repair the isolated painted nick in the rear hair, keeping the real strand gaps.
good=[];bad=[]
for t in s.tris:
 c=sum((s.coords[j] for j in t.vertices),Vector())/3
 if cid[t.vertices[0]]!=12 or c.y<.04 or not(.038<c.x<.050 and .912<c.z<.932):continue
 data=s.raster(t)
 if data is None:continue
 name,yy,xx,valid,xyz,rgb=data;r2=((xyz[:,:,0]-.044)/.003)**2+((xyz[:,:,2]-.921)/.006)**2
 for iy,ix in zip(*np.where(valid)):
  c=rgb[iy,ix];item=(name,int(yy[iy,ix]),int(xx[iy,ix]),xyz[iy,ix],c)
  if c[0]>.115 and c[2]>c[0]*1.08:good.append(item)
  elif r2[iy,ix]<1 and c[0]<.115:bad.append(item)
from mathutils.kdtree import KDTree
kd=KDTree(len(good))
for i,item in enumerate(good):kd.insert(Vector(item[3]),i)
kd.balance()
for name,y,x,p,col in bad:
 near=kd.find_n(Vector(p),4)
 if near:s.paint(name,y,x,np.mean([good[i][4] for c,i,d in near],0))
s.save(O/'textures','T_RearNick')
# Close only the two local pocket endpoint holes discovered in the boundary-edge audit.
oldfaces=[tuple(p.vertices) for p in me.polygons];oldnorms=[n.vector.copy() for n in me.corner_normals];bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();uvl=bm.loops.layers.uv.active;added=0
for ids in [[1163,1165,1159,1174,1171],[4361,4348,4340,4345,4357]]:
 verts=[bm.verts[i] for i in ids]
 try:f=bm.faces.new(verts)
 except ValueError:continue
 f.normal_update()
 if f.normal.y>0:f.normal_flip()
 f.material_index=me.materials.find('M_Cardigan');f.smooth=True
 for l in f.loops:
  p=l.vert.co;donor=source_sample(p.x+(.006 if p.x>0 else -.006),p.z)
  if donor and donor[2]=='M_Cardigan':l[uvl].uv=donor[0].xy
  else:l[uvl].uv=next(iter(l.vert.link_loops))[uvl].uv
 added+=1
bm.to_mesh(me);bm.free();me.update();preserved=[tuple(p.vertices) for p in me.polygons[:len(oldfaces)]]==oldfaces
if preserved:
 n=oldnorms+[me.vertices[l.vertex_index].normal.copy() for l in list(me.loops)[len(oldnorms):]];me.normals_split_custom_set(n)
(O/'seam_changes.json').write_text(json.dumps({'lower_skin_normals':normalcount,'rear_nick_texels':len(bad),'pocket_faces_added':added,'existing_face_order_preserved':preserved},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(O/'seams_stage.blend'))
sc=bpy.context.scene;sc.cycles.samples=20
for name,loc,target,scale in [('eye',(-.034,-3,.902),(-.034,0,.902),.10),('skirt',(0,-3,.505),(0,0,.505),.34),('head_back',(0,3,.89),(0,0,.89),.28)]:
 cam=sc.camera;cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.resolution_x=sc.render.resolution_y=1000;sc.render.filepath=str(O/'renders'/f'{name}.png');bpy.ops.render.render(write_still=True)
print('SEAMS_DONE',flush=True)
