"""Approved concept 02: editable game-review mesh and bone-only liquid Idle.
Run using the project tools/run-blender.ps1 guard, in a fresh background process.
"""
import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

OUT = Path(__file__).resolve().parent
OUT.mkdir(exist_ok=True)
PREVIEW = OUT / 'Preview'
PREVIEW.mkdir(exist_ok=True)
S = bpy.context.scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
S.unit_settings.system = 'METRIC'
S.unit_settings.scale_length = 1.0
S.render.fps = 24
S.frame_start, S.frame_end = 1, 97

def active(o):
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o

def mat(name, color, roughness, metallic=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Metallic'].default_value = metallic
    return m, p

gel, gp = mat('M_Slime_IndigoGel', (.075, .008, .34), .23)
gp.inputs['IOR'].default_value = 1.38
gp.inputs['Coat Weight'].default_value = .42
gp.inputs['Coat Roughness'].default_value = .19
gp.inputs['Subsurface Weight'].default_value = .065
gp.inputs['Subsurface Radius'].default_value = (.16, .08, .24)
# A restrained facing tint gives the approved light violet thin-edge reading.
nt = gel.node_tree
facing = nt.nodes.new('ShaderNodeLayerWeight')
facing.inputs['Blend'].default_value = .4
ramp = nt.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = .08
ramp.color_ramp.elements[0].color = (.025, .0015, .15, 1)
ramp.color_ramp.elements[1].position = .86
ramp.color_ramp.elements[1].color = (.13, .012, .46, 1)
nt.links.new(facing.outputs['Fresnel'], ramp.inputs[0])
nt.links.new(ramp.outputs[0], gp.inputs['Base Color'])
eye_mat, ep = mat('M_Slime_EyeCream', (.96, .88, .65), .25)
ep.inputs['Emission Color'].default_value = (.96, .88, .68, 1)
ep.inputs['Emission Strength'].default_value = .65

def mesh(name, verts, faces, material=gel):
    d = bpy.data.meshes.new(name)
    d.from_pydata(verts, [], faces)
    d.update()
    o = bpy.data.objects.new(name, d)
    S.collection.objects.link(o)
    o.data.materials.append(material)
    for p in d.polygons: p.use_smooth = True
    return o

def catmull(points, per=6):
    result=[]
    for i in range(len(points)-1):
        a,b,c,d = [Vector(points[min(max(j,0),len(points)-1)]) for j in (i-1,i,i+1,i+2)]
        for k in range(per):
            t=k/per
            result.append(tuple(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)))
    return result+[points[-1]]

profile = catmull([(0.014,.02),(.018,.74),(.042,1.04),(.072,1.07),(.115,.98),
                    (.20,.96),(.40,.94),(.64,.84),(.86,.68),(1.06,.46),(1.20,.22),(1.25,.015)], 5)
verts=[]; faces=[]; N=112
for z,r in profile:
    for j in range(N):
        a=2*math.pi*j/N
        lobe=(.095*math.sin(5*a+.4)+.055*math.cos(3*a-.8))*math.exp(-((z-.045)/.105)**2)
        rr=max(.003,r+lobe)
        verts.append((rr*math.cos(a),rr*.86*math.sin(a),max(.009,z)))
for i in range(len(profile)-1):
    for j in range(N):
        k=i*N+j; q=i*N+(j+1)%N
        faces.append((k,q,q+N,k+N))
faces.append(tuple(range(N-1,-1,-1)))
faces.append(tuple((len(profile)-1)*N+j for j in range(N)))
body=mesh('Slime_Body',verts,faces)

crest_path=catmull([(0,.04,1.08,.31),(0,.04,1.28,.255),(.06,-.04,1.46,.20),
                    (.19,-.16,1.53,.16),(.32,-.28,1.46,.132),(.37,-.34,1.35,.115),
                    (.36,-.35,1.29,.04),(.35,-.35,1.28,.002)], 6)
cv=[]; cf=[]; CN=40
for i,p in enumerate(crest_path):
    tangent=Vector(crest_path[min(i+1,len(crest_path)-1)][:3])-Vector(crest_path[max(0,i-1)][:3])
    tangent.normalize()
    u=tangent.cross(Vector((0,1,0))).normalized()
    v=tangent.cross(u).normalized()
    for j in range(CN):
        a=j*math.tau/CN
        cv.append(Vector(p[:3])+max(.002,p[3])*(u*math.cos(a)+v*math.sin(a)))
