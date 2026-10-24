import bpy, json
from pathlib import Path
out=Path(__file__).parent/"Audit01"
out.mkdir(parents=True,exist_ok=False)
rows=[]
for o in bpy.data.objects:
 d={"name":o.name,"type":o.type,"location":list(o.location),"dimensions":list(o.dimensions),"hidden":o.hide_render}
 if o.type=="ARMATURE":
  d["bones"]=[{"name":b.name,"parent":b.parent.name if b.parent else None,"head":list(b.head_local),"tail":list(b.tail_local)} for b in o.data.bones]
  d["action"]=o.animation_data.action.name if o.animation_data and o.animation_data.action else None
 if o.type=="MESH":
  d["vertices"]=len(o.data.vertices)
  d["materials"]=[m.name if m else None for m in o.data.materials]
  d["armature"]=o.find_armature().name if o.find_armature() else None
 rows.append(d)
(out/"scene.json").write_text(json.dumps({"file":bpy.data.filepath,"objects":rows,"actions":[{"name":a.name,"range":list(a.frame_range)} for a in bpy.data.actions]},indent=2),encoding="utf-8")
print("PHONE_SOURCE_INSPECTED",str(out))
