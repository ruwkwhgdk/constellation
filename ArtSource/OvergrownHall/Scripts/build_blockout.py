"""Approved hall geometry study. Run through tools/run-blender.ps1 only."""
import bpy, math, random, json
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Blockout/v002'
OUT.mkdir(parents=True, exist_ok=True)
random.seed(17)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1
bpy.context.preferences.filepaths.save_version = 0
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.cycles.use_denoising = True
scene.render.resolution_x = 1200
scene.render.resolution_y = 640
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.view_settings.view_transform = 'AgX'
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.29,.44,.51,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .45

def material(name, color, rough=.7, metal=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough
    p.inputs['Metallic'].default_value=metal
    return m
stone=material('Proxy_Stone',(.14,.23,.25))
edge=material('Proxy_Trim',(.23,.32,.32))
iron=material('Proxy_Metal',(.055,.095,.095),.4,.6)
wood=material('Proxy_Bench',(.22,.27,.22))
floor=material('Proxy_Floor',(.22,.31,.30))
water=material('Proxy_Water',(.07,.27,.29),.10,.65)
leaf=[material('Proxy_Foliage_'+str(i),c) for i,c in enumerate([(.10,.24,.08),(.22,.38,.10),(.32,.43,.13)])]

def box(name,loc,dim,mat=stone):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object; o.name=name; o.dimensions=dim
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(mat)
    return o

def beam(name,a,b,width=.12,depth=None,mat=iron):
    a,b=Vector(a),Vector(b)
    o=box(name,(a+b)*.5,(width,depth or width,(b-a).length),mat)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return o

def arch(name,cx,y,spring,radius,thick=.22,depth=.25,mat=edge,side=False):
    # Ring segments have actual depth; opening is geometry, not a dark decal.
    for i in range(16):
        a,b=math.pi*i/16,math.pi*(i+1)/16
        verts=[]
        for d in [-depth/2,depth/2]:
            for r,t in [(radius,a),(radius,b),(radius+thick,b),(radius+thick,a)]:
                x,z=r*math.cos(t),spring+r*math.sin(t)
                verts.append((cx+d,y+x,z) if side else (cx+x,y+d,z))
        mesh=bpy.data.meshes.new(name+'_seg'); mesh.from_pydata(verts,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
        mesh.update(); o=bpy.data.objects.new(name+'_%02d'%i,mesh); scene.collection.objects.link(o); mesh.materials.append(mat)

# The dimensional proposal remains visible in the source and report.
box('13_ContinuousFloor',(0,10,-.15),(16,20,.3),floor)
box('13_RearPlatform',(0,17,.10),(15.6,5,.2),floor)
for side in [-1,1]:
    x=side*7.6
    box('05_SidePlinth_'+str(side),(x,10,.3),(.45,20,.6),stone)
    box('09_SideBand_'+str(side),(x,10,8),(.5,20,.4),edge)
    for j,y in enumerate([2,6,10,14,18]):
        tag=f'{side}_{j}'
        box('01_Base_'+tag,(x,y,.6),(.8,.85,1.2),edge)
        box('02_Shaft_'+tag,(x,y,5.1),(.58,.65,9),stone)
        box('03_Capital_'+tag,(x,y,9.6),(.95,1,.35),edge)
        box('02_Upper_'+tag,(x,y,10.7),(.55,.65,2),stone)
        if j<4:
            arch('04_SideArch_'+tag,x,y+2,5.5,1.65,.22,.4,stone,True)
            for dy in [.2,3.8]:
                box('04_Jamb_'+tag,(x,y+dy,3),(.4,.22,5.4),stone)
        beam('11_CutSideBeam_'+tag,(x,y,8.8),(x-side*1.5,y,9.3),.24,.3,edge)
    for z in [.85,1.15]:
        beam('25_Rail_'+str(side),(x,2,z),(x,6,z),.045,mat=iron)
    for y in [2,4,6]:
        beam('25_Post_'+str(side),(x,y,.5),(x,y,1.2),.05,mat=iron)

# Rear wall with a true central small arched opening.
for x in [-4.2,4.2]:
    box('05_RearLower',(x,19.65,1.4),(7.2,.45,2.8),stone)
arch('12_RearSmallArch',0,19.65,1.35,.6,.25,.5,edge)
for x in [-.73,.73]: box('12_Jamb',(x,19.65,.67),(.26,.5,1.35),edge)
box('09_RearSill',(0,19.65,2.9),(16,.65,.25),edge)
box('09_RearBand',(0,19.65,7.45),(16,.65,.45),stone)
for x in [-7.6,-4,0,4,7.6]:
    box('02_RearPier',(x,19.65,6.6),(.4,.45,7.8),stone)
for idx,x in enumerate([-5.8,-2,2,5.8]):
    w=3.25 if abs(x)>4 else 3.55
    for dx in [-w/2,w/2]:
        box('06_Frame',(x+dx,19.6,5.15),(.09,.14,4.3),iron)
        box('07_Jamb',(x+dx,19.6,8.7),(.09,.14,2.1),iron)
    for z in [3,4.1,6.1,7.2,7.7,8.75,9.65]:
        box('08_Horizontal',(x,19.6,z),(w,.10,.065),iron)
    for dx in [-w/4,0,w/4]:
        box('08_Mullion',(x+dx,19.6,6.4),(.065,.10,6.8),iron)
    arch('07_Arch_'+str(idx),x,19.6,9.7,w/2,.085,.14,iron)

for y in [6,12,18]:
    for side in [-1,1]:
        beam('10_Rafter',(side*7.6,y,10),(0,y,12),.18,.22)
        beam('10_Brace',(side*7.6,y,9.8),(side*3,y,11.2),.12)
    beam('10_Tie',(-7.6,y,10),(7.6,y,10),.14)
for x in [-6,-3,0,3,6]:
    beam('10_Purlin',(x,1,12-abs(x)*2/7.6),(x,20,12-abs(x)*2/7.6),.13)
for x,y,sx,sy in [(-5,4,4,5),(-5,12,3,3),(5,7,3,4),(0,18,3,2)]:
    o=box('26_RoofFragment',(x,y,12-abs(x)*2/7.6),(sx,sy,.12),stone)
    o.rotation_euler.y=math.copysign(math.atan(2/7.6),x)

# Actual 180 cm bench: kept independent of architecture scaling.
bx,by=-1.7,10
for x in [-.72,.72]:
    for y in [-.23,.23]: box('14_Leg',(bx+x,by+y,.22),(.055,.055,.44),iron)
    beam('14_BackSupport',(bx+x,by+.27,.1),(bx+x,by+.35,.91),.05)
for y in [-.22,-.075,.075,.22]: box('14_SeatSlat',(bx,by+y,.45),(1.8,.13,.04),wood)
for z in [.61,.74,.87]: box('14_BackSlat',(bx,by+.31,z),(1.8,.055,.10),wood)

# Irregular shallow water boundary; flat collision floor remains underneath.
verts=[(0,6,.022)]
for i in range(48):
    t=2*math.pi*i/48; r=1+random.uniform(-.12,.12)
    verts.append((7.15*math.cos(t)*r,6+4.2*math.sin(t)*r,.022))
mesh=bpy.data.meshes.new('21_WaterBoundary'); mesh.from_pydata(verts,[],[(0,1+i,1+(i+1)%48) for i in range(48)]); mesh.update()
o=bpy.data.objects.new('21_PROXY_Water',mesh); scene.collection.objects.link(o); mesh.materials.append(water)
for i in range(16):
    x,y=random.uniform(-7,7),random.uniform(3,12)
    o=box('13_DryIsland',(x,y,.02),(random.uniform(.3,1.2),random.uniform(.25,.75),.08),floor); o.rotation_euler.z=random.uniform(-.3,.3)

def mass(name,loc,scale):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale; o.data.materials.append(random.choice(leaf))
for i in range(55):
    x=random.uniform(-7.2,7.2); y=random.uniform(17,20); h=random.uniform(.4,1.4)
    mass('17_PROXY_Shrub',(x,y,h*.5),(.6,.55,h))
for side in [-1,1]:
    for i in range(24):
        y=random.uniform(2,19); h=random.uniform(.15,.6)
        mass('16_PROXY_Grass',(side*random.uniform(6.5,7.4),y,h*.4),(.35,.35,h))
    for y in [6,14,18]:
        for z in [3,4.5,6,7.5]: mass('18_PROXY_Vine',(side*7.25,y,z),(.3,.35,.8))
for i in range(18):
    mass('19_PROXY_Tree',(random.uniform(-12,12),random.uniform(23,30),random.uniform(2,5)),(2.3,2.3,3.1))

def camera(name,loc,target,lens):
    bpy.ops.object.camera_add(location=loc); o=bpy.context.object; o.name=name
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler(); o.data.lens=lens; o.data.clip_end=200
    return o
cam=camera('ReferenceCamera',(0,2,1.55),(0,17,3.15),22)
overview=camera('OverviewCamera',(20,-10,18),(0,11,4),37)
bpy.ops.object.light_add(type='SUN',location=(8,12,15)); sun=bpy.context.object; sun.name='23_Sun'
sun.rotation_euler=Vector((-0.6,-.45,-1)).to_track_quat('-Z','Y').to_euler(); sun.data.energy=3; sun.data.angle=.07; sun.data.color=(1,.85,.61)
bpy.ops.object.light_add(type='AREA',location=(0,19,7)); lamp=bpy.context.object
lamp.rotation_euler=Vector((0,-1,-.2)).to_track_quat('-Z','Y').to_euler(); lamp.data.energy=1800; lamp.data.shape='RECTANGLE'; lamp.data.size=12; lamp.data.size_y=7

# Narrow the rear glazed field without scaling the bench or the hall.
for o in list(scene.objects):
    if o.type=='MESH' and (o.name.startswith(('06_','07_','08_','02_RearPier'))):
        o.location.x *= .84
        for v in o.data.vertices: v.co.x *= .84
for x in [-7.0,7.0]: box('05_RearSidePanel',(x,19.65,7),(1.4,.45,8),stone)
box('13_BenchDryPatch',(bx,by,.015),(2.15,.95,.03),floor)
objects=[o for o in scene.objects if o.type=='MESH']
assert all(math.isfinite(v) for o in objects for p in o.data.vertices for v in p.co)
assert abs(bpy.data.objects['14_SeatSlat'].dimensions.x-1.8)<1e-5
report={'stage':'blockout_not_final_assets','units':'meters','hall':[16,20,12],'bench_width':1.8,'mesh_objects':len(objects),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in objects),'finite_vertices':True,'human_in_scene':False,'bird_rig':'not_created_yet','unreal_playtest':'not_run','temporary':['foliage masses','water','materials','lighting'],'new_modules':[25,26]}
(OUT/'verification.json').write_text(json.dumps(report,indent=2))
scene.camera=cam
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'overgrown_hall_blockout.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT/'overgrown_hall_blockout.glb'),export_format='GLB',export_cameras=True,export_lights=False)
scene.render.filepath=str(OUT/'reference.png'); bpy.ops.render.render(write_still=True)
scene.camera=overview; scene.render.filepath=str(OUT/'overview.png'); bpy.ops.render.render(write_still=True)
print('HALL_BLOCKOUT_COMPLETE',json.dumps(report))