for i in range(len(crest_path)-1):
    for j in range(CN):
        k=i*CN+j; q=i*CN+(j+1)%CN
        cf.append((k,q,q+CN,k+CN))
cf.extend([tuple(range(CN-1,-1,-1)),tuple((len(crest_path)-1)*CN+j for j in range(CN))])
crest=mesh('Crest_build',cv,cf)
active(body); crest.select_set(True)
bpy.ops.object.join()
rem=body.modifiers.new('Continuous liquid surface', 'REMESH')
rem.mode='VOXEL'; rem.voxel_size=.016
bpy.ops.object.modifier_apply(modifier=rem.name)
sm=body.modifiers.new('Surface tension polish', 'SMOOTH')
sm.factor=.7; sm.iterations=5
bpy.ops.object.modifier_apply(modifier=sm.name)
dec=body.modifiers.new('Game topology density', 'DECIMATE')
dec.ratio=.17
bpy.ops.object.modifier_apply(modifier=dec.name)
for p in body.data.polygons: p.use_smooth=True
relax=body.modifiers.new('Final fluid rim polish','SMOOTH')
relax.factor=.5;relax.iterations=3
bpy.ops.object.modifier_apply(modifier=relax.name)
floor_z=min(v.co.z for v in body.data.vertices)
for v in body.data.vertices:v.co.z-=floor_z
active(body)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.015)
bpy.ops.object.mode_set(mode='OBJECT')
tree=BVHTree.FromPolygons([v.co for v in body.data.vertices],[list(p.vertices) for p in body.data.polygons])

def surface_y(x,z):
    hit=tree.ray_cast(Vector((x,-3,z)),Vector((0,1,0)),6)[0]
    return hit.y if hit else -.34

# True circular eyes when viewed straight on, conformed to the body.
eyes=[]
for sign in (-1,1):
    ev=[]; ef=[]; ex=sign*.27; ez=.65; radius=.114
    ev.append((ex,surface_y(ex,ez)-.009,ez))
    for k in range(1,7):
        r=radius*k/6
        for j in range(64):
            a=j*math.tau/64; x=ex+r*math.cos(a); z=ez+r*math.sin(a)
            ev.append((x,surface_y(x,z)-.008-.003*(1-(r/radius)**2),z))
    for j in range(64): ef.append((0,1+j,1+(j+1)%64))
    for k in range(5):
        for j in range(64):
            a=1+k*64+j; b=1+k*64+(j+1)%64
            ef.append((a,a+64,b+64,b))
    o=mesh('Eye_L' if sign<0 else 'Eye_R',ev,ef,eye_mat)
    eyes.append(o)

# New, explicitly independent export rig. Root remains at floor origin.
ad=bpy.data.armatures.new('Slime_Liquid_Rig')
rig=bpy.data.objects.new('Slime_Liquid_Rig',ad); S.collection.objects.link(rig)
active(rig); bpy.ops.object.mode_set(mode='EDIT')
def bone(name,head,tail,parent=None):
    b=ad.edit_bones.new(name); b.head=head; b.tail=tail
    if parent: b.parent=ad.edit_bones[parent]
    return b
bone('root',(0,0,0),(0,0,.18))
bone('center',(0,0,.18),(0,0,.78),'root')
bone('top',(0,0,.82),(0,0,1.24),'center')
bone('crest',(0,0,1.24),(.22,-.15,1.52),'top')
bone('crest_tip',(.22,-.15,1.52),(.36,-.35,1.30),'crest')
bone('drop',(.36,-.35,1.26),(.36,-.35,1.36),'root')
bpy.ops.object.mode_set(mode='OBJECT')

def smoothstep(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)))
    return t*t*(3-2*t)

def weight(o):
    groups={n:o.vertex_groups.new(name=n) for n in ['root','center','top','crest','crest_tip']}
    for v in o.data.vertices:
        x,y,z=v.co
        wc=smoothstep(.94,1.30,z)
        tip=wc*smoothstep(.12,.36,x)*smoothstep(-.10,-.30,y)
        cr=wc-tip
        top=(1-wc)*smoothstep(.62,1.05,z)*.70
        root=1-smoothstep(.04,.34,z)
        vals={'root':root,'center':max(0,1-root-top-cr-tip),'top':top,'crest':cr,'crest_tip':tip}
        total=sum(vals.values())
        for n,w in vals.items():
            if w>0: groups[n].add([v.index],w/total,'REPLACE')
    mod=o.modifiers.new('Liquid deformation','ARMATURE'); mod.object=rig
    o.parent=rig
