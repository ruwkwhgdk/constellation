import bpy,json,sys,math
from pathlib import Path
P=Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath=str(P/'Heroine_Sword_ArmCorrection03.blend'));s=bpy.context.scene;r=bpy.data.objects['Heroine_Rebuild_GameSkeleton'];sw=bpy.data.objects['Sword_proxy']
sys.path.insert(0,'C:/Users/User/.codex/skills/lida-avatar-workflow/scripts');import lida_model_tools as lt
meshes=[o for o in s.objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==r for m in o.modifiers)]
(P/'audit_after03.json').write_text(json.dumps(lt.audit_meshes(meshes,r),indent=2));snap=lt.snapshot_meshes(meshes,r,source_path=bpy.data.filepath);(P/'snapshot_after03.json').write_text(json.dumps(snap,indent=2));cmp=lt.compare_snapshots(json.loads((P/'snapshot_before.json').read_text()),snap);(P/'preservation03.json').write_text(json.dumps(cmp,indent=2));assert cmp['equal'];print('MESH_PRESERVATION_VERIFIED',flush=True)
metrics=[];prev={}
for half in range(2,1479):
 f=half/2;s.frame_set(int(f),subframe=f%1);row={'frame':f}
 for side in ['r','l']:
  a,e,w,m=[r.matrix_world@r.pose.bones[n+'_'+side].head for n in ['upperarm','lowerarm','hand','middle_01']]
  q=(r.matrix_world@r.pose.bones['hand_'+side].matrix).to_quaternion()
  row[side]={'elbow_flex':180-math.degrees((a-e).angle(w-e)),'wrist_axis_angle':math.degrees((w-e).angle(m-w)),'sword_local_wrist':list(sw.matrix_world.inverted()@w),'half_frame_rotation_degrees':math.degrees(q.rotation_difference(prev[side]).angle) if side in prev else 0};prev[side]=q
 metrics.append(row)
(P/'joint_continuity03.json').write_text(json.dumps(metrics,indent=2));print('CONTINUITY_CHECKED',flush=True)


