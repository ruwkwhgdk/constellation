import bpy, sys, json
from pathlib import Path
sys.path.insert(0,"C:/Users/User/.codex/skills/lida-avatar-workflow/scripts")
import lida_model_tools as lida
out=Path(__file__).parent/"Audit01"
rig=bpy.data.objects["Heroine_Rebuild_GameSkeleton"]
meshes=[o for o in bpy.data.objects if o.type=="MESH" and o.find_armature()==rig]
for kind,data in [
 ("before_audit",lida.audit_meshes(meshes,rig)),
 ("before_snapshot",lida.snapshot_meshes(meshes,rig,source_path=bpy.data.filepath))]:
 p=out/(kind+".json")
 assert not p.exists()
 p.write_text(json.dumps(data,indent=2),encoding="utf-8")
print("AUDIT_SNAPSHOT_COMPLETE", [o.name for o in meshes])
