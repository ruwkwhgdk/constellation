"""Run with Blender --background --python this_file. All dimensions in metres."""
import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector

OUT = Path(__file__).resolve().parent
for sub in ('Modules', 'Previews'):
    (OUT / sub).mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name != 'Collection': bpy.data.collections.remove(c)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1
lib = bpy.data.collections.new('MODULE_LIBRARY (hidden; local origins)')
scene.collection.children.link(lib)
assembly = bpy.data.collections.new('BUILDING • 3 FLOORS + ROOF')
scene.collection.children.link(assembly)
presentation = bpy.data.collections.new('PRESENTATION • not exported')
scene.collection.children.link(presentation)
materials = {}
for name, color in {'Wall':(.48,.32,.27,1), 'Inside':(.77,.75,.67,1), 'Concrete':(.62,.62,.57,1),
                    'Floor':(.42,.47,.45,1), 'Frame':(.19,.25,.26,1), 'Glass':(.28,.47,.49,1),
                    'Stair':(.73,.58,.32,1), 'Rail':(.15,.19,.19,1), 'Teal':(.12,.39,.37,1),
                    'Ochre':(.75,.40,.15,1), 'White':(.86,.85,.77,1)}.items():
    m = bpy.data.materials.new('M_BKO_'+name)
    m.diffuse_color = color
    m.use_nodes = True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = color
    m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .78
    materials[name] = m

def box(x,y,z,w,d,h,mat='Wall'):
    return (x,y,z,w,d,h,mat)

def mesh_boxes(name, parts, coll):
    verts, faces, mids = [], [], []
    keys = list(materials)
    for part in parts:
        x,y,z,w,d,h,m=part[:7]
        n=len(verts)
        local=[(0,0,0),(w,0,0),(w,d,0),(0,d,0),(0,0,h),(w,0,h),(w,d,h),(0,d,h)]
        angle=part[7] if len(part)>7 else 0
        verts.extend([(x+a,y+b*math.cos(angle)-c*math.sin(angle),z+b*math.sin(angle)+c*math.cos(angle)) for a,b,c in local])
        faces.extend([tuple(n+i for i in f) for f in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]])
        mids.extend([keys.index(m)]*6)
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(verts,[],faces); mesh.update()
    for m in materials.values(): mesh.materials.append(m)
    for p,idx in zip(mesh.polygons,mids): p.material_index=idx
    uv=mesh.uv_layers.new(name='UVMap')
    for p in mesh.polygons:
        normal=p.normal
        axes=(0,1) if abs(normal.z)>.5 else ((0,2) if abs(normal.y)>.5 else (1,2))
        for li in p.loop_indices:
            co=mesh.vertices[mesh.loops[li].vertex_index].co
            uv.data[li].uv=(co[axes[0]]/4,co[axes[1]]/4)
    obj=bpy.data.objects.new(name,mesh); coll.objects.link(obj)
    return obj

modules={}; placements=[]; collision_parts={}; solids=[]
def module(name,parts,collision=True):
    key='SM_KB_'+name
    ob=mesh_boxes(key,parts,lib)
    modules[key]=ob
    collision_parts[key]=parts if collision else []
    return key

def place(key,loc=(0,0,0),rot=0,level=0,role='structure',scale=(1,1,1)):
    src=modules[key]
    ob=bpy.data.objects.new(key+'__%03d'%len(placements),src.data)
    assembly.objects.link(ob)
    ob.location=loc; ob.rotation_euler.z=math.radians(rot)
    ob.scale=scale
    ob['module']=key; ob['level']=level; ob['role']=role
    placements.append({'name':ob.name,'module':key,'location_m':list(loc),'rotation_z_deg':rot,'level':level,'role':role,'scale':list(scale)})
    if collision_parts[key]: solids.append(ob)
    return ob

def opening(w,h=3.2,ow=1.4,oh=2.4,sill=0,mat='Wall',depth=.24):
    a=(w-ow)/2
    p=[box(0,0,0,a,depth,h,mat),box(a+ow,0,0,a,depth,h,mat),box(a,0,sill+oh,ow,depth,h-sill-oh,mat)]
    if sill: p.append(box(a,0,0,ow,depth,sill,mat))
    return p

wall=module('Wall_Solid_360', [box(0,0,0,3.6,.24,3.2)])
frontdoor=module('Wall_Entrance_360', opening(3.6))
window=module('Wall_Window_360',opening(3.6,ow=2.7,oh=1.7,sill=.8))
sidewall=module('Wall_Solid_300',[box(0,0,0,3,.24,3.2)])
sidewindow=module('Wall_Window_300',opening(3,ow=1.4,oh=1.7,sill=.8))
sidedoor=module('Wall_Entrance_300',opening(3))
frame=module('Window_Frame_270',[box(.45,-.035,.8,2.7,.08,.07,'Frame'),box(.45,-.035,2.43,2.7,.08,.07,'Frame')]+
    [box(x,-.035,.8,.055,.08,1.7,'Frame') for x in (.45,1.34,2.24,3.095)])
