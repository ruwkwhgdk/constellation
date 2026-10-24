import bpy,json
from pathlib import Path
s=bpy.context.scene
r=bpy.data.objects["Heroine_Rebuild_GameSkeleton"]
previous={}
flips=[]
for frame in range(1,s.frame_end+1):
    s.frame_set(frame)
    for b in r.pose.bones:
        q=b.rotation_quaternion.copy()
        if b.name in previous and q.dot(previous[b.name])<0:
            flips.append({"frame":frame,"bone":b.name})
        previous[b.name]=q
result={"frames":[1,s.frame_end],"quaternion_sign_flips":flips,
        "scope":"Stored pose quaternion continuity only; not a visual acceptance test"}
(Path(bpy.data.filepath).parent/"key_continuity.json").write_text(json.dumps(result,indent=2))
print(json.dumps(result),flush=True)
