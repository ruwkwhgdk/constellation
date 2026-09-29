"""First geometry/material detail pass from the maintained v002 blockout."""
import bpy, math, random, json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'Production/v001'; OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Blockout/v002/overgrown_hall_blockout.blend'))
bpy.context.preferences.filepaths.save_version=0
random.seed(34); scene=bpy.context.scene
scene.cycles.samples=32

def weather(mat,kind):
    mat['surface_detail']=kind
    nodes=mat.node_tree.nodes; links=mat.node_tree.links; bs=nodes.get('Principled BSDF')
    geo=nodes.new('ShaderNodeNewGeometry')
    noise=nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=1.2 if kind!='floor' else .8
    noise.inputs['Detail'].default_value=2
    links.new(geo.outputs['Position'],noise.inputs['Vector'])
    ramp=nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position=.34; ramp.color_ramp.elements[1].position=.61
    ramp.color_ramp.elements[0].color=(.10,.16,.16,1)
    ramp.color_ramp.elements[1].color=(.22,.29,.28,1) if kind!='floor' else (.20,.27,.25,1)
    links.new(noise.outputs['Fac'],ramp.inputs[0]); links.new(ramp.outputs[0],bs.inputs['Base Color'])
    bump=nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.28; bump.inputs['Distance'].default_value=.025
    links.new(noise.outputs['Fac'],bump.inputs['Height']); links.new(bump.outputs['Normal'],bs.inputs['Normal'])
    rough=nodes.new('ShaderNodeMapRange'); rough.inputs['To Min'].default_value=.32 if kind=='floor' else .7; rough.inputs['To Max'].default_value=.85
    links.new(noise.outputs['Fac'],rough.inputs['Value']); links.new(rough.outputs['Result'],bs.inputs['Roughness'])
for name in ['Proxy_Stone','Proxy_Trim']: weather(bpy.data.materials[name],'plaster')
weather(bpy.data.materials['Proxy_Floor'],'floor')
leaves=[bpy.data.materials['Proxy_Foliage_'+str(i)] for i in range(3)]
for m in leaves:
    m['two_sided']=True
    m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.72
wood=bpy.data.materials['Proxy_Bench']

def stem(name,a,b,r=.015):
    a,b=Vector(a),Vector(b)
    bpy.ops.mesh.primitive_cylinder_add(vertices=6,radius=r,depth=(b-a).length,location=(a+b)*.5)
    o=bpy.context.object; o.name=name; o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler(); o.data.materials.append(wood)
    return o

def leaf_mesh(name,leavespec):
    verts=[]; faces=[]
    for pos,length,width,angle,tilt in leavespec:
        p=Vector(pos); d=Vector((math.cos(angle)*math.cos(tilt),math.sin(angle)*math.cos(tilt),math.sin(tilt)))
        side=Vector((-math.sin(angle),math.cos(angle),0))
        pts=[p,p+d*length*.48-side*width*.5,p+d*length,p+d*length*.48+side*width*.5,p+d*length*.48+Vector((0,0,width*.15))]
        j=len(verts); verts.extend(pts); faces.extend([(j,j+1,j+4),(j+1,j+2,j+4),(j+2,j+3,j+4),(j+3,j,j+4)])
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(verts,[],faces); mesh.update()
    o=bpy.data.objects.new(name,mesh); scene.collection.objects.link(o)
    for m in leaves: mesh.materials.append(m)
    for p in mesh.polygons: p.material_index=random.randrange(3)
    return o

proxies=[o for o in scene.objects if '_PROXY_' in o.name and o.name[:2] in ['16','17','18','19']]
for idx,o in enumerate(proxies):
    c=o.location.copy(); sx,sy,sz=o.scale; cat=o.name[:2]; spec=[]
    if cat=='16':
        for j in range(32):
            p=c+Vector((random.uniform(-sx,sx),random.uniform(-sy,sy),-c.z+.035))
            spec.append((p,random.uniform(.18,.5),.022,random.random()*math.tau,random.uniform(.8,1.5)))
    elif cat=='18':
        stem('18_VineStem',c-Vector((0,0,sz)),c+Vector((0,0,sz)),.012)
        for j in range(38):
            p=c+Vector((random.uniform(-.18,.18),random.uniform(-.15,.15),random.uniform(-sz,sz)))
            spec.append((p,random.uniform(.12,.24),.13,random.random()*math.tau,random.uniform(-.6,.6)))
    else:
        tree=cat=='19'; count=1000 if tree else 170
        bottom=Vector((c.x,c.y,0 if tree else max(0,c.z-sz*.5)))
        top=c+Vector((0,0,sz*.45)); stem(cat+'_Trunk',bottom,top,.11 if tree else .025)
        for j in range(6):
            angle=j*math.tau/6; endpoint=c+Vector((math.cos(angle)*sx*.75,math.sin(angle)*sy*.75,random.uniform(-.2,.5)*sz))
            stem(cat+'_Branch',bottom.lerp(top,.7),endpoint,.035 if tree else .009)
        for j in range(count):
            theta=random.random()*math.tau; z=random.uniform(-1,1); r=math.sqrt(1-z*z)*random.uniform(.35,1)
            p=c+Vector((r*math.cos(theta)*sx,r*math.sin(theta)*sy,z*sz*.7))
            spec.append((p,random.uniform(.35,.65) if tree else random.uniform(.18,.35),.30 if tree else .18,random.random()*math.tau,random.uniform(-.5,.7)))
    leaf_mesh(cat+'_Foliage_'+str(idx),spec)
    bpy.data.objects.remove(o,do_unlink=True)

# Fine water normals remain subtle; still an opaque approximation for this pass.
w=bpy.data.materials['Proxy_Water']; w['surface_detail']='water'; bs=w.node_tree.nodes['Principled BSDF']
n=w.node_tree.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value=28; n.inputs['Roughness'].default_value=.35
geo=w.node_tree.nodes.new('ShaderNodeNewGeometry'); w.node_tree.links.new(geo.outputs['Position'],n.inputs['Vector'])
b=w.node_tree.nodes.new('ShaderNodeBump'); b.inputs['Strength'].default_value=.15; b.inputs['Distance'].default_value=.008
w.node_tree.links.new(n.outputs['Fac'],b.inputs['Height']); w.node_tree.links.new(b.outputs['Normal'],bs.inputs['Normal'])
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.60,.76,.81,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.7
scene.camera=bpy.data.objects['ReferenceCamera']
objects=[o for o in scene.objects if o.type=='MESH']
assert not any('_PROXY_' in o.name and o.name[:2] in ['16','17','18','19'] for o in objects)
assert all(math.isfinite(v) for o in objects for p in o.data.vertices for v in p.co)
report=dict(stage='detail_pass_01_not_final',mesh_objects=len(objects),triangles=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in objects),finite_vertices=True,foliage_proxy_replaced=True,bird_rig='pending',limitations=['procedural surface variation, not final authored peeling masks','opaque water approximation','no foliage wind or LOD','no runtime traversal validation'])
(OUT/'verification.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'overgrown_hall_detail.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT/'overgrown_hall_detail.glb'),export_format='GLB',export_cameras=True,export_lights=False)
scene.render.filepath=str(OUT/'reference.png'); bpy.ops.render.render(write_still=True)
scene.camera=bpy.data.objects['OverviewCamera']; scene.render.filepath=str(OUT/'overview.png'); bpy.ops.render.render(write_still=True)
print('HALL_DETAIL_PASS',json.dumps(report))
