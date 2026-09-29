import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P.parent/'DetailFinish2/Delivery/Heroine_DetailFinish2.blend'))
report={'units':bpy.context.scene.unit_settings.scale_length,'objects':[]}
for o in bpy.context.scene.objects:
 if o.type=='MESH':report['objects'].append({'name':o.name,'matrix':[list(r) for r in o.matrix_world],'dimensions':list(o.dimensions),'modifiers':[m.type for m in o.modifiers]})
(P/'source_inspect.json').write_text(json.dumps(report,indent=2))
if (P/'Quinn_Reference.fbx').exists():
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.fbx(filepath=str(P/'Quinn_Reference.fbx'))
 arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
 (P/'reference_bones.json').write_text(json.dumps({'matrix':[list(r) for r in arm.matrix_world],'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local)} for b in arm.data.bones]},indent=2))
 bpy.ops.wm.save_as_mainfile(filepath=str(P/'reference.blend'))
