"""Approved metric modules, convex collision, UVs and instance-only island cut."""
import bpy,bmesh,math,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'Production/v001';(O/'FBX').mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'Blockout/v001/entrance_blockout.blend'))
s=bpy.context.scene
def export_selected(path):
    selected=[o for o in bpy.context.selected_objects if o.type=='MESH']
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    # UE's retained FBX path expects baked centimetres, as in the maintained stair kit.
    for o in selected:
        for v in o.data.vertices:v.co*=100
        o.location*=100
        o.data.update()
    bpy.context.view_layer.update()
    s.unit_settings.scale_length=.01
    bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,mesh_smooth_type='FACE',bake_anim=False)
    for o in selected:
        for v in o.data.vertices:v.co/=100
        o.location/=100
        o.data.update()
    s.unit_settings.scale_length=1
    bpy.context.view_layer.update()
for o in list(s.objects):
    if o.type=='MESH' and (o.name.startswith(('PreviewGround','Guide_'))):bpy.data.objects.remove(o,do_unlink=True)
def box(name,loc,size,mat):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(mat);return o
def material(name,c):
    m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=.68;return m
steel=bpy.data.materials['Silver'];dark=bpy.data.materials['Trim'];cream=bpy.data.materials['Soffit'];stone=bpy.data.materials['Stone'];yellow=bpy.data.materials['Tactile']
grout=material('TileGrout',(.38,.44,.41));tile=material('WarmTile',(.69,.72,.63));glow=material('LampGlow',(.85,.88,.72))
gp=glow.node_tree.nodes.get('Principled BSDF');gp.inputs['Emission Color'].default_value=(.85,.88,.72,1);gp.inputs['Emission Strength'].default_value=1.5
# Visible tile faces have physical pitch. No noisy high-frequency normal map.
for side in [-1,1]:
    for row in range(13):
        z=-2.65+row*.28
        for col in range(30):
            y=-3.38+col*.24
            box('E09_Tile',(side*2.092,y,z),(.016,.233,.273),tile)
    for y in [-4.35,-.4,3.5]:box('E13_LampFace',(side*1.984,y,3.25),(.015,.24,.22),glow)
    for y in [-2.8,-.1,2.5]:box('E13_LowerMetalBox',(side*2.423,y,.55),(.09,1.25,.3),steel)
# Subtle stair nosings, flush enough not to form separate walking collision.
for i in range(18):
    box('E08_Nosing',(0,-3.5+i*.3+.025,.48-(i+1)*.16+.006),(4.2,.045,.012),steel)
for j in range(14):
    for k in range(3):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=4,radius=.018,location=(-1.95+j*.3,-3.90+k*.1,.505));o=bpy.context.object;o.name='E07_TactileStud';o.scale.z=.35;o.data.materials.append(yellow)
# Station sign texture: exact authored text, not AI lettering.
sign=material('StationSign',(.1,.15,.16));img=bpy.data.images.load(str(O/'textures/T_SE_StationSign.png'))
n=sign.node_tree.nodes.new('ShaderNodeTexImage');n.image=img;sign.node_tree.links.new(n.outputs['Color'],sign.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
for o in list(s.objects):
    if o.name.startswith('E12_'):bpy.data.objects.remove(o,do_unlink=True)
def signplane(name,verts):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],[(0,1,2,3)]);me.update();o=bpy.data.objects.new(name,me);s.collection.objects.link(o);me.materials.append(sign)
    uv=me.uv_layers.new(name='UVMap')
    for li,xy in zip(me.polygons[0].loop_indices,[(0,0),(1,0),(1,1),(0,1)]):uv.data[li].uv=xy
signplane('E12_FrontSign',[(-2.5,-5.411,3.82),(2.5,-5.411,3.82),(2.5,-5.411,4.08),(-2.5,-5.411,4.08)])
signplane('E12_SideSign',[(-2.852,-.8,3.82),(-2.852,-4.8,3.82),(-2.852,-4.8,4.08),(-2.852,-.8,4.08)])
# Gentle broad color variation, never baked light/shadow.
spec={}
for m in bpy.data.materials:
    if not m.use_nodes:continue
    p=m.node_tree.nodes.get('Principled BSDF')
    if not p:continue
    c=list(p.inputs['Base Color'].default_value)[:3]
    spec[m.name]=dict(color=c,roughness=p.inputs['Roughness'].default_value,metallic=.3 if m.name=='Silver' else 0,glass=m.name=='Glass_placeholder',texture='T_SE_StationSign.png' if m==sign else None,emission=1.5 if m==glow else 0)
    if m.name in ['Stone','Soffit','WarmTile']:
        tex=m.node_tree.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=.4;tex.inputs['Detail'].default_value=1
        ramp=m.node_tree.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=tuple(v*.96 for v in c)+(1,);ramp.color_ramp.elements[1].color=tuple(min(1,v*1.01) for v in c)+(1,)
        m.node_tree.links.new(tex.outputs['Fac'],ramp.inputs[0]);m.node_tree.links.new(ramp.outputs[0],p.inputs['Base Color'])