for o in [body]+eyes: weight(o)

bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=20,radius=1,location=(.36,-.35,1.26))
drop=bpy.context.object; drop.name='Slime_Droplet'
drop.scale=(.065,.065,.08)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
for v in drop.data.vertices:
    t=max(0,v.co.z/.08)
    v.co.x*=1-.6*t
    v.co.y=v.co.y*(1-.6*t)+.02*t*t
    v.co.z+=.035*t*t
drop.data.materials.append(gel)
for p in drop.data.polygons:p.use_smooth=True
g=drop.vertex_groups.new(name='drop');g.add(list(range(len(drop.data.vertices))),1,'REPLACE')
mod=drop.modifiers.new('Droplet deformation','ARMATURE');mod.object=rig;drop.parent=rig

def lerp(a,b,t): return a+(b-a)*t
drop_rest=Vector((.36,-.35,1.26))
rest_rotation=rig.data.bones['drop'].matrix_local.to_3x3()
for f in range(1,98):
    t=(f-1)/96; wave=math.sin(math.tau*t)
    center=rig.pose.bones['center']; center.scale=(1-.016*wave,1+.028*wave,1-.012*wave)
    center.location=(0,0,0)
    top=rig.pose.bones['top']; top.rotation_mode='XYZ'
    top.rotation_euler=(.015*math.sin(math.tau*t-.35),.017*wave,0)
    crest=rig.pose.bones['crest'];crest.rotation_mode='XYZ'
    crest.rotation_euler=(.04*math.sin(math.tau*t-.7),.04*math.sin(math.tau*t-.5),.025*wave)
    tip=rig.pose.bones['crest_tip'];tip.rotation_mode='XYZ'
    tip.rotation_euler=(.055*math.sin(math.tau*t-1.1),0,.025*wave)
    # A bead grows from the crest, runs down the cheek, detaches briefly,
    # and flattens into the existing wet foot. It resets only while hidden.
    q=t
    if q<.16:
        u=smoothstep(0,.16,q); pos=drop_rest+Vector((0,-.008,-.065*u))
        scale=(lerp(.015,.76,u),lerp(.015,.76,u),lerp(.015,1.3,u))
    elif q<.60:
        u=smoothstep(.16,.60,q); z=lerp(1.195,.32,u);x=lerp(.36,.57,u)
        y=surface_y(x,z)-.025
        pos=Vector((x,y,z));scale=(.78,.56,1.25)
    elif q<.72:
        u=(q-.60)/.12; z=lerp(.32,.095,u*u)
        pos=Vector((lerp(.57,.61,u),lerp(surface_y(.57,.32)-.025,-.86,u),z))
        scale=(.82,.74,lerp(1.25,.75,u))
    elif q<.90:
        u=smoothstep(.72,.90,q)
        pos=Vector((.61,-.86,lerp(.095,.025,u)))
        scale=(lerp(.82,2.0,u),lerp(.74,1.55,u),lerp(.75,.06,u))
    else:
        u=smoothstep(.90,1,q);pos=Vector((.61,-.86,lerp(.025,.012,u)))
        scale=(lerp(2,.015,u),lerp(1.55,.015,u),lerp(.06,.015,u))
    if f==97: pos=drop_rest+Vector((0,-.008,0));scale=(.015,.015,.015)
    pb=rig.pose.bones['drop'];pb.location=rest_rotation.inverted()@(pos-drop_rest);pb.scale=(scale[0],scale[2],scale[1])
    for p in [center,top,crest,tip,pb]:
        p.keyframe_insert('location',frame=f,group=p.name)
        p.keyframe_insert('rotation_euler',frame=f,group=p.name)
        p.keyframe_insert('scale',frame=f,group=p.name)
rig.animation_data.action.name='AS_Slime_Idle_Liquid_4s'
for layer in rig.animation_data.action.layers:
    for strip in layer.strips:
        for bag in strip.channelbags:
            for fc in bag.fcurves:
                for k in fc.keyframe_points: k.interpolation='LINEAR'

