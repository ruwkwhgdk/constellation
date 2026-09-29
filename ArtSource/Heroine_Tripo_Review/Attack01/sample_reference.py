import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(P/'Reference_Attack01.fbx'))
r=next(o for o in bpy.data.objects if o.type=='ARMATURE');s=bpy.context.scene
a=r.animation_data.action;start,end=a.frame_range
rows=[]
for i in range(int(end-start)+1):
 f=start+i;s.frame_set(int(f),subframe=f%1)
 rows.append({'frame':f,'bones':{p.name:{'head':list(r.matrix_world@p.head),'tail':list(r.matrix_world@p.tail),'matrix':[list(row) for row in r.matrix_world@p.matrix]} for p in r.pose.bones}})
report={'fps':s.render.fps,'start':start,'end':end,'scale':list(r.scale),'samples':rows,'rest':{b.name:[list(row) for row in r.matrix_world@b.matrix_local] for b in r.data.bones}}
(P/'reference_motion.json').write_text(json.dumps(report))
print('REFERENCE',report['fps'],start,end,list(report['rest']))
