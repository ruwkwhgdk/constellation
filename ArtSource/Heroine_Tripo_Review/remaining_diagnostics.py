import bpy,json,collections
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
R=Path(__file__).resolve().parent;O=R/'DetailFinish2';O.mkdir(exist_ok=True);(O/'renders').mkdir(exist_ok=True);(O/'textures').mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'DetailFinish/Delivery/Heroine_DetailFinish.blend'));ob=bpy.data.objects['Heroine_DetailFinish'];me=ob.data;me.calc_loop_triangles();ts=list(me.loop_triangles);coords=[v.co.copy() for v in me.vertices];tree=BVHTree.FromPolygons(coords,[t.vertices[:] for t in ts],all_triangles=True)
adj=[set() for v in coords]
for e in me.edges:a,b=e.vertices;adj[a].add(b);adj[b].add(a)
pending=set(range(len(coords)));components=[];cid=[0]*len(coords)
while pending:
 stack=[pending.pop()];group=[]
 while stack:
  i=stack.pop();group.append(i);cid[i]=len(components)
  for j in adj[i]:
   if j in pending:pending.remove(j);stack.append(j)
 components.append(group)
arrays={};sources={}
for m in me.materials:
 bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');s=bs.inputs['Base Color']
 if s.is_linked and s.links[0].from_node.type=='TEX_IMAGE':
  im=s.links[0].from_node.image;sources[m.name]=im
  if im.name not in arrays:arrays[im.name]=np.array(im.pixels[:],np.float32).reshape(im.size[1],im.size[0],4)
views={'eye':(-.034,.902,.10,-1),'collar':(0,.765,.23,-1),'skirt':(0,.505,.34,-1),'back':(0,.89,.28,1)}
points={'eye':[(420,349),(375,282),(536,270),(556,446),(642,467),(626,637),(662,617)],'collar':[(645,394),(640,419),(385,517),(618,543),(496,465),(322,282),(436,342),(580,337)],'skirt':[(381,199),(619,199),(537,401),(330,603),(537,610)],'back':[(344,385),(544,180),(663,483),(596,410)]}
out=[]
for view,pts in points.items():
 cx,cz,scale,side=views[view]
 for px,py in pts:
  x=cx+(px/1000-.5)*scale*(-side);z=cz+(.5-py/1000)*scale;hit,n,i,d=tree.ray_cast(Vector((x,side,z)),Vector((0,-side,0)))
  if hit is None:continue
  t=ts[i];name=me.materials[t.material_index].name;uv=barycentric_transform(hit,*(coords[j] for j in t.vertices),*(Vector((*me.uv_layers.active.data[l].uv,0)) for l in t.loops));color=None
  if name in sources:
   im=sources[name];w,h=im.size;color=arrays[im.name][int(uv.y*h)%h,int(uv.x*w)%w,:3].tolist()
  out.append({'view':view,'px':[px,py],'hit':list(hit),'normal':list(n),'face':t.polygon_index,'material':name,'component':cid[t.vertices[0]],'color':color})
(O/'probes.json').write_text(json.dumps(out,indent=2));(O/'components.json').write_text(json.dumps({'ids':cid,'groups':[{'id':i,'count':len(g),'bounds':[[min(coords[j][a] for j in g),max(coords[j][a] for j in g)] for a in range(3)]} for i,g in enumerate(components)]},indent=2))
sc=bpy.context.scene;sc.cycles.samples=12
def render(name,view):
 cx,cz,scale,side=views[view];cam=sc.camera;cam.location=(cx,3*side,cz);cam.rotation_euler=(Vector((cx,0,cz))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.resolution_x=sc.render.resolution_y=1000;sc.render.filepath=str(O/'renders'/f'{name}.png');bpy.ops.render.render(write_still=True)
for m in me.materials:
 nt=m.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');outnode=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');em=nt.nodes.new('ShaderNodeEmission');s=bs.inputs['Base Color']
 if s.is_linked:nt.links.new(s.links[0].from_socket,em.inputs['Color'])
 else:em.inputs['Color'].default_value=s.default_value
 nt.links.new(em.outputs[0],outnode.inputs['Surface'])
render('collar_albedo','collar');render('eye_albedo','eye');render('back_albedo','back');print('DIAGNOSTICS_DONE',flush=True)