glass=module('Window_Panel_270',[box(.50,.09,.87,2.6,.025,1.56,'Glass')])
sideglass=module('Window_Panel_140',[box(.8,.09,.8,1.4,.025,1.7,'Glass')])
doorframe=module('Door_Frame_140',[box(x,-.03,0,.07,.3,2.4,'Frame') for x in (1.03,2.50)]+[box(1.03,-.03,2.4,1.54,.3,.07,'Frame')],False)
floor=module('Floor_360x300',[box(0,0,-.2,3.6,3,.2,'Floor')])
trim=module('Fascia_360',[box(0,-.38,-.2,3.6,.62,.43,'Concrete')])
trimside=module('Fascia_300',[box(0,-.38,-.2,3,.62,.43,'Concrete')])
parapet=module('Parapet_360',[box(0,0,0,3.6,.24,1.05,'Concrete'),box(0,-.05,1.05,3.6,.34,.08,'White')])
parapetside=module('Parapet_300',[box(0,0,0,3,.24,1.05,'Concrete'),box(0,-.05,1.05,3,.34,.08,'White')])
inner=module('Partition_Door_720',opening(7.2,ow=1.4,mat='Inside',depth=.15))
rearinner=module('Partition_Door_1000',opening(10,ow=1.4,mat='Inside',depth=.15))
divider=module('Partition_Solid_380',[box(0,0,0,3.8,.15,3.2,'Inside')])
stairwall=module('Stairwell_Side_560',[box(0,0,0,5.6,.15,3.2,'Inside')])
landing=module('Landing_410x200',[box(0,0,-.2,4.1,2,.2,'Floor')])
rearlanding=module('Landing_410x236',[box(0,0,-.2,4.1,2.36,.2,'Stair')])
strip=module('Floor_1000x300',[box(0,0,-.2,10,3,.2,'Floor')])
filler=module('Floor_440x040',[box(0,0,-.2,4.4,.4,.2,'Floor')])
# Treads are 17 cm high boxes; two solid side stringers support the visible flight.
stair_parts=[box(0,i*.3,i*.17,1.8,.3,.17,'Stair') for i in range(10)]
for x in (0,1.74): stair_parts.append(box(x,0,-.12,.06,math.hypot(3,1.7),.15,'Stair')+(math.atan2(1.7,3),))
stair=module('Stair_Flight_180_170',stair_parts)
railparts=[box(.0,i*.6,i*.34+.17,.055,.055,1.05,'Rail') for i in range(5)]
railparts.append(box(0,0,1.17,.055,math.hypot(3,1.7),.055,'Rail')+(math.atan2(1.7,3),))
rail=module('Stair_Rail_300',railparts)
railflat=module('Guardrail_180',[box(0,0,1.05,1.8,.055,.055,'Rail')]+[box(x,0,0,.055,.055,1.05,'Rail') for x in (0,.6,1.2,1.745)])
awning=module('Awning_360',[box(0,-1.1,2.6,3.6,1.1,.12,'Teal'),box(0,-1.1,2.36,3.6,.08,.24,'Teal')],False)
sign=module('Sign_Blank_360',[box(.12,-.16,2.72,3.36,.16,.42,'Teal')],False)

