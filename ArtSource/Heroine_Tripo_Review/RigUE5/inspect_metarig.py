import bpy,json
from pathlib import Path
bpy.ops.preferences.addon_enable(module='rigify')
bpy.ops.object.armature_human_metarig_add()
a=bpy.context.object
Path(__file__).with_name('metarig.json').write_text(json.dumps([{'name':b.name,'head':list(b.head_local),'tail':list(b.tail_local),'parent':b.parent.name if b.parent else None,'type':a.pose.bones[b.name].rigify_type} for b in a.data.bones],indent=2))
