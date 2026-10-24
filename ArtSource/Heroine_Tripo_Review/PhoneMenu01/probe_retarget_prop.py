import bpy,json
from pathlib import Path
s=bpy.context.scene;s.frame_set(180);r=bpy.data.objects["Heroine_Rebuild_GameSkeleton"]
data={"rig_world":[list(x) for x in r.matrix_world],"bones":{}}
for n in ("hand_l","middle_01_l","index_01_l","pinky_01_l","thumb_03_l","hand_r","index_03_r"):
 data["bones"][n]={"head":list(r.matrix_world@r.pose.bones[n].head),"tail":list(r.matrix_world@r.pose.bones[n].tail)}
p=bpy.data.objects.get("Phone_ReviewCube")
if p:data["phone"]=[list(x) for x in p.matrix_world]
Path(__file__).with_name("retarget_prop_probe.json").write_text(json.dumps(data,indent=2))