# Raised floors are explicitly split around stair hole x=.24..4.4, y=6.4..11.76.
for lev in range(4):
    z=lev*3.4
    for ix in range(4):
        for iy in range(2 if lev else 4): place(floor,(ix*3.6,iy*3,z),level=lev,role='floor')
    if lev:
        for iy in (6,9): place(strip,(4.4,iy,z),level=lev,role='floor')
        place(filler,(0,6,z),level=lev,role='floor')
    if lev==3: break
    for ix in range(4):
        place(frontdoor if lev==0 else window,(ix*3.6,0,z),level=lev,role='front')
        if lev:
            place(frame,(ix*3.6,0,z),level=lev,role='front')
            place(glass,(ix*3.6,0,z),level=lev,role='front')
        else:
            place(doorframe,(ix*3.6,0,z),level=lev,role='front')
            place(awning,(ix*3.6,0,z),level=lev,role='front')
        place(sign,(ix*3.6,0,z),level=lev,role='front')
        place(window,(14.4-ix*3.6,12,z),180,lev,'rear')
        place(frame,(14.4-ix*3.6,12,z),180,lev,'rear')
        place(glass,(14.4-ix*3.6,12,z),180,lev,'rear')
        place(trim,(ix*3.6,0,z+3.4),level=lev,role='front')
        place(trim,(14.4-ix*3.6,12,z+3.4),180,lev,'rear')
    for iy in range(4):
        place(sidedoor if lev==0 and iy==1 else sidewindow,(0,3+iy*3,z),-90,lev,'left')
        place(sidewindow,(14.4,iy*3,z),90,lev,'right')
        place(sideglass,(14.4,iy*3,z),90,lev,'right')
        place(trimside,(0,3+iy*3,z+3.4),-90,lev,'left')
        place(trimside,(14.4,iy*3,z+3.4),90,lev,'right')
    # Terminate partitions at the inner face of the 24 cm exterior shell.
    for x in (.24,7.2): place(inner,(x,3.8,z),level=lev,role='partition',scale=(6.96/7.2,1,1))
    place(divider,(7.2,.24,z),90,lev,'partition',scale=(3.56/3.8,1,1))
    place(rearinner,(4.4,6.4,z),level=lev,role='partition',scale=(9.76/10,1,1))
    place(stairwall,(4.4,11.76,z),-90,lev,'stairwall',scale=(5.36/5.6,1,1))
    place(stair,(.3,6.4,z),level=lev,role='stair')
    place(stair,(4.1,9.4,z+1.7),180,lev,'stair')
    place(rearlanding,(.3,9.4,z+1.7),level=lev,role='stair')
    for x in (.245,2.1): place(rail,(x,6.4,z),level=lev,role='rail')
    for x in (2.3,4.155): place(rail,(x,9.4,z+1.7),180,lev,'rail')

# Rooftop perimeter and stair headhouse. No slab crosses the uppermost flight.
for ix in range(4):
    place(parapet,(ix*3.6,0,10.2),level=3,role='parapet')
    place(parapet,(14.4-ix*3.6,12,10.2),180,3,'parapet')
for iy in range(4):
    place(parapetside,(0,iy*3+3,10.2),-90,3,'parapet')
    place(parapetside,(14.4,iy*3,10.2),90,3,'parapet')
headfront=module('Roofhouse_Door_440',opening(4.4,h=2.8,mat='Concrete'))
headside=module('Roofhouse_Side_760',[box(0,0,0,7.6,.24,2.8,'Concrete')])
headback=module('Roofhouse_Back_440',[box(0,0,0,4.4,.24,2.8,'Concrete')])
headroof=module('Roofhouse_Cap_480x800',[box(0,0,0,4.8,8,.18,'Concrete')])
place(headfront,(0,4.4,10.2),level=3,role='headhouse')
place(headside,(0,12,10.2),-90,3,'headhouse')
place(headside,(4.4,4.4,10.2),90,3,'headhouse')
place(headback,(4.4,12,10.2),180,3,'headhouse')
place(headroof,(-.2,4.2,13),level=4,role='headroof')
place(railflat,(.3,6.4,10.2),level=3,role='rail')

# Append glazing to preserve the existing assembly component indices.
for lev in range(3):
    for iy in range(4):
        if lev==0 and iy==1: continue
        place(sideglass,(0,3+iy*3,lev*3.4),-90,lev,'left')

bpy.context.view_layer.update()
for ob in assembly.objects:
    if ob['role'] in ('partition','stairwall'):
        points=[ob.matrix_world @ Vector(corner) for corner in ob.bound_box]
        assert min(v.x for v in points)>=.24-1e-5 and max(v.x for v in points)<=14.16+1e-5, ob.name
        assert min(v.y for v in points)>=.24-1e-5 and max(v.y for v in points)<=11.76+1e-5, ob.name

# Convex collision boxes preserve door/window voids; never a single building hull.
def collision_objects(key, transform=None, prefix=None):
    result=[]
    for i,p in enumerate(collision_parts[key]):
        ob=mesh_boxes('UCX_'+(prefix or key)+'_%02d'%i,[p],lib)
        if transform is not None: ob.matrix_world=transform.copy()
        result.append(ob)
    return result

def export(path,objects):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects: ob.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH'},
        axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE',
        use_mesh_modifiers=True,mesh_smooth_type='FACE',use_triangles=True,add_leaf_bones=False,
        bake_anim=False,path_mode='AUTO')

for key,ob in modules.items():
    cols=collision_objects(key)
    export(OUT/'Modules'/(key+'.fbx'),[ob]+cols)
    for c in cols: bpy.data.objects.remove(c,do_unlink=True)
bpy.context.view_layer.update()
cols=[]
for ob in assembly.objects: cols.extend(collision_objects(ob['module'],ob.matrix_world,ob.name))
export(OUT/'OldKoreanBuildingB_Assembly.fbx',list(assembly.objects)+cols)
for c in cols: bpy.data.objects.remove(c,do_unlink=True)
(OUT/'assembly.json').write_text(json.dumps({'units':'metres','front':'-Y','placements':placements},indent=2),encoding='utf-8')
lib.hide_render=True; lib.hide_viewport=True