spec_path=O/'materials.json';spec_path.write_text(json.dumps(spec,indent=2),encoding='utf-8')
meshes=[];manifest=[]
for i in range(1,14):
    name='SM_SE_E%02d'%i;items=[o for o in s.objects if o.type=='MESH' and o.name.startswith('E%02d_'%i)];assert items,name
    coll=[]
    if i not in [7,8,10,12,13]:
        # Structural boxes only; no dense decorative tile hulls.
        for o in items:
            if 'Tile' in o.name:continue
            corners=[o.matrix_world@Vector(v) for v in o.bound_box];lo=Vector(tuple(min(v[j] for v in corners) for j in range(3)));hi=Vector(tuple(max(v[j] for v in corners) for j in range(3)))
            c=box('UCX_'+name+'_%03d'%len(coll),(lo+hi)/2,hi-lo,dark);c.hide_render=True;coll.append(c)
    if i==8:
        # Smooth continuous ramp (step outer edges), preserves visual 16cm risers.
        vs=[(-2.1,-3.5,.48),(2.1,-3.5,.48),(2.1,1.9,-2.4),(-2.1,1.9,-2.4),(-2.1,-3.5,-2.68),(2.1,-3.5,-2.68),(2.1,1.9,-2.68),(-2.1,1.9,-2.68)]
        me=bpy.data.meshes.new('Ramp');me.from_pydata(vs,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);me.update();c=bpy.data.objects.new('UCX_'+name+'_000',me);s.collection.objects.link(c);c.hide_render=True;coll.append(c)
        c=box('UCX_'+name+'_001',(0,2.8,-2.58),(4.2,1.8,.36),dark);c.hide_render=True;coll.append(c)
    bpy.ops.object.select_all(action='DESELECT')
    for o in items:
        o.select_set(True);bpy.context.view_layer.objects.active=o
        for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.context.view_layer.objects.active=items[0];bpy.ops.object.join();o=bpy.context.object;o.name=name
    s.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    if i!=12:
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.015);bpy.ops.object.mode_set(mode='OBJECT')
    o.data.calc_loop_triangles();tris=len(o.data.loop_triangles)
    for c in coll:c.select_set(True)
    export_selected(O/'FBX'/(name+'.fbx'))
    manifest.append(dict(name=name,id='E%02d'%i,triangles=tris,collision_hulls=len(coll),dimensions_cm=[v*100 for v in o.dimensions]))
    meshes.append(o)
    for c in coll:c.hide_viewport=True
# Island geometry is obtained in native world coordinates, avoiding transform guessing.
src=json.loads((R/'Design/island_world_mesh.json').read_text());vs=[((x-3900)/100,-(y+19500)/100,(z-10000)/100) for x,y,z in src['vertices']]
faces=[src['triangles'][i:i+3] for i in range(0,len(src['triangles']),3)]
me=bpy.data.meshes.new('IslandSource');me.from_pydata(vs,[],faces);me.update();island=bpy.data.objects.new('SM_SE_IslandWithStairwell',me);s.collection.objects.link(island)
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
cutter=box('TemporaryShaftCut',(0,.1,-.4),(4.24,7.24,5.1),dark)
bpy.context.view_layer.objects.active=island;mod=island.modifiers.new('ClosedShaft','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
bm=bmesh.new();bm.from_mesh(me);boundary=sum(not e.is_manifold for e in bm.edges);bm.free();assert boundary==0,('island open boundary',boundary)
assert len(me.polygons)>len(faces)/2
me.calc_loop_triangles();bpy.ops.object.select_all(action='DESELECT');island.select_set(True);bpy.context.view_layer.objects.active=island
export_selected(O/'FBX/SM_SE_IslandWithStairwell.fbx')
island.hide_render=True;island.hide_viewport=True
(O/'manifest.json').write_text(json.dumps(dict(assets=manifest,island=dict(triangles=len(me.loop_triangles),non_manifold_edges=boundary,pivot_world=[3900,-19500,10000],collision='use_complex_as_simple on unique static island only'),scope='accepted entrance modules; not runtime play verified'),indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(O/'entrance_kit.blend'))
s.cycles.samples=32;s.render.resolution_x=1600;s.render.resolution_y=1100
s.camera=bpy.data.objects['exterior'];s.render.filepath=str(O/'exterior.png');bpy.ops.render.render(write_still=True)
print('SUBWAY_PRODUCTION_OK',sum(r['triangles'] for r in manifest))
