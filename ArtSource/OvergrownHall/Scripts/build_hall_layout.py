"""Reference composition pass; original kit and production scene are preserved."""
import bpy,json,math,random
from pathlib import Path
from mathutils import Vector
BASE=Path(__file__).resolve().parents[1]; OUT=BASE/'Scene/v001'; OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE/'Production/v001/overgrown_hall_detail.blend'))
bpy.context.preferences.filepaths.save_version=0; scene=bpy.context.scene
random.seed(925)
def world_edit(o,fn):
    inv=o.matrix_world.inverted()
    for v in o.data.vertices: v.co=inv@fn(o.matrix_world@v.co)
# Compress only the glazed rear field; retain the full structural exterior.
for o in list(scene.objects):
    if o.type!='MESH': continue
    if o.name.startswith(('06_','07_','08_','02_RearPier')):
        world_edit(o,lambda p:Vector((p.x*.78,p.y,p.z)))
    if o.name.startswith(('01_','02_Shaft','02_Upper','03_','04_','05_Side','09_Side','11_','25_')):
        world_edit(o,lambda p:Vector((p.x-math.copysign(1.25,p.x),p.y,p.z)))
    if o.name.startswith('13_DryIsland'):
        # Broken slabs should sit in shallow water, not float above it.
        o.location.z-=.035
    if o.name.startswith('21_'): o.location.y+=1.0
    if o.name.startswith('14_'):
        o.location.x+=.50; o.location.y+=.20
    if o.name.startswith('13_BenchDryPatch'):
        o.location.x+=.50; o.location.y+=.20
# Cover the newly narrowed glazing sides with actual solid wall returns.
stone=bpy.data.materials['Proxy_Stone']
for side in [-1,1]:
    bpy.ops.mesh.primitive_cube_add(size=1,location=(side*5.95,19.65,6.95))
    o=bpy.context.object; o.name='05_InnerRearReturn'; o.dimensions=(1.45,.45,8.0); o.data.materials.append(stone)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
# Arrange existing foliage clumps in asymmetric layers, preserving the center route.
shrubs=[o for o in scene.objects if o.type=='MESH' and o.name.startswith('17_Foliage')]
for i,src in enumerate(shrubs[:14]):
    o=src.copy(); o.data=src.data.copy(); scene.collection.objects.link(o); o.name='17_PlacedShrub_%02d'%i
    # Leaf meshes use world-space vertices with origin zero.
    center=sum((v.co for v in o.data.vertices),Vector())/len(o.data.vertices)
    side=-1 if i<8 else 1
    target=Vector((side*random.uniform(3.4,5.8),random.uniform(10.5,16.8),random.uniform(.45,.8)))
    for v in o.data.vertices: v.co=target+(v.co-center)*random.uniform(.96,1.04)
for o in list(scene.objects):
    if o.type=='MESH' and o.name.startswith('18_'):
        world_edit(o,lambda p:Vector((p.x-math.copysign(1.25,p.x),p.y,p.z)))
# Break selected arch segments and roof ties instead of repeating complete bays.
for o in list(scene.objects):
    if o.name.startswith('04_SideArch_') and any(tag in o.name for tag in ['-1_1_','1_2_']):
        try: segment=int(o.name.rsplit('_',1)[-1].split('.')[0])
        except ValueError: continue
        if segment in [5,6,7,8,9]: bpy.data.objects.remove(o,do_unlink=True)
    elif o.name.startswith('10_Tie'):
        world_edit(o,lambda p:Vector((p.x,p.y,p.z+.10*math.sin(p.x*2))))
# A ground apron and exterior planting close the empty horizon through the arches.
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,17,-.4))
o=bpy.context.object; o.name='13_ExteriorGround'; o.dimensions=(65,70,.3); o.data.materials.append(bpy.data.materials['Proxy_Floor'])
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
trees=[o for o in scene.objects if o.type=='MESH' and o.name.startswith('19_Foliage')]
for i,src in enumerate(trees[:12]):
    o=src.copy(); o.data=src.data.copy(); scene.collection.objects.link(o); o.name='19_ExteriorTree_%02d'%i
    center=sum((v.co for v in o.data.vertices),Vector())/len(o.data.vertices)
    target=Vector(((-1 if i<6 else 1)*random.uniform(10,14),random.uniform(3,23),random.uniform(3,5)))
    for v in o.data.vertices: v.co=target+(v.co-center)*1.35
# Keep foreground water low, with broad reflection uninterrupted by raised slabs.
cam=bpy.data.objects['ReferenceCamera']; cam.location=(0,2,1.55)
target=Vector((0,17,4.0)); cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
scene.camera=cam; scene.cycles.samples=24
scene.render.filepath=str(OUT/'reference.png')
report=dict(stage='layout_pass_01',source='Production/v001',bench_width_cm=180,bench_center_cm=[-120,1020,0],camera_cm=[0,200,155],camera_target_cm=[0,1700,400],camera_lens_mm=22,changes=['rear glazed field narrowed 22 percent','side architectural rows inward 125cm','bench shifted 50cm right and20cm rearward','14 shrub clumps around sides','dry slabs lowered3.5cm'],human_in_comparison=False,playtest='pending')
(OUT/'layout.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'overgrown_hall_layout.blend'))
bpy.ops.render.render(write_still=True)