# Geometric route check: support and head clearance along both flights and landings.
bpy.context.view_layer.update()
def nearest_ray(origin,direction,maxdist=100):
    best=maxdist; hitname=None
    origin=Vector(origin); direction=Vector(direction)
    for ob in solids:
        inv=ob.matrix_world.inverted()
        hit,co,normal,index=ob.ray_cast(inv@origin, inv.to_3x3()@direction,distance=maxdist)
        if hit:
            distance=(ob.matrix_world@co-origin).length
            if distance<best: best=distance; hitname=ob.name
    return best,hitname
samples=[]
for lev in range(3):
    z=lev*3.4
    for i in range(10):
        samples.append((1.2,6.4+(i+.5)*.3,z+(i+1)*.17))
        samples.append((3.2,9.4-(i+.5)*.3,z+1.7+(i+1)*.17))
    for x in (1.2,2.2,3.2): samples.append((x,10.4,z+1.7))
    for y in (4.9,5.5,6.1): samples.append((3.2,y,z+3.4))
checks=[]
for x,y,z in samples:
    down,hit=nearest_ray((x,y,z+.05),(0,0,-1),.3)
    up,ceiling=nearest_ray((x,y,z+.02),(0,0,1),10)
    checks.append({'point':[x,y,z],'supported':bool(hit) and abs(down-.05)<.005,'headroom_m':round(up+.02,3)})
validation={'route_samples':len(checks),'supported':all(c['supported'] for c in checks),
            'minimum_stair_headroom_m':min(c['headroom_m'] for c in checks),
            'module_count':len(modules),'instance_count':len(placements),'checks':checks,
            'unreal_playtest':'not yet performed','note':'Vertical centreline geometry checks, not a character sweep or camera playtest.'}
(OUT/'validation.json').write_text(json.dumps(validation,indent=2),encoding='utf-8')
assert validation['supported'], 'Unsupported stair route'
assert validation['minimum_stair_headroom_m']>=2.1, 'Stair head clearance below 2.1 m'

# Presentation setup, kept out of FBX exports.
ground=mesh_boxes('Presentation_Ground',[box(-5,-5,-.28,25,23,.06,'Inside')],presentation)
def aim(ob,target): ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
camdata=bpy.data.cameras.new('Review_Camera'); cam=bpy.data.objects.new('Review_Camera',camdata)
presentation.objects.link(cam); scene.camera=cam
camdata.type='ORTHO';camdata.ortho_scale=25
cam.location=(-20,-26,22);aim(cam,(7,5,5.5))
for name,loc,power,size in [('Key',(-8,-10,24),2600,12),('Fill',(20,-2,16),1800,10),('Roof',(6,18,24),2300,10)]:
    ld=bpy.data.lights.new(name,'AREA');ld.energy=power;ld.shape='DISK';ld.size=size
    lo=bpy.data.objects.new(name,ld);presentation.objects.link(lo);lo.location=loc;aim(lo,(7,6,4))
scene.world.color=(.65,.65,.65)
scene.render.engine='CYCLES';scene.cycles.samples=32
scene.render.resolution_x=1600;scene.render.resolution_y=1300;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
scene.render.image_settings.file_format='PNG'
# Default file opens in a useful material-colour solid perspective.
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        area.spaces.active.shading.color_type='MATERIAL'
        area.spaces.active.region_3d.view_distance=28
        area.spaces.active.region_3d.view_location=(7,6,5)
        area.spaces.active.region_3d.view_rotation=cam.rotation_euler.to_quaternion()
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'OldKoreanBuildingB_Blockout.blend'))
if '--skip-render' in sys.argv:
    print('BLOCKOUT_COMPLETE (render skipped)',validation['module_count'],validation['instance_count'])
    sys.exit(0)
def render(name):
    scene.render.filepath=str(OUT/'Previews'/name)
    bpy.ops.render.render(write_still=True)
render('01_Exterior.png')
for ob in assembly.objects:
    if ob['role'] in ('front','left','headroof') or ob['level']>=2: ob.hide_render=True
cam.location=(-19,-23,27);aim(cam,(7,6,3));camdata.ortho_scale=24
render('02_Cutaway.png')
for ob in assembly.objects: ob.hide_render=False
camdata.type='PERSP';camdata.lens=19
cam.location=(6.5,5.1,1.7);aim(cam,(1.4,8.5,2.0))
ld=bpy.data.lights.new('Interior_Fill','AREA');ld.energy=350;ld.size=5
lo=bpy.data.objects.new('Interior_Fill',ld);presentation.objects.link(lo);lo.location=(3,6,3);aim(lo,(2,8,0))
render('03_Stair_Lobby.png')
print('BLOCKOUT_COMPLETE',json.dumps({k:v for k,v in validation.items() if k!='checks'}))
