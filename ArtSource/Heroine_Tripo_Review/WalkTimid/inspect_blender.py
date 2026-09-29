import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(P/'Reference_Walk.fbx'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
sc=bpy.context.scene
report={'fps':sc.render.fps,'range':[sc.frame_start,sc.frame_end],'rig':rig.name,'scale':list(rig.scale),'matrix':[list(row) for row in rig.matrix_world],'actions':[(a.name,list(a.frame_range)) for a in bpy.data.actions], 'bones':{b.name:{'head':list(rig.matrix_world@b.head_local),'tail':list(rig.matrix_world@b.tail_local),'parent':b.parent.name if b.parent else None} for b in rig.data.bones}}
frames=[]
for f in range(sc.frame_start,sc.frame_end+1):
 sc.frame_set(f)
 frames.append({'frame':f,'bones':{b.name:{'head':list(rig.matrix_world@b.head),'tail':list(rig.matrix_world@b.tail),'matrix':[list(row) for row in rig.matrix_world@b.matrix]} for b in rig.pose.bones}})
report['samples']=frames
(P/'reference_motion.json').write_text(json.dumps(report))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'reference_walk.blend'))
bpy.ops.wm.open_mainfile(filepath=str(P.parent/'RigReferenceFit/Delivery/Heroine_AnimationRig.blend'))
r=bpy.data.objects['Heroine_AnimationRig']
(P/'rig_controls.json').write_text(json.dumps({'scale':list(r.scale),'bones':{b.name:{'head':list(b.head),'tail':list(b.tail),'parent':b.parent.name if b.parent else None,'props':{k:str(v) for k,v in b.items()},'constraints':[(c.name,c.type) for c in b.constraints]} for b in r.pose.bones}},indent=2))