def point(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
floor,fm=mat('Studio_WarmGray',(.63,.61,.57),.8)
bpy.ops.mesh.primitive_plane_add(size=200)
ground=bpy.context.object;ground.name='Studio_Ground';ground.data.materials.append(floor)
ground.location.z=-.004
world=bpy.data.worlds.new('Studio_World');world.use_nodes=True;S.world=world
next(n for n in world.node_tree.nodes if n.type=='BACKGROUND').inputs[0].default_value=(.44,.46,.55,1)
next(n for n in world.node_tree.nodes if n.type=='BACKGROUND').inputs[1].default_value=.35
for name,loc,power,color,size in [('Key',(-3,-4,5),650,(.89,.93,1),3.2),('Fill',(3,-2,3),420,(.70,.72,1),3),('Rim',(1,3,4),950,(.68,.57,1),2.5)]:
    ld=bpy.data.lights.new(name,'AREA');ld.energy=power;ld.color=color;ld.shape='DISK';ld.size=size
    ob=bpy.data.objects.new(name,ld);S.collection.objects.link(ob);ob.location=loc;point(ob,(0,0,.7))
cd=bpy.data.cameras.new('Review_Camera');cam=bpy.data.objects.new('Review_Camera',cd);S.collection.objects.link(cam);S.camera=cam
cd.type='ORTHO';cd.ortho_scale=3.05
cam.location=(3,-6,2.65);point(cam,(0,0,.76))
S.render.engine='CYCLES';S.cycles.samples=24;S.cycles.use_denoising=True
S.render.resolution_x=1100;S.render.resolution_y=1000;S.render.resolution_percentage=100
S.render.image_settings.file_format='PNG'
S.view_settings.view_transform='AgX'
S.frame_set(1)
rig.show_in_front=True
active(body)
for a in bpy.context.screen.areas:
    if a.type=='VIEW_3D':
        a.spaces.active.region_3d.view_perspective='CAMERA'
        a.spaces.active.shading.type='MATERIAL'
S['design_reference']='../Concepts/2026-10-13/slime-form-refinement-02.png'
S['delivery_note']='Model review. New rig; existing Unreal skeleton/ABP replacement not performed.'
S['drop_axis_and_tail_polished']=True
S['body_scale_axis_polished']=True
sys.path.insert(0,str(OUT))
from refine_slime import refine
refine(S,OUT)
eyes=[bpy.data.objects[n] for n in ['Eye_L','Eye_R']]  # Revision 03 restores narrow original eyes.
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Slime_Liquid.blend'))

# Mesh and animation travel together; no modifiers, constraints or drivers needed in UE.
bpy.ops.object.select_all(action='DESELECT')
for o in [rig,body,drop]+eyes:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(OUT/'SK_Slime_Liquid_Idle.fbx'),use_selection=True,
    object_types={'ARMATURE','MESH'},add_leaf_bones=False,axis_forward='-Z',axis_up='Y',
    apply_unit_scale=True,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,
    bake_anim_simplify_factor=0,mesh_smooth_type='FACE',use_mesh_modifiers=True,path_mode='COPY',embed_textures=True)

stats={'blender':bpy.app.version_string,'fps':24,'frames':[1,97],'duration_seconds':4,
       'rig_bones':list(ad.bones.keys()),'units':'meters','forward':'-Y','pivot':'floor',
       'meshes':{o.name:{'vertices':len(o.data.vertices),'triangles':sum(len(p.vertices)-2 for p in o.data.polygons)} for o in [body,drop]+eyes},
       'body_bounds_m':[[min(v.co[i] for v in body.data.vertices),max(v.co[i] for v in body.data.vertices)] for i in range(3)]}
(OUT/'build-report.json').write_text(json.dumps(stats,indent=2),encoding='utf8')
S.render.filepath=str(PREVIEW/'three-quarter.png');bpy.ops.render.render(write_still=True)
cam.location=(0,-6,2.25);point(cam,(0,0,.78));S.render.filepath=str(PREVIEW/'front.png');bpy.ops.render.render(write_still=True)
cam.location=(6,0,1.6);point(cam,(0,0,.78));S.render.filepath=str(PREVIEW/'side.png');bpy.ops.render.render(write_still=True)
print('SLIME_BUILD_COMPLETE',json.dumps(stats))
