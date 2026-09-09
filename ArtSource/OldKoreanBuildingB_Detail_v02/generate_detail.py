"""Detailed art pass built from the approved v02 geometry. Blender background entry."""
from pathlib import Path
import sys, math, json, random
import bpy
import numpy as np
BASE=Path(__file__).resolve().parent
source=(BASE/'blockout_v02_source.py').read_text(encoding='utf-8')
exec(compile(source.split('# Convex collision boxes')[0],str(BASE/'blockout_v02_source.py'),'exec'))
(OUT/'Textures').mkdir(exist_ok=True)
random.seed(17)

# Portable, tileable PBR texture maps; UVs cover 4 metres per repeat.
N=1024
yy,xx=np.mgrid[0:N,0:N].astype(np.float32)/N
rng=np.random.default_rng(17)
fine=rng.random((N,N)).astype(np.float32)
cloud=(np.sin(xx*math.tau*3+np.sin(yy*math.tau*2))*.3+
       np.cos(yy*math.tau*5+np.sin(xx*math.tau*4))*.2)
def write_image(name,array,noncolor=False):
    img=bpy.data.images.new(name,width=N,height=N,alpha=True)
    img.colorspace_settings.name='Non-Color' if noncolor else 'sRGB'
    if array.ndim==2: array=np.repeat(array[:,:,None],3,axis=2)
    rgba=np.concatenate([array,np.ones((N,N,1),dtype=np.float32)],axis=2)
    img.pixels.foreach_set(np.ascontiguousarray(rgba,dtype=np.float32).ravel())
    img.filepath_raw=str(OUT/'Textures'/(name+'.png'));img.file_format='PNG';img.save()
    return img
def pbr(key,color,height,rough,metallic=0):
    m=materials[key];m.name='M_KB_'+key
    nodes=m.node_tree.nodes;links=m.node_tree.links;bs=nodes.get('Principled BSDF')
    bs.inputs['Metallic'].default_value=metallic
    for suffix,arr,socket,nc in [('BaseColor',color,'Base Color',False),('Roughness',rough,'Roughness',True)]:
        tex=nodes.new('ShaderNodeTexImage');tex.image=write_image('T_KB_'+key+'_'+suffix,arr,nc)
        links.new(tex.outputs['Color'],bs.inputs[socket])
    dx=(np.roll(height,-1,axis=1)-np.roll(height,1,axis=1))*3
    dy=(np.roll(height,-1,axis=0)-np.roll(height,1,axis=0))*3
    norm=np.stack([-dx,-dy,np.ones_like(dx)],axis=2);norm/=np.linalg.norm(norm,axis=2)[:,:,None]
    tex=nodes.new('ShaderNodeTexImage');tex.image=write_image('T_KB_'+key+'_Normal',(norm+1)/2,True)
    normal=nodes.new('ShaderNodeNormalMap');links.new(tex.outputs['Color'],normal.inputs['Color']);links.new(normal.outputs['Normal'],bs.inputs['Normal'])
row=np.floor(yy*48).astype(int)
col=np.floor(xx*16+(row%2)*.5).astype(int)%16
fx=(xx*16+(row%2)*.5)%1;fy=(yy*48)%1
mortar=(fx<.035)|(fx>.965)|(fy<.075)|(fy>.925)
tone=rng.random((48,16))[row%48,col]
brick=np.stack([.43+tone*.13,.20+tone*.075,.13+tone*.06],axis=2)
brick=np.clip(brick+cloud[:,:,None]*.08+(fine[:,:,None]-.5)*.055,0,1)
brick[mortar]=np.stack([.27+fine*.035]*3,axis=2)[mortar]
pbr('Wall',brick,np.where(mortar,.12,.8)+(fine-.5)*.06,np.clip(.82+cloud*.2,0,1))
for key,base in [('Concrete',(.67,.65,.59)),('Inside',(.76,.74,.67)),('Floor',(.50,.51,.48)),('Stair',(.58,.56,.50))]:
    arr=np.clip(np.array(base)[None,None,:]+cloud[:,:,None]*.025+(fine[:,:,None]-.5)*.035,0,1)
    pbr(key,arr,np.clip(.5+cloud*.015+(fine-.5)*.035,0,1),np.clip(.78+cloud*.05,0,1))
# Aged aluminium, painted metal, and opaque dusty glazing remain inexpensive in-game.
for key,colr in [('Frame',(.32,.35,.34)),('Rail',(.18,.20,.19)),('Glass',(.18,.29,.30)),('Teal',(.10,.35,.29))]:
    m=materials[key];m.name='M_KB_'+key
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*colr,1)
    bs.inputs['Roughness'].default_value=.38 if key=='Glass' else .65
    bs.inputs['Metallic'].default_value=.65 if key in ('Frame','Rail') else 0
