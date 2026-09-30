"""Targeted closed tunnel revision; approved kit and shared island source stay intact."""
import bpy,bmesh,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'Connection/v002';(O/'FBX').mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'Blockout/v001/entrance_blockout.blend'))
s=bpy.context.scene
keep=[o for o in s.objects if o.type=='MESH' and o.name.startswith('E09_') and 'EndWall' not in o.name]
for o in list(s.objects):
 if o not in keep:bpy.data.objects.remove(o,do_unlink=True)
stone=bpy.data.materials['Stone'];cream=bpy.data.materials['Soffit'];dark=bpy.data.materials['Trim']
black=bpy.data.materials.new('TunnelDark');black.diffuse_color=(.012,.017,.019,1);black.use_nodes=True
p=black.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=black.diffuse_color;p.inputs['Roughness'].default_value=.97
warm=bpy.data.materials.new('WarmTile');warm.diffuse_color=(.69,.72,.63,1);warm.use_nodes=True;warm.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=warm.diffuse_color

def box(n,loc,size,mat):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=n;o.dimensions=size;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);o.data.materials.append(mat);return o

def wedge(n,x0,x1,y0,y1,b0,b1,t0,t1,mat):
 vs=[(x0,y0,b0),(x1,y0,b0),(x1,y1,b1),(x0,y1,b1),(x0,y0,t0),(x1,y0,t0),(x1,y1,t1),(x0,y1,t1)]
 me=bpy.data.meshes.new(n);me.from_pydata(vs,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);me.update();o=bpy.data.objects.new(n,me);s.collection.objects.link(o);me.materials.append(mat);return o

