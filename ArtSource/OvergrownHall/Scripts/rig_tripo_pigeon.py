"""Skin approved Tripo geometry; preserve topology, UVs and packed PBR maps."""
import bpy, math, json
from pathlib import Path
from mathutils import Vector, Quaternion
BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'Bird/Tripo_Rig_v001'; OUT.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.import_scene.gltf(filepath=str(BASE/'Bird/Tripo_v001/OH_Pigeon_Tripo_v001.glb'))
scene=bpy.context.scene; scene.render.fps=48; scene.world=bpy.data.worlds.new('World')
meshobj=next(o for o in scene.objects if o.type=='MESH')
bpy.context.view_layer.objects.active=meshobj
meshobj.select_set(True)
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
# Coordinates below are measured in the original model's world axes, face -Y.
scale=.68/.9811401368
for v in meshobj.data.vertices: v.co*=scale
meshobj.name='SK_OH_Pigeon'
for im in bpy.data.images:
    if im.packed_file:
        im.filepath_raw=str(OUT/(im.name.rsplit('.',1)[0]+'.png')); im.file_format='PNG'; im.save()
bpy.ops.object.armature_add(); rig=bpy.context.object; rig.name='RIG_OH_Pigeon_Tripo'
bpy.ops.object.mode_set(mode='EDIT'); rig.data.edit_bones.remove(rig.data.edit_bones[0])
def bone(name,a,b,parent=None):
    e=rig.data.edit_bones.new(name); e.head=Vector(a)*scale; e.tail=Vector(b)*scale
    if parent: e.parent=rig.data.edit_bones[parent]
bone('root',(0,0,0),(0,0,.1))
bone('body',(0,0,.2),(0,0,.36),'root')
bone('neck',(0,0,.36),(0,-.08,.47),'body')
bone('head',(0,-.08,.47),(0,-.2,.51),'neck')
bone('tail',(0,.1,.22),(0,.28,.13),'body')
for side,label in [(1,'L'),(-1,'R')]:
    bone('shoulder_'+label,(side*.09,.015,.33),(side*.23,.005,.47),'body')
    bone('elbow_'+label,(side*.23,.005,.47),(side*.35,.03,.58),'shoulder_'+label)
    bone('wrist_'+label,(side*.35,.03,.58),(side*.47,.07,.70),'elbow_'+label)
    bone('tip_'+label,(side*.47,.07,.70),(side*.49,.1,.74),'wrist_'+label)
    bone('leg_'+label,(side*.06,-.01,.19),(side*.07,-.04,.065),'body')
    bone('foot_'+label,(side*.07,-.04,.065),(side*.07,-.17,.02),'leg_'+label)
bpy.ops.object.mode_set(mode='OBJECT')
groups={b.name:meshobj.vertex_groups.new(name=b.name) for b in rig.data.bones}
def smooth(a,b,x):
    t=max(0,min(1,(x-a)/(b-a))); return t*t*(3-2*t)
for v in meshobj.data.vertices:
    x,y,z=v.co/scale; ax=abs(x); label='L' if x>=0 else 'R'
    # Body stays rigid; blend only the shoulder attachment into the wing fan.
    w=smooth(.09,.17,ax)*smooth(.21,.32,z)
    weights={}
    if z<.18:
        f=1-smooth(.055,.105,z); weights={'foot_'+label:f,'leg_'+label:1-f}
        if y>.12: weights={'tail':1}
    elif y>.15 and z<.3: weights={'tail':1}
    elif z>.40 and ax<.10:
        h=smooth(.41,.48,z); weights={'neck':1-h,'head':h}
    else: weights={'body':1}
    weights={k:value*(1-w) for k,value in weights.items()}
    e=smooth(.20,.27,ax); r=smooth(.32,.39,ax); t=smooth(.44,.485,ax)
    for name,value in [('shoulder',1-e),('elbow',e*(1-r)),('wrist',r*(1-t)),('tip',r*t)]:
        if value*w>0: weights[name+'_'+label]=value*w
    weights=sorted(weights.items(),key=lambda p:p[1],reverse=True)[:4]; total=sum(v for _,v in weights)
    for name,value in weights:
        if value>0: groups[name].add([v.index],value/total,'REPLACE')
mod=meshobj.modifiers.new('Skin','ARMATURE'); mod.object=rig; mod.use_deform_preserve_volume=False
meshobj.parent=rig; rig.show_in_front=True
# Reuse validated clip/export mechanics, with this model's raised rest pose.
source=(BASE/'Scripts/build_pigeon.py').read_text()
tail=source[source.index('def rotation(name,axis,degrees):'):]
tail=tail.replace('-side*(6+amplitude*42*math.sin(phase))','side*(38-amplitude*38*math.sin(phase))')
tail=tail.replace('amp*14','amp*8').replace('amplitude*14','amplitude*8')
tail=tail.replace("rotation('tail',(1,0,0),amplitude*4*math.sin(phase+.5))", "rotation('body',(1,0,0),-18)\n    rotation('tail',(1,0,0),amplitude*3*math.sin(phase+.5))")
tail=tail.replace('location=(.60,.73,.39)','location=(.68,-1.05,.50)')
tail=tail.replace('Vector((0,0,.03))','Vector((0,0,.24))')
tail=tail.replace('((.2,.5,1),90,1)','((.2,-.5,1),90,1)')
tail=tail.replace('first procedural bird appearance; user visual review pending','approved Tripo appearance; new skin deformation review pending')
exec(compile(tail,__file__,'exec'))
