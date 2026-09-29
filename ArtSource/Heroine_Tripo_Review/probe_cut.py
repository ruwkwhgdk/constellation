"""Rebuild eye sockets with stitched skin topology; eliminate generated floating eyelid fragments."""
import bpy,bmesh,math,json
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parent;O=R/'FaceClean';O.mkdir(exist_ok=True);(O/'renders').mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'Refined/Heroine_Refined.blend'))
bpy.context.preferences.filepaths.save_version=0
body=bpy.data.objects['Heroine_Refined'];body.name='Heroine_FaceClean'
for ob in list(bpy.context.scene.objects):
 if ob.type=='MESH' and ob!=body and ob.name!='Heroine_Pearl_Bracelet':bpy.data.objects.remove(ob,do_unlink=True)
def mat(name,col,rough=.7):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Roughness'].default_value=rough;p.inputs['Specular IOR Level'].default_value=.23;return m
hair=body.data.materials['M_Hair'];hp=hair.node_tree.nodes.get('Principled BSDF')
for link in list(hp.inputs['Base Color'].links):hair.node_tree.links.remove(link)
hp.inputs['Base Color'].default_value=(.013,.010,.020,1);hp.inputs['Roughness'].default_value=.56
skin=mat('Face_Skin_Clean',(.56,.405,.35),.74)
lash=mat('Lash_Clean',(.023,.008,.013),.76);lower=mat('Lid_Waterline',(.27,.11,.10),.76)
white=mat('Sclera_Clean',(.68,.60,.55),.51)
iris=bpy.data.materials['Ruby_Iris'];brow=mat('Brow_Clean',(.055,.026,.035),.81)
for m in [skin,lash,lower]:body.data.materials.append(m)
si=body.data.materials.find(skin.name);li=body.data.materials.find(lash.name);lli=body.data.materials.find(lower.name)
bm=bmesh.new();bm.from_mesh(body.data);bm.verts.ensure_lookup_table();uvlayer=bm.loops.layers.uv.active
seen=set();comps=[]
for v in bm.verts:
 if v in seen:continue
 stack=[v];seen.add(v);vs=[];fs=set()
 while stack:
  a=stack.pop();vs.append(a);fs.update(a.link_faces)
  for e in a.link_edges:
   b=e.other_vert(a)
   if b not in seen:seen.add(b);stack.append(b)
 comps.append((vs,fs))
comps.sort(key=lambda p:-len(p[0]));headvs,headfs=comps[2]
# Remove separate generated eyebrow/lash fragments instead of covering them.
bad=[f for vs,fs in comps for f in fs if len(vs)<100 and min(v.co.z for v in vs)>.88 and max(v.co.z for v in vs)<.93]
bmesh.ops.delete(bm,geom=bad,context='FACES')
headfs=[f for f in headfs if f.is_valid];headvs=[v for v in headvs if v.is_valid]
# Use a clean skin material for the head: its old atlas contains painted duplicate eyelids.
for f in headfs:f.material_index=si
report={'removed_floating_faces':len(bad),'sockets':[]}
inners={}

side=-1
cut=[f for f in headfs if f.is_valid and .007<side*f.calc_center_median().x<.056 and .879<f.calc_center_median().z<.928 and f.calc_center_median().y<-.024]
cutset=set(cut);edges=set(e for f in cut for e in f.edges if any(g not in cutset for g in e.link_faces))
bmesh.ops.delete(bm,geom=cut,context='FACES_ONLY')
print('EDGES',len(edges))
adj={}
for e in edges:
 for v in e.verts:adj.setdefault(v,[]).append(e.other_vert(v))
print('DEGREES', {k:sum(len(a)==k for a in adj.values()) for k in range(1,6)})
for v,a in adj.items():
 if len(a)!=2:print('BAD',list(v.co),len(a))
seen=set()
for v in adj:
 if v in seen:continue
 stack=[v];group=[];seen.add(v)
 while stack:
  q=stack.pop();group.append(q)
  for w in adj[q]:
   if w not in seen:seen.add(w);stack.append(w)
 print('LOOP',len(group), [[min(v.co[j] for v in group),max(v.co[j] for v in group)] for j in range(3)])
