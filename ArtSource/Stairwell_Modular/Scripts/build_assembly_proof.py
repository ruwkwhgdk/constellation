"""Disposable-size assembly proof, not final game meshes. Run through run-blender.ps1."""
import bpy, math, json, os
from pathlib import Path
from mathutils import Vector, Quaternion

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Assembly'
OUT.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.name = 'Assembly_Proof'
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1
report = {'units': 'cm', 'purpose': 'Geometric proof only; no Unreal playtest or production mesh approval',
          'joints': [], 'tile_pitch_cm': 30, 'grout_cm': 0.3, 'rail_diameter_cm': 4,
          'rail_vertical_spacing_cm': 25, 'bend_radius_cm': 8}

def mat(name, color, metal=0, rough=.6):
    m = bpy.data.materials.new(name); m.diffuse_color = (*color, 1); m.use_nodes = True
    p = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Metallic'].default_value = metal; p.inputs['Roughness'].default_value = rough
    return m
concrete = mat('Concrete_Blockout', (.32,.36,.38))
tile = mat('Tile_30cm', (.57,.62,.62))
yellow = mat('Tactile_30cm', (.75,.57,.08))
steel = mat('Shared_Rail_Steel', (.40,.47,.51), .8, .28)
trim = mat('Dark_Skirting', (.06,.08,.09))
blue = mat('Transition_Highlight', (.05,.48,.64), .5, .27)
white = mat('Labels', (.8,.87,.9))

def box(name, loc, size, material, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o=bpy.context.object; o.name=name; o.dimensions=size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material)
    if bevel:
        mod=o.modifiers.new('Small_Edge','BEVEL'); mod.width=bevel; mod.segments=2
    return o

def text(name, body, loc, size=.1):
    d=bpy.data.curves.new(name,'FONT'); d.body=body; d.size=size; d.extrude=.0002
    o=bpy.data.objects.new(name,d); scene.collection.objects.link(o); o.location=loc
    d.materials.append(white); return o

def tube(name, pts, tans, material=steel, radius=.02):
    vs=[]; faces=[]; rings=16
    for p,t in zip(pts,tans):
        p=Vector(p); t=Vector(t).normalized()
        ref=Vector((0,0,1)) if abs(t.z)<.95 else Vector((0,1,0))
        u=t.cross(ref).normalized(); v=t.cross(u).normalized()
        for j in range(rings):
            a=2*math.pi*j/rings; vs.append(p+radius*(u*math.cos(a)+v*math.sin(a)))
    for i in range(len(pts)-1):
        for j in range(rings):
            a=i*rings+j; b=i*rings+(j+1)%rings
            faces.append((a,b,b+rings,a+rings))
    me=bpy.data.meshes.new(name); me.from_pydata(vs,[],faces); me.update()
    o=bpy.data.objects.new(name,me); scene.collection.objects.link(o); me.materials.append(material)
    for poly in me.polygons: poly.use_smooth=True
    return o

def straight(a,b):
    a,b=Vector(a),Vector(b); t=(b-a).normalized()
    return [a,b],[t,t]

def rounded_path(points, radius=.08):
    points=list(map(Vector,points)); cursor=points[0]; segments=[]
    for i in range(1,len(points)-1):
        p=points[i]; a=(p-points[i-1]).normalized(); b=(points[i+1]-p).normalized()
        theta=a.angle(b); dist=radius*math.tan(theta/2)
        assert dist < min((p-points[i-1]).length,(points[i+1]-p).length)/2
        start=p-a*dist; end=p+b*dist; axis=a.cross(b).normalized()
        normal=(b-a*math.cos(theta)).normalized(); center=start+normal*radius
        segments.append(('Straight',*straight(cursor,start)))
        n=max(8,math.ceil(theta/math.radians(3)))
        pts=[]; tans=[]
        for j in range(n+1):
            q=Quaternion(axis,theta*j/n); rad=q@(start-center)
            pts.append(center+rad); tans.append(axis.cross(rad).normalized())
        pts[0]=start; pts[-1]=end; tans[0]=a; tans[-1]=b
        segments.append(('Bend',pts,tans)); cursor=end
    segments.append(('Straight',*straight(cursor,points[-1])))
    return segments

def ring_center(o, end):
    vs=o.data.vertices; items=list(vs[-16:]) if end else list(vs[:16])
    return sum((v.co for v in items),Vector())/16

def ring_normal(o,end):
    vs=o.data.vertices; k=len(vs)-16 if end else 0
    return (vs[k+4].co-vs[k].co).cross(vs[k+8].co-vs[k].co).normalized()

def build_chain(name,segments):
    objects=[]
    for i,(kind,pts,tans) in enumerate(segments):
        o=tube(f'{name}_{i:02d}_{kind}',pts,tans,blue if kind=='Bend' else steel)
        o['proof_component']=kind; objects.append(o)
    for a,b in zip(objects,objects[1:]):
        gap=(ring_center(a,True)-ring_center(b,False)).length*100
        angle=math.degrees(ring_normal(a,True).angle(ring_normal(b,False)))
        report['joints'].append({'a':a.name,'b':b.name,'gap_cm':gap,'ring_plane_angle_deg':angle})
        assert gap <= .1 and angle <= .5, (gap,angle)
    return objects

