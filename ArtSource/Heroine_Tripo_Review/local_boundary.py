"""Local boundary corrections only, based on the user's marked DetailPreserved image."""
import bpy,math,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;O=R/'BoundaryLocal';O.mkdir(exist_ok=True);(O/'renders').mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'DetailPreserved/Heroine_DetailPreserved.blend'))
bpy.context.preferences.filepaths.save_version=0
body=bpy.data.objects['Heroine_DetailPreserved'];body.name='Heroine_BoundaryLocal';me=body.data
original=[v.co.copy() for v in me.vertices];adj=[[] for v in me.vertices];vm=[set() for v in me.vertices]
for e in me.edges:
 a,b=e.vertices;adj[a].append(b);adj[b].append(a)
for p in me.polygons:
 for vi in p.vertices:vm[vi].add(me.materials[p.material_index].name)
def box(x,z,x0,x1,z0,z1,feather=.001):
 return max(0,min(1,(x-x0)/feather,(x1-x)/feather,(z-z0)/feather,(z1-z)/feather))
# Keep front silhouettes and painted details; only tuck small pale rim fragments in depth.
for v in me.vertices:
 x,y,z=v.co
 if y>-.035:continue
 if vm[v.index].issubset({'M_Details','M_Skin'}):
  inner=box(x,z,-.018,-.010,.899,.906,.001)
  outer=box(x,z,-.050,-.042,.900,.907,.001)
  brow=box(x,z,-.050,-.013,.9135,.918,.001)
  if adj[v.index]:
   avg=sum(original[i].y for i in adj[v.index])/len(adj[v.index]);w=max(inner,outer,brow)
   v.co.y+=max(-.00065,min(.00065,(avg-y)*.65))*w
   # Skin-colored slivers at the lash's corners sit just behind the dark lash edge.
   if 'M_Details' in vm[v.index]:v.co.y+=.0002*outer
me.update()
# Match the existing lower-corner patch to the original cheek; retain its topology.
from mathutils.bvhtree import BVHTree
skinpolys=[p for p in me.polygons if me.materials[p.material_index].name=='M_Skin']
tree=BVHTree.FromPolygons(original,[list(p.vertices) for p in skinpolys])
skinpatch=bpy.data.objects.get('Lower_Lid_Skin_-1')
if skinpatch:
 for v in skinpatch.data.vertices:
  x,y,z=v.co;k=v.index%4
  w=max(box(x,z,-.049,-.033,.884,.900,.001),box(x,z,-.023,-.012,.884,.899,.001))
  if w and k>0:
   hit,n,idx,dist=tree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
   if hit and hit.y<-.02:
    target=hit.y+.00004;v.co.y+=(target-y)*w*(k/3)**2
 skinpatch.data.update()
# A feathered attribute gates the hair-only color correction to the red marked strands.
attr=me.color_attributes.new(name='MarkedHairBoundary',type='FLOAT_COLOR',domain='POINT')
marked=0
for v in me.vertices:
 x,y,z=v.co
 w=max(box(x,z,-.014,-.002,.879,.949,.0015),box(x,z,-.004,.013,.880,.928,.0015),box(x,z,-.079,-.044,.848,.899,.002),box(x,z,-.056,-.044,.900,.915,.001)) if y<.04 else 0
 if 'M_Hair' not in vm[v.index]:w=0
 attr.data[v.index].color=(w,w,w,1);marked+=w>0
hair=me.materials['M_Hair'];nt=hair.node_tree;bs=nt.nodes.get('Principled BSDF');source=bs.inputs['Base Color'].links[0].from_socket
def node(kind):return nt.nodes.new(kind)
def mathn(op,a,b):
 n=node('ShaderNodeMath');n.operation=op
 for s,val in zip(n.inputs,[a,b]):
  if isinstance(val,(int,float)):s.default_value=val
  else:nt.links.new(val,s)
 return n.outputs[0]
sep=node('ShaderNodeSeparateColor');nt.links.new(source,sep.inputs[0])
region=node('ShaderNodeAttribute');region.attribute_name=attr.name
warm=mathn('GREATER_THAN',sep.outputs['Red'],mathn('MULTIPLY',sep.outputs['Blue'],1.0))
light=mathn('MULTIPLY',mathn('MAXIMUM',mathn('SUBTRACT',sep.outputs['Red'],.006),0),100)
light=mathn('MINIMUM',light,1);mask=mathn('MULTIPLY',region.outputs['Fac'],mathn('MULTIPLY',warm,light))
mix=node('ShaderNodeMixRGB');mix.blend_type='MIX';nt.links.new(mask,mix.inputs[0]);nt.links.new(source,mix.inputs[1]);mix.inputs[2].default_value=(.015,.012,.022,1);nt.links.new(mix.outputs[0],bs.inputs['Base Color'])
# The bright gap next to the bang is actual skin with stray dark hair painted onto it.
# Clean that transfer locally on the skin material; do not blacken the exposed forehead.
for material_name,attribute_name,color,mode in [('M_Skin','MarkedSkinBoundary',(.58,.435,.385),'skin')]:
 ca=me.color_attributes.new(name=attribute_name,type='FLOAT_COLOR',domain='POINT')
 for v in me.vertices:
  x,y,z=v.co
  if mode=='skin':w=max(box(x,z,-.014,-.002,.903,.949,.001),box(x,z,-.001,.009,.881,.892,.001))
  else:w=max(box(x,z,-.019,-.010,.900,.908,.001),box(x,z,-.050,-.041,.900,.907,.001))
  if y>-.03 or material_name not in vm[v.index]:w=0
  ca.data[v.index].color=(w,w,w,1)
 m=me.materials[material_name];nt=m.node_tree;bs=nt.nodes.get('Principled BSDF');src=bs.inputs['Base Color'].links[0].from_socket
 sep=node('ShaderNodeSeparateColor');nt.links.new(src,sep.inputs[0]);region=node('ShaderNodeAttribute');region.attribute_name=attribute_name
 if mode=='skin':
  amount=1.0
 else:amount=mathn('MINIMUM',mathn('MULTIPLY',mathn('MAXIMUM',mathn('SUBTRACT',sep.outputs['Red'],.10),0),10),1)
 fac=mathn('MULTIPLY',region.outputs['Fac'],amount);mx=node('ShaderNodeMixRGB');nt.links.new(fac,mx.inputs[0]);nt.links.new(src,mx.inputs[1]);mx.inputs[2].default_value=(*color,1);nt.links.new(mx.outputs[0],bs.inputs['Base Color'])