for key,color in [('Red',(.55,.025,.02,1)),('Navy',(.035,.07,.17,1)),('Cream',(.81,.77,.65,1)),('Dark',(.055,.065,.063,1))]:
    m=bpy.data.materials.new('M_KB_'+key);m.diffuse_color=color;m.use_nodes=True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=color
    m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.7
    materials[key]=m

def extra(name,parts,loc,rot=0,level=0,collision=False):
    key=module(name,parts,collision)
    return place(key,loc,rot,level,'detail')
def adopt(name,objects,collision_parts_local=None):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects: ob.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    if len(objects)>1: bpy.ops.object.join()
    ob=objects[0]
    scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    key='SM_KB_'+name;ob.name=key
    for c in list(ob.users_collection):c.objects.unlink(ob)
    lib.objects.link(ob);modules[key]=ob;collision_parts[key]=collision_parts_local or []
    return key
font=bpy.data.fonts.load('C:/Windows/Fonts/malgunbd.ttf')
def lettering(name,words,width,height,color='Cream'):
    curve=bpy.data.curves.new(name,'FONT');curve.body=words;curve.font=font;curve.align_x='CENTER';curve.align_y='CENTER'
    curve.size=1;curve.extrude=.001;curve.resolution_u=3
    ob=bpy.data.objects.new(name,curve);lib.objects.link(ob);curve.materials.append(materials[color])
    bpy.context.view_layer.update();factor=min(width/max(ob.dimensions.x,.01),height/max(ob.dimensions.y,.01))
    ob.scale=(factor,)*3;ob.rotation_euler.x=math.pi/2
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    bpy.ops.object.convert(target='MESH');bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    return adopt(name,[ob])

# Replace the flat blockout canopies with sloping striped fabric.
awning_parts=[box(i*.15,-1.35,2.62,.15,1.35,.035,'Cream' if i%2 else 'Teal')+(math.radians(10),) for i in range(24)]
awning_parts += [box(i*.15,-1.35,2.35,.15,.035,.27,'Cream' if i%2 else 'Teal') for i in range(24)]
newawning=module('Awning_Striped_Green_360',awning_parts)
orangeparts=[tuple('Ochre' if v=='Teal' else v for v in p) for p in awning_parts]
orangeawning=module('Awning_Striped_Orange_360',orangeparts)
for ob in list(assembly.objects):
    if ob['module']=='SM_KB_Awning_360':
        key=orangeawning if ob.location.x<7 else newawning
        ob.data=modules[key].data;ob['module']=key
        p=next(p for p in placements if p['name']==ob.name);p['module']=key
for lev,labels in enumerate([['특등상회','특등상회','화산심해','화산심해'],['삼성영어','삼성영어','삼성영어','서용상설'],['독서전용','수초등전문','수초등전문','학원']]):
    for i,label in enumerate(labels):
        key=lettering('SignText_%d_%d'%(lev,i),label,2.8,.30)
        place(key,(i*3.6+1.8,-.175,lev*3.4+2.92),level=lev,role='detail')
# Large vertical projection sign and small storefront plaques.
extra('VerticalSign_Case',[box(0,0,0,.72,.22,3.0,'Teal'),box(-.035,-.015,-.035,.035,.025,3.07,'Frame'),box(.72,-.015,-.035,.035,.025,3.07,'Frame'),box(0,-.015,-.035,.72,.025,.035,'Frame'),box(0,-.015,3,.72,.025,.035,'Frame')],(.05,-.65,3.8))
vtext=lettering('VerticalSign_Text','삼\n성\n영\n어',.52,2.6)
place(vtext,(.41,-.68,5.30),role='detail')
for i,(word,x) in enumerate([('특\n등',.6),('수\n초',4.2),('등\n전',8.8),('학\n원',11.9)]):
    extra('WindowPoster_%d'%i,[box(0,0,0,.55,.012,1.28,'Cream')],(x,-.01,7.72))
    key=lettering('WindowPosterText_%d'%i,word,.40,1.05,'Navy')
    place(key,(x+.275,-.025,8.36),level=2,role='detail')
for i in (0,1,2,3):
    for side in (0,1):
        x=i*3.6+(1.10 if not side else 2.43)
        extra('ShopDoorTrim_%d_%d'%(i,side),[box(0,0,0,.055,.045,2.4,'Frame')],(x,-.02,0))