def bracket(name, x,y,z,wall_y):
    # Intersect the rail underside: previous 3.5cm offset left a 5mm air gap.
    a=Vector((x,y,z-.015)); b=Vector((x,wall_y,z-.015))
    tube(name,*straight(a,b),radius=.01)
    return box(name+'_WallPlate',(x,wall_y,z-.015),(.06,.008,.07),steel,.004)

def floor_tiles(name, x0,y0,nx,ny,z,material):
    objects=[]
    box(name+'_Bed',(x0+.15*nx,y0+.15*ny,z-.035),(.3*nx,.3*ny,.07),concrete)
    for ix in range(nx):
        for iy in range(ny):
            o=box(f'{name}_{ix}_{iy}',(x0+.15+.3*ix,y0+.15+.3*iy,z+.006),(.297,.297,.012),material,.001)
            objects.append(o)
    return objects

# Six-step staircase and a 180cm-deep landing. Positive X is uphill.
for i in range(6):
    top=.15*(i+1)
    box(f'01_Step_{i+1}',(.15+.3*i,0,top/2),(.3,1.4,top),concrete,.003)
    box(f'16_Nosing_{i+1}',(.018+.3*i,0,top+.003),(.035,1.4,.006),trim,.001)
box('02_Landing',(2.7,0,.85),(1.8,1.4,.1),concrete)
# Fit a common 30cm pitch with 10cm edge strips, without stretching central tiles.
for ix in range(6):
    for iy in range(6):
        ylo=[-.7,-.6,-.3,0,.3,.6][iy]; widths=[.1,.3,.3,.3,.3,.1]
        box(f'Landing_Tile_{ix}_{iy}',(1.95+.3*ix,ylo+widths[iy]/2,.906),(.297,widths[iy]-.003,.012),yellow if ix in (0,1) else tile,.001)
# Show one wall; opposite wall stays absent from rendering to expose clear width.
box('05_Back_Wall',(1.65,.775,1.4),(4.0,.15,2.8),concrete)
box('22_Skirting',(2.7,.688,.96),(1.8,.025,.12),trim)
for h in (.65,.90):
    points=[(-.15,.62,h-.075),(1.8,.62,h+.9),(3.35,.62,h+.9),
            (3.35,-.62,h+.9),(1.8,-.62,h+.9),(-.15,-.62,h-.075)]
    build_chain(f'Rail_{int(h*100)}',rounded_path(points))
    for x in (.3,1.2,2.3,3.0):
        bracket(f'Bracket_{h}_{x}',x,.62,h+min(.5*x,.9),.70)
# Read cross-section vertices on straight sections on both sides, not input constants only.
straight_meshes=[o for o in scene.objects if o.type=='MESH' and o.name.startswith('Rail_') and o.get('proof_component')=='Straight']
right=[]; left=[]
for o in straight_meshes:
    ys=[v.co.y for v in o.data.vertices]
    if min(ys)>.59 and max(ys)<.65: right.extend(ys)
    if min(ys)>-.65 and max(ys)<-.59: left.extend(ys)
clear=(min(right)-max(left))*100
report['measured_straight_rail_clear_width_cm']=clear
assert clear >= 119.99
report['stair_rise_cm']=15; report['stair_tread_cm']=30
report['stair_angle_deg']=math.degrees(math.atan(.5))
report['headroom_test']='Not tested: no final ceiling/beam assembly in this sample'
report['playtest']='Not run; heroine capsule width 68cm used only as a dimensional reference'
text('Assembly_Label','ASSEMBLY PROOF / 120 cm CLEAR',(-.15,-1.13,.025),.13)

# Separate exact-scale tile comparison, all panels have equal physical tile pitch.
tile_objs=[]
tile_objs+=floor_tiles('02_PitchProof',0,-4,6,6,0,tile)
tile_objs+=floor_tiles('03_PitchProof',2.1,-4,2,2,0,tile)
tile_objs+=floor_tiles('04_PitchProof',3,-4,2,2,0,yellow)
for bx in (3.15,3.45):
    for by in (-3.85,-3.55):
        for dx in (-.09,-.045,0,.045,.09):
            for dy in (-.09,-.045,0,.045,.09):
                bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=4,radius=1,location=(bx+dx,by+dy,.014))
                o=bpy.context.object; o.name='Tactile_Dot_Proof'; o.scale=(.013,.013,.004); o.data.materials.append(yellow)
report['measured_tile_body_cm']=[round(x*100,4) for x in tile_objs[0].dimensions[:2]]
report['tile_centers_pitch_cm']=(tile_objs[1].location-tile_objs[0].location).length*100
assert abs(report['tile_centers_pitch_cm']-30)<.001
assert all(abs(o.dimensions.x-.297)<1e-5 and abs(o.dimensions.y-.297)<1e-5 for o in tile_objs)
text('Tiles_Label','SAME 30 cm PITCH / 3 mm GROUT',(0,-4.35,.015),.13)
text('02_Label','02 / 180 x 180',(0,-2.03,.015),.12)
text('03_Label','03 / 60 x 60',(2.1,-3.22,.015),.1)
text('04_Label','04 / 60 x 60',(3,-3.22,.015),.1)