# Mild, masked texture sharpening keeps the eyebrow's original tonal detail.
ca=me.color_attributes.new(name='MarkedBrowSharp',type='FLOAT_COLOR',domain='POINT')
for v in me.vertices:
 x,y,z=v.co;w=box(x,z,-.049,-.012,.916,.922,.001) if y<-.035 and 'M_Skin' in vm[v.index] else 0;ca.data[v.index].color=(w,w,w,1)
nt=me.materials['M_Skin'].node_tree;bs=nt.nodes.get('Principled BSDF');src=bs.inputs['Base Color'].links[0].from_socket;tex=next(n for n in nt.nodes if n.type=='TEX_IMAGE');uv=node('ShaderNodeTexCoord')
def vec(op,a,b):
 n=node('ShaderNodeVectorMath');n.operation=op
 nt.links.new(a,n.inputs[0])
 if op=='SCALE':n.inputs[3].default_value=b
 elif isinstance(b,tuple):n.inputs[1].default_value=b
 else:nt.links.new(b,n.inputs[1])
 return n.outputs[0]
colors=[]
for du,dv in [(.00035,0),(-.00035,0),(0,.00035),(0,-.00035)]:
 t=node('ShaderNodeTexImage');t.image=tex.image;nt.links.new(vec('ADD',uv.outputs['UV'],(du,dv,0)),t.inputs['Vector']);colors.append(t.outputs['Color'])
avg=vec('SCALE',vec('ADD',vec('ADD',colors[0],colors[1]),vec('ADD',colors[2],colors[3])),.25)
sharp=vec('ADD',tex.outputs['Color'],vec('SCALE',vec('SUBTRACT',tex.outputs['Color'],avg),.65));sharp=vec('MINIMUM',vec('MAXIMUM',sharp,(0,0,0)),(1,1,1))
a=node('ShaderNodeAttribute');a.attribute_name=ca.name;mx=node('ShaderNodeMixRGB');nt.links.new(a.outputs['Fac'],mx.inputs[0]);nt.links.new(src,mx.inputs[1]);nt.links.new(sharp,mx.inputs[2]);nt.links.new(mx.outputs[0],bs.inputs['Base Color'])
# Remove only the disconnected pale spur at the marked inner corner (not the main lash).
import bmesh
normals={tuple(round(c,8) for c in me.vertices[me.loops[i].vertex_index].co):me.corner_normals[i].vector.copy() for i in range(len(me.loops))}
bm=bmesh.new();bm.from_mesh(me);seen=set();remove=[]
for v in bm.verts:
 if v in seen:continue
 stack=[v];seen.add(v);vs=[];fs=set()
 while stack:
  q=stack.pop();vs.append(q);fs.update(q.link_faces)
  for e in q.link_edges:
   n=e.other_vert(q)
   if n not in seen:seen.add(n);stack.append(n)
 if 20<len(vs)<40 and min(v.co.x for v in vs)>-.018 and max(v.co.x for v in vs)<-.010 and min(v.co.z for v in vs)>.900 and max(v.co.z for v in vs)<.909:remove.extend(fs)
removed_faces=len(remove)
if remove:bmesh.ops.delete(bm,geom=remove,context='FACES_ONLY')
bm.to_mesh(me);bm.free()
me.normals_split_custom_set([normals.get(tuple(round(c,8) for c in me.vertices[l.vertex_index].co),Vector((0,0,0))) for l in me.loops])
# Review first; final baking/export is a separate step after visual inspection.
report={'baseline':'DetailPreserved','body_modified_vertices':sum((v.co-original[i]).length>1e-10 for i,v in enumerate(me.vertices)),'max_body_displacement':max((v.co-original[i]).length for i,v in enumerate(me.vertices)),'body_front_outline_unchanged':all(v.co.x==original[i].x and v.co.z==original[i].z for i,v in enumerate(me.vertices)),'marked_hair_vertices':marked,'removed_corner_fragment_faces':removed_faces,'geometry_replacements':False,'iris_edited':False,'material_replacement':False}
(O/'local_changes.json').write_text(json.dumps(report,indent=2))
sc=bpy.context.scene;sc.cycles.samples=32;cam=sc.camera;cam.location=(-.034,-3,.902);cam.rotation_euler=(Vector((-.034,0,.902))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.10;sc.render.resolution_x=sc.render.resolution_y=1100
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Heroine_BoundaryLocal.blend'))
sc.render.filepath=str(O/'renders/eye.png');bpy.ops.render.render(write_still=True)
print('LOCAL_REPORT',json.dumps(report))
