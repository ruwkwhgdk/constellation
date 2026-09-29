import bpy,sys,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R));from surface_retouch_utils import Surface,inside
O=R/'DetailFinish2';bpy.ops.wm.open_mainfile(filepath=str(O/'texture_stage.blend'));bpy.context.preferences.filepaths.save_version=0;ob=bpy.data.objects['Heroine_DetailFinish2'];s=Surface(ob);cid=json.loads((O/'components.json').read_text())['ids'];counts={}
for region in ['pin','hem']:
 good={};bad={}
 for t in s.tris:
  component=cid[t.vertices[0]];c=sum((s.coords[i] for i in t.vertices),Vector())/3
  if region=='pin' and not(component==12 and c.y<-.025 and -.054<c.x<-.029 and .913<c.z<.935):continue
  if region=='hem' and not(component==1 and c.z<.49):continue
  data=s.raster(t)
  if data is None:continue
  name,yy,xx,valid,xyz,rgb=data;r,g,b=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2]
  if region=='pin':
   px=(xyz[:,:,0]+.034)/.1*1000+500;py=500-(xyz[:,:,2]-.902)/.1*1000
   zone=inside(px,py,[(355,205),(478,349),(465,358),(349,226)])
   accept=valid&zone&(r>.54)&(np.abs(r-b)<.15);reject=valid&zone&(r<.49)
  else:
   # Only hem's lowest strip; blue pleat surfaces above provide matching color samples.
   ang=np.arctan2(xyz[:,:,1]/.075,xyz[:,:,0]/.101);edge=.4625+.014*np.abs(np.cos(ang))**1.5
   accept=valid&(xyz[:,:,2]>edge+.003)&(b>r*1.3)&(r>.08)
   reject=valid&(xyz[:,:,2]<edge+.003)&(r>.22)&(b<r*1.34)
  for iy,ix in zip(*np.where(accept)):good[(name,int(yy[iy,ix]),int(xx[iy,ix]))]=(xyz[iy,ix],rgb[iy,ix])
  for iy,ix in zip(*np.where(reject)):bad[(name,int(yy[iy,ix]),int(xx[iy,ix]))]=xyz[iy,ix]
 entries=list(good.values());kd=KDTree(len(entries))
 for i,(p,col) in enumerate(entries):kd.insert(Vector(p),i)
 kd.balance();fixed=0
 for (name,y,x),p in bad.items():
  near=kd.find_n(Vector(p),4)
  if not near or near[0][2]>(.0012 if region=='pin' else .008):continue
  s.paint(name,y,x,np.mean([entries[i][1] for c,i,d in near],0));fixed+=1
 counts[region]=fixed
s.save(O/'textures','T_PinHem');bpy.ops.wm.save_as_mainfile(filepath=str(O/'pinhem_stage.blend'));(O/'pinhem_changes.json').write_text(json.dumps(counts,indent=2));print('PINHEM_DONE',counts,flush=True)
