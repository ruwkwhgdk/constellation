import bpy,json
from pathlib import Path
p=Path('C:/Users/User/Documents/UnrealProjects/Constellation/ArtSource/Heroine_Tripo_Review/PhoneMenu01/UnrealApply01')
bpy.ops.wm.open_mainfile(filepath=str(p.parent/'OneHandReview04/Heroine_Mixamo_OneHand_Cube08.blend'))
bpy.context.scene.frame_set(80)
r=bpy.data.objects['Heroine_Rebuild_GameSkeleton'];c=bpy.data.objects['Phone_Portrait_ReviewCube']
d={'rig_world':[list(v) for v in r.matrix_world],'cube_world':[list(v) for v in c.matrix_world],'hand':[list(v) for v in r.pose.bones['hand_r'].matrix],'cube_eval':[list(v) for v in c.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world]}
d['vertices']=[list(v.co) for v in c.data.vertices];(p/'source-space.json').write_text(json.dumps(d,indent=2))

