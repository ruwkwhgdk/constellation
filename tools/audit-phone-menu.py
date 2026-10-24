"""Read-only asset audit; run in a separate Unreal commandlet. Never saves assets."""
import unreal as u
import json
from pathlib import Path
out = Path(u.Paths.project_dir()) / "Saved/PhoneMenu/Audit01"
out.mkdir(parents=True, exist_ok=False)
paths = [
 "/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine",
 "/Game/Constellation/Characters/Heroine/Blueprints/BP_PlayerController",
 "/Game/Constellation/Characters/Heroine/Blueprints/ABP_Player_Heroine",
 "/Game/Constellation/Input/IAC_Default",
]
rows=[]
sub=u.get_engine_subsystem(u.SubobjectDataSubsystem)
fn=u.SubobjectDataBlueprintFunctionLibrary
for path in paths:
 obj=u.load_asset(path)
 assert obj,path
 row={"path":path}
 if isinstance(obj,u.Blueprint):
  (out/(obj.get_name()+".txt")).write_text(u.ResourceRecoveryLibrary.export_blueprint_graphs(obj),encoding="utf-8")
  row["components"]=[]
  for h in sub.k2_gather_subobject_data_for_blueprint(obj):
   c=fn.get_object_for_blueprint(fn.get_data(h),obj)
   if not c: continue
   d={"name":c.get_name(),"class":c.get_class().get_name(),"properties":{}}
   for p in ("skeletal_mesh_asset","anim_class","relative_location","relative_rotation","target_arm_length","socket_offset","field_of_view"):
    try: d["properties"][p]=str(c.get_editor_property(p))
    except Exception: pass
   row["components"].append(d)
 elif isinstance(obj,u.InputMappingContext):
  row["keys"]=[{"action":str(m.action),"key":str(m.key)} for m in obj.get_editor_property("default_key_mappings").get_editor_property("mappings")]
 rows.append(row)
(out/"assets.json").write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding="utf-8")
u.log("PHONE_AUDIT_COMPLETE")
