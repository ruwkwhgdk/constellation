import bpy,json,sys
from pathlib import Path
P=Path(__file__).parent
S=Path('C:/Users/User/.codex/visualizations/2026/09/19/01a0ba3a-ca09-73e0-b9bd-7084c8f3096b/SwordPull_Heroine01/Heroine_Sword_Final03.blend')
bpy.ops.wm.open_mainfile(filepath=str(S));s=bpy.context.scene
print('OBJECTS',[(o.name,o.type) for o in s.objects],flush=True)
r=bpy.data.objects['Heroine_Rebuild_GameSkeleton'];sw=bpy.data.objects['Sword_proxy']
sys.path.insert(0,'C:/Users/User/.codex/skills/lida-avatar-workflow/scripts');import lida_model_tools as lt
meshes=[o for o in s.objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==r for m in o.modifiers)]
(P/'audit_before.json').write_text(json.dumps(lt.audit_meshes(meshes,r),indent=2));(P/'snapshot_before.json').write_text(json.dumps(lt.snapshot_meshes(meshes,r,source_path=str(S)),indent=2))
for f in [100,355,415,457,523]:
 s.frame_set(f)
 print('FRAME',f,'SWORD',list(sw.matrix_world.translation))
 for side in ['r','l']:
  m=sw.matrix_world.inverted()@r.matrix_world@r.pose.bones['hand_'+side].matrix
  print(side,'rel',list(m.translation),'quat',list(m.to_quaternion()))
print('INSPECTION_DONE',flush=True)