# Reusable condenser: sheet metal housing, circular fan rings, grille and brackets.
parts=[box(0,0,0,.90,.36,.68,'Cream'),box(.03,-.018,.03,.84,.018,.62,'Frame')]
parts += [box(.60,-.035,.06+j*.055,.25,.025,.018,'Dark') for j in range(10)]
parts += [box(x,-.015,-.14,.045,.55,.06,'Frame') for x in (.10,.74)]
housing=mesh_boxes('AC_parts',parts,lib)
pieces=[housing]
for rad in (.23,.205,.18,.155,.13,.10,.07):
    bpy.ops.mesh.primitive_torus_add(major_radius=rad,minor_radius=.005,major_segments=32,minor_segments=4,location=(.31,-.045,.34),rotation=(math.pi/2,0,0))
    ob=bpy.context.object;ob.data.materials.append(materials['Dark']);pieces.append(ob)
fanbars=mesh_boxes('FanBars',[box(.08+i*.055,-.054,.11,.006,.007,.46,'Dark') for i in range(9)],lib);pieces.append(fanbars)
ac=adopt('AirConditioner_90',pieces,[box(0,0,0,.9,.36,.68)])
for x,z in [(.35,3.65),(7.0,3.65),(12.75,3.65),(.35,7.05),(10.1,7.05)]: place(ac,(x,-.50,z),role='detail')
for x in (5.3,6.5):place(ac,(x,10.8,10.2),180,3,'detail')

# Narrow pipe cylinders, assembled into a single modular riser with elbow approximation.
def pipe_module(name,segments,radius=.035,mat='Frame'):
    obs=[]
    for a,b in segments:
        a=Vector(a);b=Vector(b);delta=b-a
        bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=radius,depth=delta.length,location=(a+b)/2)
        ob=bpy.context.object;ob.rotation_euler=delta.to_track_quat('Z','Y').to_euler();ob.data.materials.append(materials[mat]);obs.append(ob)
    return adopt(name,obs)
pipe=pipe_module('Drainpipe_340',[((0,0,0),(0,0,3.4))],.045)
for lev in range(3):
    for x in (-.08,14.48): place(pipe,(x,-.12,lev*3.4),level=lev,role='detail')
cable=pipe_module('AC_PipePair',[((0,0,0),(.6,0,0)),((.6,0,0),(.6,0,.8)),((0,.06,0),(.65,.06,0)),((.65,.06,0),(.65,.06,.8))],.018)
for x,z in [(1.25,3.7),(7.9,3.7),(1.25,7.1)]:place(cable,(x,-.18,z),role='detail')

# Stackable red stools, outside the door approaches.
stool_parts=[box(0,0,.41,.35,.35,.05,'Red')]+[box(x,y,0,.055,.055,.41,'Red') for x in (0,.295) for y in (0,.295)]
stool_parts += [box(0,0,.16,.35,.045,.04,'Red'),box(0,.305,.16,.35,.045,.04,'Red'),box(0,0,.16,.045,.35,.04,'Red'),box(.305,0,.16,.045,.35,.04,'Red')]
stool=module('Stool_Red',stool_parts,True)
for i in range(4):place(stool,(13.55,-.50-i*.45,0),role='detail')
extra('UtilityBox',[box(0,0,0,.42,.18,.60,'Concrete'),box(.035,-.02,.04,.35,.03,.52,'Frame'),box(.28,-.045,.24,.035,.025,.10,'Dark')],(-.27,2.0,1.4),-90)

# Interior finish: baseboards and wall lamps, kept out of the stair/door route.
baseboard=module('Baseboard_300',[box(0,0,0,3,.035,.12,'Frame')],False)
for lev in range(3):
    for ix in range(3):place(baseboard,(4.6+ix*3,11.73,lev*3.4),180,lev,'detail')
    extra('CeilingLamp_%d'%lev,[box(0,0,0,1.2,.18,.06,'Frame'),box(.04,.02,-.012,1.12,.14,.02,'Cream')],(6,4.9,lev*3.4+3.14),level=lev)

# Reference silhouette revision: preserve the traversable roof exit (2.4m).
for ob in list(assembly.objects):
    if ob['role']=='headhouse':
        ob.scale.z=2.4/2.8
    if ob['role']=='headroof': ob.location.z=12.6
    if 'Awning_Striped' in ob['module']:
        ob.scale.x=.88
        ob.location.x+=.12
    for entry in placements:
        if entry['name']==ob.name:
            entry['scale']=list(ob.scale);entry['location_m']=list(ob.location)
