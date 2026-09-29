import bpy,math,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parent;O=R/'DetailFinish'
bpy.ops.wm.open_mainfile(filepath=str(O/'stage2.blend'));bpy.context.preferences.filepaths.save_version=0
body=bpy.data.objects['Heroine_DetailFinish'];me=body.data
tree=BVHTree.FromPolygons([v.co for v in me.vertices],[p.vertices[:] for p in me.polygons])
brace=bpy.data.objects['Heroine_Pearl_Bracelet'];bm=brace.data;adj=[set() for v in bm.vertices]
for e in bm.edges:a,b=e.vertices;adj[a].add(b);adj[b].add(a)
pending=set(range(len(bm.vertices)));groups=[]
while pending:
 stack=[pending.pop()];group=[]
 while stack:
  i=stack.pop();group.append(i)
  for j in adj[i]:
   if j in pending:pending.remove(j);stack.append(j)
 groups.append(group)
center=Vector((-.356,.0005,.7835));inverse=brace.matrix_world.inverted();placements=[]
for k,group in enumerate(groups):
 old=sum((brace.matrix_world@bm.vertices[i].co for i in group),Vector())/len(group)
 a=2*math.pi*k/len(groups);direction=Vector((0,math.cos(a),math.sin(a)))
 hit,n,idx,d=tree.ray_cast(center+direction*.055,-direction,.06)
 if hit is None:hit=center+direction*.020
 target=hit+direction*.0027;placements.append(list(target))
 for i in group:
  delta=brace.matrix_world@bm.vertices[i].co-old;bm.vertices[i].co=inverse@(target+delta*1.6)
bm.update()
shoe=me.materials.find('M_Shoes');stock=me.materials.find('M_Stockings');mat=me.materials[shoe];bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');im=bs.inputs['Base Color'].links[0].from_node.image;w,h=im.size;pixels=list(im.pixels[:]);changed=[]
for p in me.polygons:
 if p.material_index!=shoe:continue
 z=sum(me.vertices[i].co.z for i in p.vertices)/len(p.vertices)
 if z<.039:continue
 uv=sum((me.uv_layers.active.data[l].uv for l in p.loop_indices),Vector((0,0)))/len(p.loop_indices);offset=(int(uv.y*h)%h*w+int(uv.x*w)%w)*4;r,g,b=pixels[offset:offset+3]
 if z>.057 or (b>r*.96 and z>.044):p.material_index=stock;changed.append(p.index)
bs.inputs['Roughness'].default_value=.54;bs.inputs['Specular IOR Level'].default_value=.28
(O/'fit_changes.json').write_text(json.dumps({'bracelet_beads':len(groups),'centers':placements,'ankle_faces_reassigned':changed,'shoe_roughness':.54},indent=2))
sc=bpy.context.scene;sc.cycles.samples=20;sc.render.use_border=False;sc.render.use_crop_to_border=False
def render(name,loc,target,scale):
 cam=sc.camera;cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.resolution_x=sc.render.resolution_y=1000;sc.render.filepath=str(O/'renders'/f'{name}.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'stage3.blend'))
render('collar',(0,-3,.765),(0,0,.765),.23)
render('hand_top',(-.4,-.3,3),(-.4,0,.785),.135)
render('shoes',(0,-3,.067),(0,0,.067),.24)
render('skirt',(0,-3,.505),(0,0,.505),.34)
render('face',(0,-3,.862),(0,0,.862),.30)
print('FIT_DONE',len(changed),flush=True)
