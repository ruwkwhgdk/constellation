import bpy,json
from pathlib import Path
P=Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath=str(P/'Heroine_Sword_ArmCorrection03.blend'));s=bpy.context.scene;r=bpy.data.objects['Heroine_Rebuild_GameSkeleton']
for f in [100,278,457,490,523]:
 s.frame_set(f)
 print(f,{n:{'q':list(r.pose.bones[n].rotation_quaternion),'p':list(r.pose.bones[n].matrix.translation)} for n in ['upperarm_r','lowerarm_r','hand_r']})