# Shallow roofhouse clerestory detailing, outside the stair enclosure.
extra('Roofhouse_Clerestory',[box(0,0,0,4.4,.045,.55,'Dark')]+[box(x,-.02,0,.045,.07,.55,'Frame') for x in (0,.73,1.46,2.2,2.93,3.66,4.35)]+[box(0,-.02,z,4.4,.07,.04,'Cream') for z in (0,.51)],(0,4.33,12.0),level=3)
# Front fascia panels establish the pale, broad horizontal bands in the reference.
for lev in (1,2,3):
    z=lev*3.4
    for i in range(12):
        extra('BandPanel_%d_%d'%(lev,i),[box(0,0,0,1.17,.05,.45,'Concrete'),box(0,-.025,.42,1.17,.09,.055,'Cream')],(i*1.2,-.43,z-.18),level=lev)
# Shop display panels flank a continuously open 1.4m passage.
for i in range(4):
    for j,xoff in enumerate((.08,2.52)):
        extra('ShopDisplay_%d_%d'%(i,j),[box(0,0,0,.98,.045,2.35,'Frame'),box(.045,-.018,.08,.89,.025,.68,'Teal'),box(.045,-.018,.79,.89,.025,1.50,'Glass')],(i*3.6+xoff,-.07,0))
        key=lettering('ShopPrint_%d_%d'%(i,j),'특등' if i<2 else '화산',.68,.24,'Cream')
        place(key,(i*3.6+xoff+.49,-.11,1.55),role='detail')
# Second-floor window film with separate panes instead of repeated blank glass.
for i in range(4):
    for j in range(3):
        x=i*3.6+.52+j*.87
        extra('AcademyFilm_%d_%d'%(i,j),[box(0,0,0,.77,.012,.58,'Teal')],(x,-.045,4.40),level=1)
    key=lettering('AcademyWindowText_%d'%i,'삼성 영어',2.35,.30,'Cream')
    place(key,(i*3.6+1.8,-.065,4.70),level=1,role='detail')
# Update inventories and export the portable geometry + texture set.
exec(source[source.index('def collision_objects'):source.index('for key,ob in modules.items():')])
for key,ob in modules.items():
    cols=collision_objects(key);export(OUT/'Modules'/(key+'.fbx'),[ob]+cols)
    for c in cols:bpy.data.objects.remove(c,do_unlink=True)
bpy.context.view_layer.update();cols=[]
for ob in assembly.objects:cols.extend(collision_objects(ob['module'],ob.matrix_world,ob.name))
export(OUT/'OldKoreanBuildingB_Detail_Assembly.fbx',list(assembly.objects)+cols)
for c in cols:bpy.data.objects.remove(c,do_unlink=True)
(OUT/'assembly.json').write_text(json.dumps({'units':'metres','front':'-Y','placements':placements},indent=2),encoding='utf-8')
(OUT/'collision_policy.json').write_text(json.dumps({key:{'custom_hulls':len(collision_parts[key]),'disable_auto_collision':True} for key in modules},indent=2),encoding='utf-8')
(OUT/'material_manifest.json').write_text(json.dumps({'texture_size':1024,'texture_repeat_m':4,'normal_format':'OpenGL +Y; flip green channel for Unreal DirectX normal convention','pbr_materials':{key:{'material':materials[key].name,'basecolor':'Textures/T_KB_'+key+'_BaseColor.png','roughness':'Textures/T_KB_'+key+'_Roughness.png','normal':'Textures/T_KB_'+key+'_Normal.png'} for key in ('Wall','Concrete','Inside','Floor','Stair')}},indent=2),encoding='utf-8')
lib.hide_render=True;lib.hide_viewport=True
exec(source[source.index('# Geometric route check'):source.index('# Presentation setup')])
exec(source[source.index('# Presentation setup'):source.index("bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'OldKoreanBuildingB_Blockout.blend'))")].replace("'Inside'","'Cream'"))
scene.render.resolution_x=1600;scene.render.resolution_y=1400;scene.cycles.samples=24
scene.cycles.use_denoising=True
scene.world.color=(.65,.65,.65)
scene.view_settings.exposure=.8
cam.location=(-12,-30,13);aim(cam,(7,4,5.8));camdata.ortho_scale=22
for img in bpy.data.images:
    if img.filepath and 'T_KB_' in img.name: img.filepath='//Textures/'+Path(img.filepath).name
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'OldKoreanBuildingB_Detail.blend'))
def render(name):
    scene.render.filepath=str(OUT/'Previews'/name);bpy.ops.render.render(write_still=True)
render('01_Detailed_Exterior.png')
cam.location=(22,-24,13);aim(cam,(7,4,5));camdata.ortho_scale=22
render('02_Detailed_FrontRight.png')
cam.location=(-8,-11,5);aim(cam,(4,0,2.6));camdata.ortho_scale=11
render('03_Storefront_Closeup.png')
print('DETAIL_COMPLETE',len(modules),len(placements))
