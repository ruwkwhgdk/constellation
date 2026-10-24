import bpy,json,sys
from pathlib import Path
sys.path.insert(0,"C:/Users/User/.codex/skills/lida-avatar-workflow/scripts")
import lida_model_tools as lida
P=Path(__file__).parent;out=Path(bpy.data.filepath).parent/"Validation";out.mkdir(exist_ok=False)
r=bpy.data.objects["Heroine_Rebuild_GameSkeleton"]
meshes=[o for o in bpy.data.objects if o.type=="MESH" and o.find_armature()==r]
before=json.loads((P/"Audit01/before_snapshot.json").read_text())
after=lida.snapshot_meshes(meshes,r,source_path=bpy.data.filepath)
(out/"snapshot.json").write_text(json.dumps(after,indent=2))
comparison=lida.compare_snapshots(before,after)
(out/"compare.json").write_text(json.dumps(comparison,indent=2))
print("SAVED_DATA_COMPARISON",comparison.get("status"),flush=True)
(out/"audit.json").write_text(json.dumps(lida.audit_meshes(meshes,r),indent=2))
print("AUDIT_COMPLETE",flush=True)
