"""Editable stylized pigeon, skeletal weights and four in-place flight clips."""
import bpy, math, json
from pathlib import Path
from mathutils import Vector, Quaternion
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'Bird/v001'; OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.context.preferences.filepaths.save_version=0
scene=bpy.context.scene; scene.unit_settings.system='METRIC'; scene.render.fps=48
def mat(name,c):
    m=bpy.data.materials.new(name); m.diffuse_color=(*c,1); m.use_nodes=True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*c,1)
    m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.65
    return m
white=mat('Pigeon_Ivory',(.79,.78,.7)); feather=mat('Pigeon_Feather',(.65,.65,.59)); black=mat('Pigeon_Eye',(.018,.014,.012)); beakmat=mat('Pigeon_Beak',(.35,.25,.20)); feet=mat('Pigeon_Feet',(.38,.22,.20))
parts=[]
def weight(o,bone):
    o.vertex_groups.new(name=bone).add(list(range(len(o.data.vertices))),1,'REPLACE'); parts.append(o)
def ellipsoid(name,loc,scale,material,bone):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=10,radius=1,location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale; bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    o.data.materials.append(material)
    for p in o.data.polygons:p.use_smooth=True
    weight(o,bone); return o
ellipsoid('Body',(0,0,.015),(.051,.092,.048),white,'body')
ellipsoid('Breast',(0,.052,.038),(.043,.057,.047),white,'body')
ellipsoid('Neck',(0,.091,.061),(.028,.043,.036),white,'neck')
ellipsoid('Head',(0,.13,.086),(.029,.035,.03),white,'head')
for side in [-1,1]: ellipsoid('Eye',(side*.025,.145,.094),(.005,.005,.005),black,'head')
ellipsoid('Beak',(0,.169,.08),(.012,.025,.009),beakmat,'head')
for side,label in [(1,'L'),(-1,'R')]:
    ellipsoid('Thigh',(side*.024,-.042,-.025),(.014,.025,.016),white,'leg_'+label)
    ellipsoid('Foot',(side*.025,-.07,-.04),(.008,.025,.006),feet,'foot_'+label)

def blade(name,start,end,width,material,bone):
    a,b=Vector(start),Vector(end); d=b-a; lateral=Vector((-d.y,d.x,0)).normalized()*width*.5
    mid=a+d*.52
    vertices=[a,mid-lateral,b,mid+lateral,mid+Vector((0,0,.002)),mid-Vector((0,0,.001))]
    faces=[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(1,0,5),(2,1,5),(3,2,5),(0,3,5)]
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(vertices,[],faces); mesh.update()
    o=bpy.data.objects.new(name,mesh); scene.collection.objects.link(o); mesh.materials.append(material); weight(o,bone)
for i in range(9):
    x=(i-4)*.010
    blade('Tail',(x*.55,-.065,.013),(x,-.174,.004),.022,white if i%2 else feather,'tail')
for side,label in [(1,'L'),(-1,'R')]:
    # Continuous wing surface with blended elbow/wrist weighting.
    verts=[]
    for x in [.035,.075,.12,.16,.20,.24,.285]:
        y=-.005 if x<.14 else .004
        verts.extend([(side*x,y,.035),(side*x,y-(.085 if x<.20 else .065),.028)])
    faces=[(2*i,2*i+1,2*i+3,2*i+2) for i in range(6)]
    if side<0: faces=[tuple(reversed(f)) for f in faces]
    mesh=bpy.data.meshes.new('WingSurface'); mesh.from_pydata(verts,[],faces); mesh.update()
    o=bpy.data.objects.new('Wing_'+label,mesh); scene.collection.objects.link(o); mesh.materials.append(white)
    groups={n:o.vertex_groups.new(name=n+'_'+label) for n in ['shoulder','elbow','wrist']}
    for v in mesh.vertices:
        x=abs(v.co.x)
        if x<.12:
            t=max(0,min(1,(x-.065)/.055)); groups['shoulder'].add([v.index],1-t,'REPLACE'); groups['elbow'].add([v.index],t,'REPLACE')
        else:
            t=max(0,min(1,(x-.17)/.06)); groups['elbow'].add([v.index],1-t,'REPLACE'); groups['wrist'].add([v.index],t,'REPLACE')
    parts.append(o)
    for i in range(10):
        x=.075+i*.014
        blade('Secondary',(side*x,-.025,.03),(side*(x+.008),-.127,.017),.024,white if i%2 else feather,('shoulder' if x<.1 else 'elbow')+'_'+label)
    for i in range(9):
        x=.20+i*.009
        blade('Primary',(side*x,.002,.03),(side*(.27+i*.010),-.085-i*.010,.018),.025,white if i%2 else feather,'tip_'+label)

bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0]; bpy.ops.object.join(); meshobj=bpy.context.object; meshobj.name='SK_OH_Pigeon'
bpy.ops.object.armature_add(); rig=bpy.context.object; rig.name='RIG_OH_Pigeon'
bpy.ops.object.mode_set(mode='EDIT'); rig.data.edit_bones.remove(rig.data.edit_bones[0])
def bone(name,a,b,parent=None):
    e=rig.data.edit_bones.new(name); e.head=a; e.tail=b
    if parent:e.parent=rig.data.edit_bones[parent]
bone('root',(0,0,0),(0,.03,0))
bone('body',(0,-.06,.015),(0,.05,.035),'root')
bone('neck',(0,.05,.035),(0,.105,.07),'body')
bone('head',(0,.105,.07),(0,.17,.08),'neck')
bone('tail',(0,-.06,.015),(0,-.17,.008),'body')
for side,label in [(1,'L'),(-1,'R')]:
    bone('shoulder_'+label,(side*.03,0,.035),(side*.12,-.005,.035),'body')
    bone('elbow_'+label,(side*.12,-.005,.035),(side*.22,0,.035),'shoulder_'+label)
    bone('wrist_'+label,(side*.22,0,.035),(side*.285,0,.03),'elbow_'+label)
    bone('tip_'+label,(side*.285,0,.03),(side*.35,-.06,.025),'wrist_'+label)
    bone('leg_'+label,(side*.024,-.035,0),(side*.025,-.06,-.04),'body')
    bone('foot_'+label,(side*.025,-.06,-.04),(side*.025,-.09,-.04),'leg_'+label)
bpy.ops.object.mode_set(mode='OBJECT')
mod=meshobj.modifiers.new('Skin','ARMATURE'); mod.object=rig; meshobj.parent=rig
rig.show_in_front=True
def rotation(name,axis,degrees):
    p=rig.pose.bones[name]; p.rotation_mode='QUATERNION'
    local=p.bone.matrix_local.to_3x3().inverted()@Vector(axis)
    p.rotation_quaternion=Quaternion(local,math.radians(degrees))
def pose(phase,amplitude):
    for p in rig.pose.bones:p.rotation_quaternion=Quaternion(); p.location=(0,0,0)
    for side,label in [(1,'L'),(-1,'R')]:
        rotation('shoulder_'+label,(0,1,0),-side*(6+amplitude*42*math.sin(phase)))
        rotation('elbow_'+label,(0,1,0),-side*amplitude*14*math.sin(phase-.55))
        rotation('wrist_'+label,(0,1,0),side*amplitude*10*math.sin(phase-.9))
        rotation('tip_'+label,(0,0,1),side*amplitude*5*math.sin(phase-.6))
    rotation('tail',(1,0,0),amplitude*4*math.sin(phase+.5))
actions={}
for name,end in [('Fly',25),('Glide',49),('FlyToGlide',13),('GlideToFly',13)]:
    rig.animation_data_create(); action=bpy.data.actions.new('A_OH_Pigeon_'+name); action.use_fake_user=True; rig.animation_data.action=action
    for frame in range(1,end+1):
        t=(frame-1)/(end-1)
        if name=='Fly': phase=t*math.tau; amp=1
        elif name=='Glide': phase=0; amp=0
        elif name=='FlyToGlide': phase=t*math.pi; amp=1-(3*t*t-2*t*t*t)
        else: phase=(t-1)*math.pi; amp=3*t*t-2*t*t*t
        pose(phase,amp)
        for p in rig.pose.bones:
            p.keyframe_insert(data_path='rotation_quaternion',frame=frame,group=p.name)
    actions[name]=(action,end)
    rig.animation_data.action=None