# Two end-return prototypes; rotate SINGLE pipe tangent, not the double-rail assembly.
for angle,base,name in [(0,Vector((0,-6,0)),'12-H'),(math.atan(.5),Vector((1.8,-6,0)),'12-S')]:
    t=Vector((math.cos(angle),0,math.sin(angle))); n=Vector((0,1,0)); r=.06
    for h in (.35,.60):
        start=base+Vector((0,0,h)); bend_start=start+t*.65; center=bend_start+n*r
        pts=[]; tans=[]
        for j in range(31):
            a=(math.pi/2)*j/30
            pts.append(center+t*(r*math.sin(a))-n*(r*math.cos(a)))
            tans.append(t*math.cos(a)+n*math.sin(a))
        end=pts[-1]+n*.02
        build_chain(name+str(h),[('Straight',*straight(start,bend_start)),('Bend',pts,tans),('Straight',*straight(pts[-1],end))])
        box(name+'_WallPlate_'+str(h),end,(.07,.008,.07),steel,.003)
    box(name+'_Wall',(base.x+.5,base.y+.105,.6),(1,.05,1.2),concrete)
    text(name+'_Label',name+' / WALL RETURN',(base.x,base.y-.28,.005),.1)
report['return_validation']='Horizontal and 26.565deg slope: pipe-to-bend and bend-to-wall stub interfaces measured; mounting clearance outside sample not tested'

# A wall-end and convex-corner proof, using simple geometry (tile material TBD).
box('20_OuterCorner_A',(4.3,-3.5,.6),(.15,1,1.2),concrete)
box('20_OuterCorner_B',(4.725,-3.925,.6),(.7,.15,1.2),concrete)
box('21_ExposedEndFinish',(4.3,-2.998,.6),(.15,.006,1.2),tile)
box('22_OuterSkirting_A',(4.215,-3.5,.06),(.02,1,.12),trim)
box('22_OuterSkirting_B',(4.65,-4.01,.06),(.89,.02,.12),trim)
text('Wall_Label','20 / 21 / 22',(4.1,-4.3,.015),.1)

box('StudioFloor',(1.8,-2,-.1),(14,15,.12),mat('Studio',(.035,.052,.065)))
scene.world.use_nodes=True
bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND'); bg.inputs[0].default_value=(.15,.19,.23,1); bg.inputs[1].default_value=.45
for loc,power,size in [((1,-3,8),1600,7),((-4,1,5),1100,5),((5,4,6),1700,5)]:
    d=bpy.data.lights.new('Softbox','AREA'); d.energy=power; d.shape='DISK'; d.size=size
    o=bpy.data.objects.new('Softbox',d); scene.collection.objects.link(o); o.location=loc
    o.rotation_euler=(Vector((1,-1,0))-o.location).to_track_quat('-Z','Y').to_euler()
camd=bpy.data.cameras.new('ReviewCamera'); cam=bpy.data.objects.new('ReviewCamera',camd); scene.collection.objects.link(cam)
scene.camera=cam; camd.type='ORTHO'
try: scene.render.engine='CYCLES'
except TypeError: pass
scene.cycles.samples=24; scene.cycles.use_denoising=True
scene.render.resolution_x=1500; scene.render.resolution_y=1050; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
def render(name,loc,target,scale):
    cam.location=loc; cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler(); camd.ortho_scale=scale
    scene.render.filepath=str(OUT/name); bpy.ops.render.render(write_still=True)
report['joint_count']=len(report['joints']); report['max_gap_cm']=max(j['gap_cm'] for j in report['joints'])
report['max_ring_plane_angle_deg']=max(j['ring_plane_angle_deg'] for j in report['joints'])
report['limitations']=['Procedural proof geometry, not Tripo production assets','No UV/LOD/collision production handoff','No full source camera match','No Unreal locomotion/camera test','Wall pieces are untextured geometric prototypes','Open mating rings must be welded or otherwise finished for final meshes']
(OUT/'assembly_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
render('assembly_overview.png',(-4.7,-6.4,5.6),(1.55,0,1),5.8)
if os.environ.get('STAIRWELL_PROOF_RENDER_ONLY') != 'assembly':
    render('tile_pitch_comparison.png',(3,-8,6),(2.0,-3.05,0),6.2)
    render('rail_return_comparison.png',(-.8,-8.5,2.5),(1.3,-5.92,.55),4.4)
cam.location=(-4.7,-6.4,5.6); cam.rotation_euler=(Vector((1.55,0,1))-cam.location).to_track_quat('-Z','Y').to_euler(); camd.ortho_scale=5.8
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'stairwell_assembly_proof_v001.blend'))
print('ASSEMBLY_PROOF_COMPLETE',json.dumps({k:report[k] for k in ['joint_count','max_gap_cm','max_ring_plane_angle_deg','measured_straight_rail_clear_width_cm']}))
