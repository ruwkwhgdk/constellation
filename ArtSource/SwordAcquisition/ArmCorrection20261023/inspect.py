import bpy,json,sys
from pathlib import Path
P=Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath=str(P.parent/'GripRevision20261023/Heroine_Sword_RightUpper06.blend'))
r=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE' and 'hand_r' in o.pose.bones)
d={}
for b in r.data.bones:
 if any(k in b.name for k in ['upperarm','lowerarm','hand_']):
  d[b.name]={'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local),'matrix':[list(x) for x in b.matrix_local],'children':[x.name for x in b.children]}
(P/'hierarchy.json').write_text(json.dumps(d,indent=2));print(json.dumps(d))
sys.path.insert(0,'C:/Users/User/.codex/skills/lida-avatar-workflow/scripts');import lida_model_tools as lt
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==r for m in o.modifiers)]
(P/'audit_before.json').write_text(json.dumps(lt.audit_meshes(meshes,r),indent=2))
(P/'snapshot_before.json').write_text(json.dumps(lt.snapshot_meshes(meshes,r,source_path=bpy.data.filepath),indent=2))