def vertices_at(action,frame):
    rig.animation_data.action=action; scene.frame_set(frame); bpy.context.view_layer.update()
    evaluated=meshobj.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=evaluated.to_mesh()
    result=[v.co.copy() for v in me.vertices]; evaluated.to_mesh_clear(); return result
checks={}
for name in ['Fly','Glide']:
    a,end=actions[name]; first=vertices_at(a,1); last=vertices_at(a,end)
    err=max((p-q).length for p,q in zip(first,last)); assert err<1e-5,(name,err)
    checks[name]={'loop_vertex_error_m':err,'frames':end,'fps':48}
for trans,src,sframe,dst,dframe in [('FlyToGlide','Fly',1,'Glide',1),('GlideToFly','Glide',1,'Fly',1)]:
    a,end=actions[trans]
    start=vertices_at(a,1); finish=vertices_at(a,end)
    ref1=vertices_at(actions[src][0],sframe); ref2=vertices_at(actions[dst][0],dframe)
    err=max(max((p-q).length for p,q in zip(start,ref1)),max((p-q).length for p,q in zip(finish,ref2)))
    assert err<1e-5,(trans,err); checks[trans]={'endpoint_error_m':err,'frames':end}
assert all(abs(sum(g.weight for g in v.groups)-1)<1e-5 for v in meshobj.data.vertices)
rig.animation_data.action=actions['Fly'][0]; scene.frame_start=1; scene.frame_end=25; scene.frame_set(1)
# Neutral bind pose for skeletal mesh export, per-clip FBX files for animation.
bpy.ops.object.select_all(action='DESELECT'); rig.select_set(True); meshobj.select_set(True); bpy.context.view_layer.objects.active=rig
rig.animation_data.action=None
for p in rig.pose.bones:p.rotation_quaternion=Quaternion()
fbx=dict(use_selection=True,object_types={'ARMATURE','MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,add_leaf_bones=False,bake_anim_use_nla_strips=False,bake_anim_use_all_actions=False,bake_anim_simplify_factor=0)
bpy.ops.export_scene.fbx(filepath=str(OUT/'SK_OH_Pigeon.fbx'),bake_anim=False,**fbx)
for name,(a,end) in actions.items():
    rig.animation_data.action=a; scene.frame_start=1; scene.frame_end=end
    bpy.ops.export_scene.fbx(filepath=str(OUT/('A_OH_Pigeon_'+name+'.fbx')),bake_anim=True,**fbx)
rig.animation_data.action=actions['Fly'][0]; scene.frame_start=1; scene.frame_end=25; scene.frame_set(1)
scene.render.engine='CYCLES'; scene.cycles.samples=20; scene.render.resolution_x=720; scene.render.resolution_y=600; scene.render.resolution_percentage=100
scene.world.color=(.22,.22,.22)
bpy.ops.object.camera_add(location=(.60,.73,.39)); cam=bpy.context.object; cam.rotation_euler=(Vector((0,0,.03))-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.type='ORTHO'; cam.data.ortho_scale=1.02; scene.camera=cam
for loc,power,size in [((.2,.5,1),90,1),((-.5,-.2,.4),60,.7)]:
    bpy.ops.object.light_add(type='AREA',location=loc); o=bpy.context.object; o.data.energy=power; o.data.shape='DISK'; o.data.size=size; o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
report=dict(status='rig_and_clip_checks_pass',bones=len(rig.data.bones),vertices=len(meshobj.data.vertices),triangles=sum(len(p.vertices)-2 for p in meshobj.data.polygons),weights_normalized=True,clips=checks,root_motion='in_place',unreal_import='pending',limitations=['first procedural bird appearance; user visual review pending','no flight paths or animation controller yet','loop boundary tested, not full collision or anatomical validation'])
(OUT/'verification.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'pigeon_rig.blend'))
for frame in [1,7,13,19]:
    scene.frame_set(frame); scene.render.filepath=str(OUT/('fly_%02d.png'%frame)); bpy.ops.render.render(write_still=True)
print('PIGEON_RIG_PASS',json.dumps(report))