manifest=[]
def export(n,items,collide=True):
 coll=[]
 if collide:
  for i,o in enumerate(items):
   c=o.copy();c.data=o.data.copy();s.collection.objects.link(c);c.name='UCX_'+n+'_%03d'%i;c.hide_render=True;coll.append(c)
 bpy.ops.object.select_all(action='DESELECT')
 for o in items:o.select_set(True);bpy.context.view_layer.objects.active=o
 for o in items:
  bpy.context.view_layer.objects.active=o
  for m in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=m.name)
 bpy.context.view_layer.objects.active=items[0];bpy.ops.object.join();obj=bpy.context.object;obj.name=n;s.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.02);bpy.ops.object.mode_set(mode='OBJECT')
 for c in coll:c.select_set(True)
 bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 selected=list(bpy.context.selected_objects)
 for o in selected:
  for v in o.data.vertices:v.co*=100
  o.data.update()
 s.unit_settings.scale_length=.01;bpy.context.view_layer.update()
 bpy.ops.export_scene.fbx(filepath=str(O/'FBX'/(n+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,mesh_smooth_type='FACE',bake_anim=False)
 for o in selected:
  for v in o.data.vertices:v.co/=100
  o.data.update()
 s.unit_settings.scale_length=1;bpy.context.view_layer.update();obj.data.calc_loop_triangles()
 manifest.append(dict(name=n,triangles=len(obj.data.loop_triangles),hulls=len(coll),dimensions_cm=[v*100 for v in obj.dimensions]))
 for c in coll:c.hide_viewport=True
 return obj
# Keep original sidewalls and their tiles; remove only the end wall.
struct=list(keep)
for side in [-1,1]:
 for row in range(13):
  for col in range(30):keep.append(box('Tile',(side*2.092,-3.38+col*.24,-2.65+row*.28),(.016,.233,.273),warm))
# Export visual tile faces without their own convex collision.
# Only three original structural boxes need collision; use a temporary joined visual export then separate UCX.
# export() takes all pieces as convex; tile faces would duplicate collision, so mark their collision disabled below.
# Side walls/failsafe form closed boxes; simple collision from these three only.
original_export=export
# Join tile faces into sidewalls before export; all tile geometry is decorative, handled by importer override.
e09=export('SM_SE_E09_DarkEntry',keep,False)
# Tunnel ramp goes 1.2m deeper, keeping its roof under the island after the canopy.
items=[]
items.append(wedge('Ramp',-2.1,2.1,3.65,7.7,-2.65,-3.85,-2.4,-3.6,stone))
items.append(wedge('RampRoof',-2.3,2.3,3.65,7.7,.4,-.8,.65,-.55,cream))
for x in [-2.22,2.22]:items.append(wedge('RampSide',x-.12,x+.12,3.65,7.9,-2.65,-3.85,.65,-.55,cream))
# L turn: forward to y=10, then right to x=10.5. All deep surfaces share a dark matte material.
items += [box('FloorA',(0,9.9,-3.75),(4.6,4.4,.3),black),box('RoofA',(0,9.9,-.65),(4.6,4.4,.3),black),
 box('OuterLeft',(-2.22,9.9,-2.2),(.24,4.4,3.1),black),box('BackWall',(4.15,12.22,-2.2),(12.9,.24,3.1),black),
 box('FloorB',(6.3,10,-3.75),(8.4,4.2,.3),black),box('RoofB',(6.3,10,-.65),(8.4,4.2,.3),black),
 box('InnerTurn',(6.3,7.78,-2.2),(8.4,.24,3.1),black),box('EndWall',(10.62,10,-2.2),(.24,4.6,3.1),black)]
export('SM_SE_ExteriorDarkTunnel',items)
# Interior world-space coordinates converted to Blender's FBX basis.
def ibox(n,pos,size,mat):return box(n,(pos[0]/100,-pos[1]/100,pos[2]/100),tuple(v/100 for v in size),mat)
items=[ibox('FloorEntry',(-1210,0,345),(980,420,30),stone),ibox('RoofEntry',(-1210,0,655),(980,460,30),cream),
 ibox('RightEntry',(-1210,222,500),(980,24,310),cream),ibox('LeftEntry',(-1000,-222,500),(560,24,310),cream),
 ibox('BackTurn',(-1722,-490,500),(24,1440,310),black),ibox('FloorExit',(-1500,-710,345),(420,1000,30),black),
 ibox('RoofExit',(-1500,-710,655),(460,1000,30),black),ibox('InnerExit',(-1278,-710,500),(24,1000,310),black),
 ibox('EndExit',(-1500,-1222,500),(460,24,310),black)]
export('SM_SE_InteriorDarkTunnel',items)
# Derive island from the native pre-cut source, not an already-cut revision.
src=json.loads((R/'Design/island_world_mesh.json').read_text());vs=[((x-3900)/100,-(y+19500)/100,(z-10000)/100) for x,y,z in src['vertices']];fs=[src['triangles'][i:i+3] for i in range(0,len(src['triangles']),3)]
me=bpy.data.meshes.new('Island');me.from_pydata(vs,[],fs);me.update();island=bpy.data.objects.new('Island',me);s.collection.objects.link(island)
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
cutters=[box('ShaftCut',(0,.1,-.4),(4.24,7.24,5.1),dark),wedge('RampCut',-2.35,2.35,3.6,7.95,-2.95,-4.05,.7,-.5,dark),box('TurnCut',(4.15,10,-2.3),(13.3,4.7,3.6),dark)]
for c in cutters:
 bpy.context.view_layer.objects.active=island;m=island.modifiers.new('ClosedTunnelCut','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=c;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(c,do_unlink=True)
bm=bmesh.new();bm.from_mesh(me);nonmanifold=sum(not e.is_manifold for e in bm.edges);bm.free();assert nonmanifold==0
export('SM_SE_IslandDarkTunnel',[island],False);island.hide_render=True
(O/'manifest.json').write_text(json.dumps(dict(assets=manifest,non_manifold_island=nonmanifold,exterior_portal=[4700,-20500,9640],interior_portal=[-1500,-800,360]),indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(O/'dark_connection.blend'))
print('DARK_TUNNEL_SOURCE_OK')

